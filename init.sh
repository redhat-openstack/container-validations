#!/bin/sh
REPO=${VALIDATION_REPOSITORY:="https://github.com/openstack/tripleo-validations.git"}
BRANCH=${REPO_BRANCH:='master'}
INV=${INVENTORY:="/home/validation/inventory.yaml"}
VALS=${VALIDATIONS:="dns,no-op"}

val_dir=$(basename "${REPO}" .git)
echo -n "Cloning repository ${REPO}"
git clone -q -b "${BRANCH}" "${REPO}"
echo " ... DONE"

if [ -z "${VALS}" ]; then
  echo "No validation passed, nothing to do"
else

  cd "${val_dir}"
  VALIDATIONS_BASEDIR="$(pwd)"
	export ANSIBLE_RETRY_FILES_ENABLED=false
	export ANSIBLE_KEEP_REMOTE_FILES=1

	export ANSIBLE_CALLBACK_PLUGINS="${VALIDATIONS_BASEDIR}/callback_plugins"
	export ANSIBLE_ROLES_PATH="${VALIDATIONS_BASEDIR}/roles"
	export ANSIBLE_LOOKUP_PLUGINS="${VALIDATIONS_BASEDIR}/lookup_plugins"
	export ANSIBLE_LIBRARY="${VALIDATIONS_BASEDIR}/library"

  while IFS=',' read -ra LIST; do
    for i in "${LIST[@]}"; do
      echo "Running ${i}"
      ansible-playbook -i ${INV} playbooks/${i}.yaml
    done
  done <<< "$VALS"
fi
