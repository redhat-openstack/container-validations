# container-validations
Provide a container allowing to run validations

## Notes
In order to keep this README simple, examples and commands will replace your
container engine by "ct_cli". Please change this to either docker or podman.

## Building
```Bash
ct_cli build -t validation -f Containerfile
```

## Running
### Environment variables
There are several variables you can set when running the container:

#### VALIDATION_REPOSITORY
- Points to the git repository holding your validations.
- Defaults to https://github.com/openstack/tripleo-validations.git

#### INVENTORY
- Allows you to set an inventory, either bind-mounted file or as a string.
- Defaults to "/home/validation/inventory.yaml"

#### VALIDATION_LIST
- Allows to pass a list of playbook to run in the container, as a space
separated list.
- Defaults to "dns no-op"

## Override the Inventory
The easiest way to override the inventory is to bind-mount a file from the
host:
```Bash
ct_cli run --rm -v your-inventory:/inventory -e "INVENTORY=/inventory" validation
```
