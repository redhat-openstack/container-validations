#!/usr/bin/env python3

#   Copyright 2022 Red Hat, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import argparse
from distutils import spawn
import logging
import os
import pwd
import subprocess
import sys


DESCRIPTION = "Build and execute Validations from a container."
EPILOG = "Example: ./validation --run --cmd run --validation check-ftype,512e"

VALIDATIONS_LOG_BASEDIR = os.path.expanduser('~/validations')
CONTAINER_INVENTORY_PATH = '/root/inventory.yaml'
COMMUNITY_VALIDATION_PATH = os.path.expanduser('~/community-validations')

CONTAINERFILE_TMPL = """
FROM %(image)s

LABEL name="VF dockerfile"

RUN dnf install -y git python3-pip gcc python3-devel jq %(extra_pkgs)s

# Clone the Framework and common Validations
RUN git clone https://opendev.org/openstack/validations-common \
    /root/validations-common
RUN git clone https://opendev.org/openstack/validations-libs \
    /root/validations-libs

# Clone user repository if provided
%(clone_user_repo)s
%(install_user_repo)s

RUN python3 -m pip install cryptography==3.3

RUN cd /root/validations-libs && \
    python3 -m pip install .

RUN cd /root/validations-common && \
    python3 -m pip install .

#Setting up the default directory structure for both ansible,
#and the VF
RUN ln -s /usr/local/share/ansible  /usr/share/ansible

ENV ANSIBLE_HOST_KEY_CHECKING false
ENV ANSIBLE_RETRY_FILES_ENABLED false
ENV ANSIBLE_KEEP_REMOTE_FILES 1
# @todo: Fix the User
ENV ANSIBLE_REMOTE_USER root
ENV ANSIBLE_PRIVATE_KEY_FILE /root/containerhost_private_key

%(entrypoint)s
"""


class Validation(argparse.ArgumentParser):
    """Validation client implementation class"""

    log = logging.getLogger(__name__ + ".Validation")

    def __init__(self, description=DESCRIPTION, epilog=EPILOG):
        """Init validation paser"""
        super(Validation, self).__init__(description=DESCRIPTION,
                                         epilog=EPILOG)

    def parser(self, parser):
        """Argument parser for validation"""
        parser.add_argument('--run', '-R', action='store_true',
                            help=('Run Validation command. '
                                  'Defaults to False'))
        parser.add_argument('--interactive', '-i', action='store_true',
                            help=('Execute interactive Validation shell. '
                                  'Defaults to False'))
        parser.add_argument('--build', '-B', action='store_true',
                            help=('Build container even if it exists. '
                                  'Defaults to False'))
        parser.add_argument('--cmd', type=str, nargs=argparse.REMAINDER,
                            default=None,
                            help='Validation command you want to execute, '
                                 'use --help to get more information. '
                                 'Only available in non-interactive mode. ')

        parser.add_argument('--image', type=str, default='fedora:30',
                            help='Container base image. Defaults to fedora:30')
        parser.add_argument('--extra-pkgs', type=str, default='',
                            help=('Extra packages to install in the container.'
                                  'Comma or space separated list. '
                                  'Defaults to empty string.'))
        parser.add_argument('--volumes', '-v', type=str, action='append',
                            default=[],
                            help=('Volumes you want to add to the container. '
                                  'Can be provided multiple times. '
                                  'Defaults to []'))
        parser.add_argument('--keyfile', '-K', type=str,
                            default=os.path.join(os.path.expanduser('~'),
                                                 '.ssh/id_rsa'),
                            help=('Keyfile path to bind-mount in container. '))
        parser.add_argument('--container', '-c', type=str, default='podman',
                            choices=['docker', 'podman'],
                            help='Container engine. Defaults to podman.')
        parser.add_argument('--validation-log-dir', '-l', type=str,
                            default=VALIDATIONS_LOG_BASEDIR,
                            help=('Path where the log files and artifacts '
                                  'will be located. '))
        parser.add_argument('--repository', '-r', type=str,
                            default=None,
                            help=('Remote repository to clone validations '
                                  'role from.'))
        parser.add_argument('--branch', '-b', type=str, default='master',
                            help=('Remote repository branch to clone '
                                  'validations from. Defaults to master'))

        parser.add_argument('--inventory', '-I', type=str,
                            default=None,
                            help=('Path of the Ansible inventory. '
                                  'It will be pulled to {} inside the '
                                  'container. '.format(
                                    CONTAINER_INVENTORY_PATH)))
        parser.add_argument('--debug', '-D', action='store_true',
                            help='Toggle debug mode. Defaults to False.')

        return parser.parse_args()

    def take_action(self, parsed_args):
        """Take validation action"""
        # Container params
        self.image = parsed_args.image
        self.extra_pkgs = parsed_args.extra_pkgs
        self.container = parsed_args.container
        self.validation_log_dir = parsed_args.validation_log_dir
        self.keyfile = parsed_args.keyfile
        self.interactive = parsed_args.interactive
        self.cmd = parsed_args.cmd
        # Build container
        self.repository = parsed_args.repository
        self.branch = parsed_args.branch
        self.debug = parsed_args.debug

        build = parsed_args.build
        run = parsed_args.run
        # Validation params
        self.inventory = parsed_args.inventory
        self.volumes = parsed_args.volumes

        if build:
            self.build()
        if run:
            self.run()

    def _print(self, string, debug=True):
        if self.debug:
            print(string)

    def _generate_containerfile(self):
        self._print('Generating "Containerfile"')
        clone_user_repo, install_user_repo, entrypoint = "", "", ""
        if self.repository:
            clone_user_repo = ("RUN git clone {} -b {} "
                               "/root/user_repo").format(self.repository,
                                                         self.branch)
            install_user_repo = ("RUN cd /root/user_repo && \\"
                                 "python3 -m pip install .")
        if self.interactive:
            entrypoint = "ENTRYPOINT /usr/local/bin/validation"
        param = {'image': self.image, 'extra_pkgs': self.extra_pkgs,
                 'clone_user_repo': clone_user_repo,
                 'install_user_repo': install_user_repo,
                 'entrypoint': entrypoint}
        with open('./Containerfile', 'w+') as containerfile:
            containerfile.write(CONTAINERFILE_TMPL % param)

    def _check_container_cli(self, cli):
        if not spawn.find_executable(cli):
            raise RuntimeError(
                "The container cli {} doesn't exist on this host".format(cli))

    def _build_container(self):
        self._print('Building image')
        self._check_container_cli(self.container)
        cmd = [
                self.container,
                'build',
                '-t',
                'localhost/validation',
                '-f',
                'Containerfile',
                '.'
                ]
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            print('An error occurred!')
            sys.exit(1)

    def _create_volume(self, path):
        try:
            self._print("Attempt to create {}.".format(path))
            os.mkdir(path)
        except (OSError, FileExistsError) as e:
            self._print(e)
            pass


    def _build_run_cmd(self):
        self._check_container_cli(self.container)
        if self.interactive:
            container_args = '-ti'
        else:
            container_args = '--rm'
        cmd = [self.container, 'run', container_args]
        # Keyfile
        cmd.append('-v%s:/root/containerhost_private_key:z' %
                   self.keyfile)
        # log path
        self._create_volume(self.validation_log_dir)
        if os.path.isdir(os.path.abspath(self.validation_log_dir)):
            cmd.append('-v%s:/root/validations:z' %
                       self.validation_log_dir)
        # community validation path
        self._create_volume(COMMUNITY_VALIDATION_PATH)
        if os.path.isdir(os.path.abspath(COMMUNITY_VALIDATION_PATH)):
            cmd.append('-v%s:/root/community-validations:z' %
                       COMMUNITY_VALIDATION_PATH)
        # Volumes
        if self.volumes:
            self._print('Adding volumes:')
            for volume in self.volumes:
                self._print(volume)
                cmd.extend(['-v', volume])
        # Inventory
        if self.inventory:
            if os.path.isfile(os.path.abspath(self.inventory)):
                cmd.append('-v%s:%s:z' % (
                    os.path.abspath(self.inventory),
                    CONTAINER_INVENTORY_PATH))
        # Map host network config
        cmd.append('--network=host')
        # Container name
        cmd.append('localhost/validation')
        # Validation binary
        cmd.append('validation')
        if not self.interactive and self.cmd:
            cmd.extend(self.cmd)
        return cmd

    def build(self):
        self._generate_containerfile()
        self._build_container()

    def run(self):
        self._print('Starting container')
        cmd = self._build_run_cmd()
        self._print('Running %s' % ' '.join(cmd))
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            print('An error occurred!')
            sys.exit(2)

if __name__ == "__main__":
    validation = Validation()
    args = validation.parser(validation)
    validation.take_action(args)
