# container-validations
Provide a container allowing to run validations

## How to use this project?
All is relying on a python script: validation.py. Using this script, you will
get the following:
- a container image able to run the validations
- a run of a container based on this image

All the logs will be in the container stdout/stderr, meaning you're able
to rely on the container enging logging configuration in order to get a proper
status.

### First run
The script is based on a configuration file. It will be located in your current
directory, for instance $PWD/.config/run_validations.conf.

This file will be generated once, unless you add the ```--regenerate``` option.
Configuration file has priority, meaning you need to regenerate it if you want
to modify some options. You can also edit it if you want.

### Day+1 operation
Once you have the configuration file you want, you can just call the script as
follow:
```Bash
./validation.py --run
```
You can also force a rebuild:
```Bash
./validation.py --run --build
```

### Options
Please refer to ```./validation.py --help``` for a complete, up-to-date listing.

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
