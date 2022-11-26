# -*- coding: utf-8 -*-
import os
import sys

from appdirs import AppDirs

#  Copyright (c) 2021, University of Luxembourg / DHARPA project
#  Copyright (c) 2021, Markus Binsteiner
#
#  Mozilla Public License, version 2.0 (see LICENSE or https://www.mozilla.org/en-US/MPL/2.0/)


kiara_dev_app_dirs = AppDirs("kiara-dev", "DHARPA")

if not hasattr(sys, "frozen"):
    KIARA_DEV_MODULE_BASE_FOLDER = os.path.dirname(__file__)
    """Marker to indicate the base folder for the `kiara_plugin/develop` module."""
else:
    KIARA_DEV_MODULE_BASE_FOLDER = os.path.join(sys._MEIPASS, "kiara_plugin.develop")  # type: ignore
    """Marker to indicate the base folder for the `kiara_plugin/develop` module."""

KIARA_DEV_RESOURCES_FOLDER = os.path.join(KIARA_DEV_MODULE_BASE_FOLDER, "resources")
"""Default resources folder for this package."""

KIARA_DEV_CACHE_FOLDER = kiara_dev_app_dirs.user_cache_dir
KIARA_DEV_MICROMAMBA_PATH = os.path.join(KIARA_DEV_CACHE_FOLDER, "bin", "micromamba")
KIARA_DEV_MICROMAMBA_TARGET_PREFIX = os.path.join(
    kiara_dev_app_dirs.user_data_dir, "micromamba", "envs"
)
KIARA_DEV_MICROMAMBA_ENV = {
    "MAMBA_ROOT_PREFIX": os.path.join(kiara_dev_app_dirs.user_data_dir, "micromamba"),
}
DEFAULT_PYTHON_VERSION = "3.10"
