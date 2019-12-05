#!/usr/bin/env python

import argparse
import os
import yaml


PLAYBOOK_DIR = 'playbooks'


def _get_playbooks(directory):
    playbook_dir = os.path.join(os.path.abspath(directory),
                                PLAYBOOK_DIR)
    playbooks = {}
    for playbook in os.listdir(playbook_dir):
        path = os.path.join(playbook_dir, playbook)
        with open(path, 'r') as file:
            playbooks[os.path.basename(path)] = yaml.safe_load(file)[0]
    return playbooks


def _has_host(host, playbook):
    hosts = [h.strip() for h in playbook.get('hosts', '').split(',')]
    return host in hosts

def _has_group(group, playbook):
    return group in playbook.get('vars', {}).get('metadata', {}).get(
        'groups', [])


def _filter_playbooks(args, playbooks):
    # Filter by group
    if args['group']:
        return {key: val for (key, val) in playbooks.items() if
                _has_group(args['group'], val)}
    if args['host']:
        return {key: val for (key, val) in playbooks.items() if
                _has_host(args['host'], val)}
    return playbooks


def _format_listing(args, playbooks):
    return [os.path.splitext(path)[0] for path in playbooks.keys()]


def run(args):
    if args['show']:
        # TODO(flfuchs): details listing for playbook
        print(args['show'])
    else:
        playbooks = _format_listing(
            args, _filter_playbooks(
                args, _get_playbooks(args['directory'])))
        for playbook in playbooks:
            print(playbook)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=("List validations in a directory structure of a "
                     "tripleo-validations-based repository"),
        epilog=("Example: ./listing.py /usr/share/tripleo-validations "
                "--group pre-deployment")
        )
    parser.add_argument("directory", help="The validations directory",
                        type=str)
    parser.add_argument("--show", help="Show details for a single validation",
                        type=str)
    parser.add_argument("--group", help="Filter listing by validation group",
                        type=str)
    parser.add_argument("--host", help="Filter listing by host",
                        type=str)

    args = parser.parse_args()
    run(vars(args))
