#!/bin/sh
REPO=${VALIDATION_REPOSITORY:="https://github.com/openstack/tripleo-validations.git"}
BRANCH=${REPO_BRANCH:='master'}
INV=${INVENTORY:="/root/inventory.yaml"}
VALS=${VALIDATIONS:="inventory-ping"}

# Run the inventory ping test
if [ "${ACTION}" == "inventory_ping" ]; then
  echo "Running ping test on inventory"
  ansible all -i ${INVENTORY} -m ping
fi

# Run a list of validations 
if [ "${ACTION}" == "run" ]; then
  if [ -d "${DEFAULT_REPO_LOCATION}/.git" ]; then
    val_dir=${DEFAULT_REPO_LOCATION}
  else
    val_dir=$(basename "${REPO}" .git)
    echo -n "Cloning repository ${REPO}"
    git clone -q -b "${BRANCH}" "${REPO}"
    echo " ... DONE"
  fi

  cd "${val_dir}"
  VALIDATIONS_BASEDIR="$(pwd)"
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
