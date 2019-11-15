# container-validations
Provide a container allowing to run validations

## How to use this project?
All is relying on a python script: validation.py. Using this script, you will
get the following:
- a container image able to run the validations
- a run of a container based on this image

All the logs will be in the container stdout/stderr, meaning you're able
to rely on the container engine's logging configuration in order to get a proper
status.

### Inventory file
The repository holds an inventory file which holds connection information for
all relevant hosts. You can add or edit host information here before the first
run.

### First run
The script first needs to build a container image which will be able to run the
validations. To build the immage using the default options run:
```Bash
./validation.py --build
```
Please note that the default container cli is `podman` if you don't have podman
installed use `--container=docker` instead.

Once the container is built you can test it by running:
```Bash
./validation.py --run
```
This will test the connection information inside the inventory file.

If you want to run a specific validation run:
```Bash
./validation.py --run --validations=openstack-endpoints
```

### Options
To see a list of options run
```Bash
./validation.py -h
```

## Containerfile.sample
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
