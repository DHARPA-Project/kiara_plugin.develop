#!/usr/bin/env sh

set -e
set -o pipefail

# set to your github user if you forked the repos
GITHUB_USER="DHARPA-Project"
# set to 'false' if you want to use https git urls instead
USE_SSH="true"
# set to 'false' if you don't want to install Python development utilities (black, etc.)
INSTALL_DEV_UTILS="true"

checkout_repo() {
  name=${1}

  if [[ -d "${name}" ]]; then
    echo "Repo '${name}' exists, doing a git pull instead"
    cd ${name}
    git pull
    cd ..
  else
    if [[ "${USE_SSH}" == "true" ]]; then
        url="git@github.com:${GITHUB_USER}/${name}.git/"
    else
        url="https://github.com/${GITHUB_USER}/${name}.git"
    fi

    echo "-------------------------------------------------------"
    echo "Checking out: ${url}"
    git clone ${url}
    pip_install_pkg "${name}"
  fi
  echo
}

pip_install_pkg() {

  name=${1}
  echo "Installing int current virtual-env: ${name}"

  if [[ "${INSTALL_DEV_UTILS}" == "true" ]]; then
    pkg_name="${name}[dev_utils]"
  else
    pkg_name=${name}
  fi

  pip install -e "${pkg_name}"
  echo "Done."
}

# comment out the repositories you don't want to work on
checkout_repo "kiara"
checkout_repo "kiara_plugin.core_types"
checkout_repo "kiara_plugin.tabular"
checkout_repo "kiara_plugin.onboarding"
# checkout_repo "kiara_plugin.network_analysis"
# checkout_repo "kiara_plugin.language_processing"
# checkout_repo "kiara_plugin.streamlit"
# checkout_repo "kiara_plugin.develop"
# checkout_repo "kiara_plugin.html"
# checkout_repo "kiara_plugin.service"
