#!/usr/bin/env python

import argparse
import os
import pwd
import subprocess
import sys

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser as ConfigParser

CONTAINERFILE_TMPL = '''
FROM %(image)s

# Install some packages
RUN yum install -y git ansible sudo %(extra_pkgs)s
RUN yum clean all

COPY init.sh /init.sh
RUN chmod 0755 /init.sh

# Create validation user
RUN useradd -c "Validation user" -m -s /bin/sh -u %(uid)s %(user)s
USER %(user)s
COPY inventory.yaml /home/%(user)s/inventory.yaml
WORKDIR /home/%(user)s
CMD ["/init.sh"]
'''


class RunValidations:
    def __init__(self, args):
        self.__args = args
        self.__params = {}

        self.__conf_file = os.path.join(os.getcwd(),
                                        '.config', 'run_validations.conf')

        self.__setup()
        if self.__params['build']:
            self.build()
        if self.__params['run']:
            self.run()
        pass

    def __print(self, string, debug=True):
        if bool(self.__params['debug']):
            print(string)

    def __setup(self):
        if not os.path.exists(self.__conf_file) or self.__args.regenerate:
            print('Generating config file')
            if not os.path.isdir(os.path.dirname(self.__conf_file)):
                os.makedirs(os.path.dirname(self.__conf_file))
            config = ConfigParser()
            config.add_section('Validations')
            config.set('Validations', 'user', self.__args.user)
            config.set('Validations', 'uid', self.__args.uid)
            config.set('Validations', 'image', self.__args.image)
            config.set('Validations', 'extra_pkgs', self.__args.extra_pkgs)
            config.set('Validations', 'debug', self.__args.debug)
            config.set('Validations', 'validations',
                       ','.join(self.__args.validation))
            config.set('Validations', 'repository', self.__args.repository)
            config.set('Validations', 'branch', self.__args.branch)
            config.set('Validations', 'container', self.__args.container)
            config.set('Validations', 'inventory', self.__args.inventory)
            config.set('Validations', 'volumes', ','.join(self.__args.volumes))
            with open(self.__conf_file, 'w+') as cfg_file:
                config.write(cfg_file)

        config = ConfigParser(allow_no_value=True)
        with open(self.__conf_file, 'r') as cfg_file:
            try:
                config.read_file(cfg_file)
            except AttributeError:
                config.readfp(cfg_file)
        self.__params['user'] = config.get('Validations', 'user')
        self.__params['uid'] = config.getint('Validations', 'uid')
        self.__params['image'] = config.get('Validations', 'image')
        self.__params['debug'] = config.getboolean('Validations', 'debug')
        self.__params['validations'] = config.get('Validations', 'validations')
        self.__params['repository'] = config.get('Validations', 'repository')
        self.__params['branch'] = config.get('Validations', 'branch')
        self.__params['container'] = config.get('Validations', 'container')
        self.__params['inventory'] = config.get('Validations', 'inventory')
        self.__params['build'] = self.__args.build
        self.__params['run'] = self.__args.run

        validations = config.get('Validations', 'volumes').split(',')
        self.__params['volumes'] = validations

        extra_pkgs = config.get('Validations', 'extra_pkgs')
        self.__params['extra_pkgs'] = ' '.join(extra_pkgs.split(','))

    def __generate_containerfile(self):
        self.__print('Generating "Containerfile"')
        with open('./Containerfile', 'w+') as containerfile:
            containerfile.write(CONTAINERFILE_TMPL % self.__params)

    def __build_container(self):
        self.__print('Building image')
        cmd = [
                self.__params['container'],
                'build',
                '-t',
                'localhost/validations',
                '-f',
                'Containerfile',
                '.'
                ]
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            print('An error occurred!')
            sys.exit(1)
        else:
            self.run()

    def build(self):
        self.__generate_containerfile()
        self.__build_container()
        pass

    def __build_run_cmd(self):
        cmd = [
                self.__params['container'],
                'run', '--rm',
                ]

        if len(self.__params['volumes']) > 1:
            self.__print('Adding volumes:')
            for volume in self.__params['volumes']:
                self.__print(volume)
                cmd.extend(['-v', volume])

        cmd.append('--env=VALIDATION_REPOSITORY=%s' %
                   self.__params['repository'])
        cmd.append('--env=INVENTORY=%s' % self.__params['inventory'])
        cmd.append('--env=REPO_BRANCH=%s' % self.__params['branch'])
        if self.__params['validations'] != '':
            cmd.append('--env=VALIDATIONS=%s' % self.__params['validations'])

        cmd.append('localhost/validations')
        self.__print(' '.join(cmd))
        return cmd

    def run(self):
        if self.__params['run']:
            self.__print('Running validations')
            cmd = self.__build_run_cmd()
            self.__print('Running %s' % ' '.join(cmd))
            try:
                subprocess.check_call(cmd)
            except subprocess.CalledProcessError:
                print('An error occurred!')
                sys.exit(2)


if __name__ == "__main__":

    default_user = pwd.getpwuid(os.getuid()).pw_name
    default_uid = os.getuid()
    default_repo = 'https://opendev.org/openstack/tripleo-validations'
    default_branch = 'master'
    default_inventory = os.path.join('/home', default_user, 'inventory.yaml')

    parser = argparse.ArgumentParser(
            description=('Run validations. It can either use in-line '
                         'parameter, or use an existing configuration '
                         'file located in '
                         'CURRENT_DIR/.config/run_validations.conf. '
                         'The configuration file has priority.'),
            epilog=('Example: ./validation.py --extra-pkgs whois '
                    '--regenerate --run --debug '
                    '-v /tmp/foo:/tmp/bar:z')
            )
    parser.add_argument('--user', '-u', type=str, default=default_user,
                        help=('Set user in container. '
                              'Defaults to %s' % default_user))
    parser.add_argument('--uid', '-U', type=int, default=default_uid,
                        help=('User UID in container. '
                              'Defaults to %s' % default_uid))
    parser.add_argument('--build', '-B', action='store_true',
                        help='Build container even if it exists. '
                             'Defaults to False')
    parser.add_argument('--run', '-R', action='store_true',
                        help='Run validations. Defaults to False')
    parser.add_argument('--image', '-i', type=str, default='fedora:30',
                        help='Container base image. Defaults to fedora:30')
    parser.add_argument('--extra-pkgs', type=str, default='',
                        help=('Extra packages to install in the container. '
                              'Comma or space separated list. '
                              'Defaults to empty string.'))
    parser.add_argument('--validation', '-V', type=str, default=[],
                        action='append',
                        help=('Validation to run. Can be provided multiple '
                              'times. Defaults to [].'))
    parser.add_argument('--repository', '-r', type=str, default=default_repo,
                        help=('Remote repository to clone validations role '
                              'from. Defaults to %s' % default_repo))
    parser.add_argument('--branch', '-b', type=str, default=default_branch,
                        help=('Remote repository branch to clone validations '
                              'from. Defaults to %s' % default_branch))
    parser.add_argument('--regenerate', action='store_true',
                        help='Re-generate the configuration file')
    parser.add_argument('--container', '-c', type=str, default='podman',
                        choices=['docker', 'podman'],
                        help='Container engine. Defaults to podman.')
    parser.add_argument('--volumes', '-v', type=str, action='append',
                        default=[],
                        help=('Volumes you want to add to the container. '
                              'Can be provided multiple times. '
                              'Defaults to []'))
    parser.add_argument('--inventory', '-I', type=str,
                        default=default_inventory,
                        help=('Provide inventory for validations. Can be a '
                              'path, or a string. Please refer to Ansible '
                              'inventory documentation. '
                              'Defaults to %s' % default_inventory))
    parser.add_argument('--debug', '-D', action='store_true',
                        help='Toggle debug mode. Defaults to False.')

    args = parser.parse_args()

    val = RunValidations(args)
