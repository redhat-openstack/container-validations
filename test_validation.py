from validation import (
    CONTAINERFILE_TMPL,
    RunValidations,
    os,
    )


TEST_ARGS = {
    'user': 'stack',
    'uid': 1000,
    'keyfile': '/home/stack/.ssh/id_rsa',
    'image': 'fedora:30',
    'extra_pkgs': '',
    'debug': False,
    'validations': 'no-op',
    'repository': 'https://opendev.org/openstack/tripleo-validations',
    'branch': 'master',
    'container': 'podman',
    'inventory': '/home/stack/inventory.yaml',
    'volumes': '',
    'build': False,
    'run': False,
}


def test_containerfile_has_from_instruction():
    assert 'FROM' in CONTAINERFILE_TMPL


def test_volume_is_created_for_local_repo(mocker):
    os.path.isdir = mocker.MagicMock(return_value=True)
    args = dict(TEST_ARGS)
    args.update({
        'repository': '/home/stack/tripleo-validations'
        })
    rv = RunValidations(args)
    cmd = rv._RunValidations__build_run_cmd()
    # Make sure VALIDATION_REPOSITORY env var is not set
    assert ('--env=VALIDATION_REPOSITORY='
            '/home/stack/tripleo-validations') not in cmd
    # Make sure local repo is added as a volume
    assert ('-v/home/stack/tripleo-validations:'
            '/home/stack/validation-repository:z') in cmd
