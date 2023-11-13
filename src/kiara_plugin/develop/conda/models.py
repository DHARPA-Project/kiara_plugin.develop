# -*- coding: utf-8 -*-
import os
from typing import Dict, List, Union

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel, ConfigDict, Extra, Field, PrivateAttr, model_validator

from kiara.utils.yaml import StringYAML
from kiara_plugin.develop.defaults import KIARA_DEV_RESOURCES_FOLDER


def DEFAULT_HOST_DEPENDENCIES():
    return ["python", "pip"]


def DEFAULT_KIARA_HOST_DEPENDENCIES():
    return ["python", "pip", "setuptools_scm", "setuptools_scm_git_archive"]


class PkgSpecMetadata(BaseModel):

    home: str = Field(description="The package homepage.")
    license: str = Field(description="The package license.")
    license_family: Union[str, None] = Field(
        description="The license family.", default=None
    )
    summary: str = Field(description="A short description for this package.")
    doc_url: Union[str, None] = Field(
        description="The url to the documentation for this package.", default=None
    )
    dev_url: Union[str, None] = Field(
        description="The url to development information for this package.", default=None
    )
    recipe_maintainers: List[str] = Field(
        description="The conda-forge usernames of the recipe maintainers."
    )


class PkgSpecTests(BaseModel):

    model_config = ConfigDict(extra="forbid")

    imports: List[str] = Field(description="The imports to test.", default_factory=list)
    source_files: List[str] = Field(
        description="Source files to copy for tests.", default_factory=list
    )
    requires: List[str] = Field(
        description="Conda packages required for testing.", default_factory=list
    )
    commands: List[str] = Field(
        description="Commands to run for testing.", default_factory=list
    )

    def generate_conda_test_section(self) -> str:

        if not self.imports and not self.commands:
            return ""

        yaml = StringYAML()
        result: str = yaml.dump({"test": self.model_dump()})
        return result


class PkgSpec(BaseModel):
    # class Config(object):
    #     json_loads = orjson.loads
    #     json_dumps = orjson_dumps
    #     extra = Extra.forbid

    model_config = ConfigDict(extra=Extra.forbid)

    pkg_name: str = Field(description="The package name.")
    pkg_version: str = Field(
        description="The package version, either version number, or git branch/tag."
    )
    pkg_url: str = Field(description="The package url.")
    pkg_hash: Union[str, None] = Field(
        description="The package hash (sha256), if not git url.", default=None
    )
    host_requirements: List[str] = Field(
        description="The host dependencies for this package.",
        default_factory=DEFAULT_HOST_DEPENDENCIES,
    )
    pkg_requirements: List[str] = Field(
        description="The runtime dependencies of this package.", default_factory=list
    )
    pkg_channels: List[str] = Field(
        description="The channels to look for dependencies in.", default_factory=list
    )
    metadata: PkgSpecMetadata = Field(description="Misc. package metadata.")
    test: PkgSpecTests = Field(description="Test specs.", default_factory=PkgSpecTests)
    entry_points: Dict[str, str] = Field(
        description="The package entry point(s).", default_factory=dict
    )

    _environment: Environment = PrivateAttr(None)

    @model_validator(mode="before")
    @classmethod
    def validate_url_type(cls, values):
        pkg_url = values.get("pkg_url", None)
        if pkg_url is None:
            pkg_url = "https://pypi.io/packages/source/{{ name[0] }}/{{ name }}/{{ name }}-{{ version }}.tar.gz"
            values["pkg_url"] = pkg_url
            if not values.get("pkg_hash"):
                raise ValueError("No package hash provided.")
        elif pkg_url.endswith(".git"):
            pkg_hash = values.get("pkg_hash", None)
            if pkg_hash:
                raise ValueError("Package hash not supported for git url.")
        elif pkg_url.startswith("file://"):
            pkg_hash = values.get("pkg_hash", None)
            if pkg_hash:
                raise ValueError("Package hash not supported for local project.")

        return values

    def jinja_environment(self) -> Environment:
        if self._environment:
            return self._environment
        else:
            template_loader = FileSystemLoader(
                searchpath=os.path.join(KIARA_DEV_RESOURCES_FOLDER, "templates")
            )
            self._environment = Environment(
                loader=template_loader, autoescape=select_autoescape()
            )
            return self._environment

    def create_boa_recipe(self) -> str:

        template = self.jinja_environment().get_template("recipe.yaml.j2")
        result: str = template.render(pkg_info=self)
        return result

    def create_conda_spec(self) -> str:

        template = self.jinja_environment().get_template("meta.yaml.j2")
        result: str = template.render(pkg_info=self)
        return result


class RunDetails(BaseModel):

    cmd: str = Field(description="The command that was run.")
    args: List[str] = Field(description="The arguments to the command.")
    exit_code: int = Field(description="The command exit code.")
    stdout: str = Field(description="The command output.")
    stderr: str = Field(description="THe command error output.")


class CondaBuildPackageDetails(RunDetails):

    base_dir: str = Field(description="The base directory.")
    build_dir: str = Field(description="The build directory.")
    meta_file: str = Field(description="The path to the package meta file.")
    package: PkgSpec = Field(description="Package metadata.")
    build_artifact: str = Field(description="Path to the package build artifact.")
