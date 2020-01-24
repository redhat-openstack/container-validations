# container-validations

This project provides a container-based mechanism to run validations.


## How to use this project?

All is relying on a python script: validation.py. Using this script, you will
get the following:
- a container image able to run the validations
- a run of a container based on this image
- information on the validations available to run

All the logs will be in the container stdout/stderr, meaning you're able
to rely on the container engine's logging configuration in order to get a proper
status.


### Inventory file

The repository holds an inventory file which holds connection information for
all relevant hosts. You can add or edit host information here before the first
run or provide your own inventory file using the `--inventory` option.


#### TripleO

If you're working in a TripleO environment, you can use the
`scripts/tripleo-inventory` script to create an inventory file from the
tripleo-ansible-inventory. The resulting file will contain connection
information for the undercloud and overcloud nodes, as well as some additional
information that can be used in validations. For now the script is tested with
the Newton release of OpenStack. It can be used like this:

```Bash
source ~/stackrc
tripleo-ansible-inventory | ./scripts/tripleo-inventory > tripleo-inventory.yaml
```


### First run / building the container image

The script first needs to build a container image which will be able to run the
validations. To build the immage using the default options run:

```Bash
./validation.py --build
```

Please note that the default container cli is `podman` if you don't have podman
installed use `--container=docker` instead.

Once the container is built you can test it by running:
```Bash
./validation.py --inventory-ping
```

This will test the connection information inside the inventory file.


### Running validations

If you want to run a specific validation run:
```Bash
./validation.py --run --validations=openstack-endpoints
```

If you want to run all validations for a certain group run:
```Bash
./validation.py --run --group pre-deployment
```

If you want to run all validations run:
```Bash
./validation.py --run
```

### Listing validations

If you want to list validations run:
```Bash
./validation.py --list --group pre-deployment
```

or

```Bash
./validation.py --list
```

### Using a config file

If you regularly run validations with similar settings it might make sense to
use a config file instead of adding all arguments to each call.

First you need to create one:

```Bash
./validation.py --create-config my-config.ini --container docker --repository /home/stack/tripleo-validations
```

This will create a config file `my-config.ini` and add the values for the
`--container` and `repository` arguments to it, so you don't have to add them
to the call any more. You can use the file like this:

```Bash
./validation.py --config my-config.ini --list
```

You can of course edit the file with a text editor, too.


### Logging

If you want to have the validation results logged into a file you can use the `--log-path <local file path>` option. Instead of just outputting the validation results on stdout it will log the results to the given log file path. If the file already exists the entries will be appended to the file, otherwise the file will be created. 


### Options

To see the complete list of options run
```Bash
./validation.py -h
```

## Developing validations

By default container-validations downloads and installs the upstream master
during build time. You can use the `--repository` option to change this to
either a remote git repository or a local path.

Here's a step to step guide to test a new validation in container-validations:

1. Make sure to use a correct inventory file

For example if you want to test a new validation that runs on the host from
which you're running container-validations your inventory file should look
something like this: 

```
---
all:
  hosts:
  children:
    undercloud:          # The validation playbook should point to this host
      hosts:
        172.16.0.95:     # This is your local IP
```

Reference the inventory file using the `--inventory` option:

```Bash
(sudo) validation.py --run --inventory my-inventory.yaml
```

Please note that you can test all connections in your inventory file:

```Bash
./validation.py --inventory my-inventory.ini --inventory-ping
```


2. Define a development repository

Usually you want to use a local repository for development. You can use the
`--repository` option to define a path to a local repository (remember you can
store the value in a config file): 

```Bash
./validations.py --repository /home/stack/tripleo-validations --validations my-validation
```

If you want to switch between branches of you repository, use `--branch`:

```Bash
./validations.py --repository /home/stack/tripleo-validations --validations my-validation --branch my-feature
```

Please note: If you use that option with the `--build` command it will install
the repository's dependencies inside the container, so you should do this at
least once. If you use `--repository` together with the `--run` command it will
only bind-mount the local path into the container. This means that you don't
need to bulid the container everytime you make changes to your validations,
only when there are changes with the dependencies.


## Other

### Containerfile.sample
If you want to bypass the script, you can take the provided
Containerfile.sample and build the container on your own. Please keep in mind
some packages are mandatory: ansible and git.

Please also ensure the init.sh script is copied inside your image, since it's
the default command.

In order to build it on your own, you can run:
```Bash
(podman|docker) build -t validations -f Containerfile
```

In order to manually run the container, you can run:
```Bash
(podman|docker) run --rm -e "INVENTORY=localhost," \
  -e "VALIDATIONS=dns,no-op' \
  -v $(pwd)/.ssh/id_rsa:/home/my-user/.ssh/id_rsa \
  validations
```

### Additional options

#### `--user` and `--uid`

This will use a different user and UID than the current one when trying to connect to
hosts.


#### `--keyfile`

Set the keyfile manually (usually /home/<current user>/.ssh/id_rsa).


#### `--extra-pkgs`

Install additional packages into your container image if they're needed by
custom validations.

