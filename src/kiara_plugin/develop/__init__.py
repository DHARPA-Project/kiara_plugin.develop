# -*- coding: utf-8 -*-

"""Top-level package for kiara_plugin.develop."""


import os

from kiara.utils.class_loading import (
    KiaraEntryPointItem,
    find_data_types_under,
    find_kiara_model_classes_under,
    find_kiara_modules_under,
    find_pipeline_base_path_for_module,
)

__author__ = """Markus Binsteiner"""
__email__ = "markus@frkl.io"


KIARA_METADATA = {
    "authors": [{"name": __author__, "email": __email__}],
    "description": "Kiara modules for: develop",
    "references": {
        "source_repo": {
            "desc": "The module package git repository.",
            "url": "https://github.com/DHARPA-Project/kiara_plugin.develop",
        },
        "documentation": {
            "desc": "The url for the module package documentation.",
            "url": "https://DHARPA-Project.github.io/kiara_plugin.develop/",
        },
    },
    "tags": ["develop"],
    "labels": {"package": "kiara_plugin.develop"},
}

find_modules: KiaraEntryPointItem = (
    find_kiara_modules_under,
    "kiara_plugin.develop.develop",
)
find_model_classes: KiaraEntryPointItem = (
    find_kiara_model_classes_under,
    "kiara_plugin.develop.models",
)
find_data_types: KiaraEntryPointItem = (
    find_data_types_under,
    "kiara_plugin.develop.data_types",
)
find_pipelines: KiaraEntryPointItem = (
    find_pipeline_base_path_for_module,
    "kiara_plugin.develop.pipelines",
    KIARA_METADATA,
)


def get_version():
    from pkg_resources import DistributionNotFound, get_distribution

    try:
        # Change here if project is renamed and does not equal the package name
        dist_name = __name__
        __version__ = get_distribution(dist_name).version
    except DistributionNotFound:

        try:
            version_file = os.path.join(os.path.dirname(__file__), "version.txt")

            if os.path.exists(version_file):
                with open(version_file, encoding="utf-8") as vf:
                    __version__ = vf.read()
            else:
                __version__ = "unknown"

        except (Exception):
            pass

        if __version__ is None:
            __version__ = "unknown"

    return __version__
