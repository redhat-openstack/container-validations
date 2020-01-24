#!/bin/sh
REPO=${VALIDATION_REPOSITORY:="https://github.com/openstack/tripleo-validations.git"}
BRANCH=${REPO_BRANCH:='master'}
INV=${INVENTORY:="/root/inventory.yaml"}
VALS=${VALIDATIONS:=""}

# Set logging env var to file mounted into the container.
if [ -f "/root/validations.log" ]; then
  export ANSIBLE_LOG_PATH="/root/validations.log"
fi


# Run the inventory ping test
if [ "${ACTION}" == "inventory_ping" ]; then
  echo "Running ping test on inventory"
  ansible all -i ${INVENTORY} -m ping
fi

if [[ "${ACTION}" =~ ^(run|list)$ ]]; then
  if [ -d "${DEFAULT_REPO_LOCATION}/.git" ]; then
    val_dir=${DEFAULT_REPO_LOCATION}
  else
    echo -n "Cloning repository ${REPO}"
    git clone -q -b "${BRANCH}" "${REPO}"
    echo " ... DONE"
    val_dir=$(basename "${REPO}" .git)
  fi
  if [ "${GROUP}" != "" ]; then
    VALS_FROM_REPO=$(/usr/bin/python3 listing.py ${val_dir} --group ${GROUP})
  elif [ "${HOST}" != "" ]; then
    VALS_FROM_REPO=$(/usr/bin/python3 listing.py ${val_dir} --host ${HOST})
  else
    VALS_FROM_REPO=$(/usr/bin/python3 listing.py ${val_dir})
  fi
fi

# List validations
if [ "${ACTION}" == "list" ]; then
  if [ "${GROUP}" != "" ]; then
    echo "Listing validations for group ${GROUP}."
  elif [ "${HOST}" != "" ]; then
    echo "Listing validations for host ${HOST}."
  else
    echo "Listing all validations."
  fi
  echo ${VALS_FROM_REPO}
fi

# Run a list of validations 
if [ "${ACTION}" == "run" ]; then

  cd "${val_dir}"
  VALIDATIONS_BASEDIR="$(pwd)"
  export ANSIBLE_CALLBACK_PLUGINS="${VALIDATIONS_BASEDIR}/callback_plugins"
  export ANSIBLE_ROLES_PATH="${VALIDATIONS_BASEDIR}/roles"
  export ANSIBLE_LOOKUP_PLUGINS="${VALIDATIONS_BASEDIR}/lookup_plugins"
  export ANSIBLE_LIBRARY="${VALIDATIONS_BASEDIR}/library"

  if [ "${VALS}" == "" ]; then
    VALS=${VALS_FROM_REPO}
  fi
  while IFS=',' read -ra LIST; do
    for i in "${LIST[@]}"; do
      echo "Running ${i}"
      ansible-playbook -i ${INV} playbooks/${i}.yaml
    done
  done <<< "$VALS"
fi
