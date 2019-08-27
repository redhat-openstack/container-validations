#!/bin/sh
REPO=${VALIDATION_REPOSITORY:="https://github.com/openstack/tripleo-validations.git"}
INV=${INVENTORY:="/home/validation/inventory.yaml"}
V_LIST=${VALIDATION_LIST:="dns no-op"}

val_dir=$(basename "${REPO}" .git)
echo -n "Cloning repository ${REPO}"
git clone -q "${REPO}"
echo " ... DONE"

if [ -z "${V_LIST}" ]; then
  echo "No validation passed, nothing to do"
else

  cd "${val_dir}"
  VALIDATIONS_BASEDIR="$(pwd)"
	echo $VALIDATIONS_BASEDIR
	export ANSIBLE_RETRY_FILES_ENABLED=false
	export ANSIBLE_KEEP_REMOTE_FILES=1

	export ANSIBLE_CALLBACK_PLUGINS="${VALIDATIONS_BASEDIR}/callback_plugins"
	export ANSIBLE_ROLES_PATH="${VALIDATIONS_BASEDIR}/roles"
	export ANSIBLE_LOOKUP_PLUGINS="${VALIDATIONS_BASEDIR}/lookup_plugins"
	export ANSIBLE_LIBRARY="${VALIDATIONS_BASEDIR}/library"

  for i in ${V_LIST}; do
    ansible-playbook -i ${INV} playbooks/${i}.yaml
  done
fi
