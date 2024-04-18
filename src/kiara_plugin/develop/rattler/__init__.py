# -*- coding: utf-8 -*-
import os
import shutil
from pathlib import Path
from typing import Union

from diskcache import Cache

from kiara.utils.cli import terminal_print
from kiara_plugin.develop.conda.models import (
    CondaBuildPackageDetails,
    PkgSpec,
)
from kiara_plugin.develop.conda.states import (
    States,
)
from kiara_plugin.develop.defaults import (
    DEFAULT_PYTHON_VERSION,
    KIARA_DEV_CACHE_FOLDER,
)
from kiara_plugin.develop.rattler.states import RattlerBuildAvailable
from kiara_plugin.develop.utils import execute

CACHE_DIR = os.path.join(KIARA_DEV_CACHE_FOLDER, "pypi_cache")
cache = Cache(CACHE_DIR)


def default_stdout_print(msg):
    terminal_print(f"[green]stdout[/green]: {msg}")


def default_stderr_print(msg):
    terminal_print(f"[red]stderr[/red]: {msg}")

RATTLER_BUILD_VERSION = "0.15.0"

class RattlerBuildEnvMgmt(object):
    def __init__(self) -> None:

        self._states: States = States()
        self._states.add_state(
            RattlerBuildAvailable(
                "rattler-build-available", root_path=KIARA_DEV_CACHE_FOLDER, version=RATTLER_BUILD_VERSION
            )
        )

    def get_state_details(self, state_id: str):
        return self._states.get_state_details(state_id)

    def build_package(
        self, package: PkgSpec, python_version=DEFAULT_PYTHON_VERSION, package_format: str = "tarbz2"
    ) -> CondaBuildPackageDetails:

        build_env_details = self.get_state_details("rattler-build-available")
        rattler_build_bin = build_env_details["rattler_build_bin"]

        # tempdir = tempfile.TemporaryDirectory()
        # base_dir = tempdir.name
        base_dir = Path(os.path.join(
            KIARA_DEV_CACHE_FOLDER,
            "build",
            package.pkg_name,
            package.pkg_version,
            f"python-{python_version}",
        ))

        if base_dir.is_dir():
            shutil.rmtree(base_dir)
        base_dir.mkdir(parents=True, exist_ok=False)

        build_dir = base_dir / "build"


        recipe_file = base_dir / "recipe" / "recipe.yaml"
        recipe = package.create_rattler_build_recipe()
        recipe_file.parent.mkdir(parents=True, exist_ok=False)
        with open(recipe_file, "wt") as f:
            f.write(recipe)

        channels = [
            item
            for tokens in (("--channel", channel) for channel in package.pkg_channels)
            for item in tokens
        ]

        args = ["build", "-r", recipe_file.absolute().as_posix(), "--log-style", "plain"]

        args.extend(channels)
        args.extend(["--output-dir", build_dir.as_posix()])

        args.append("--package-format")
        args.append(package_format)

        result = execute(
            rattler_build_bin,
            *args,
            stdout_callback=default_stdout_print,
            stderr_callback=default_stderr_print,
        )

        artefact_stem = f"{package.pkg_name}-{package.pkg_version}-*"

        output_folder = os.path.join(build_dir, "noarch")
        # find files matching artefact_stem in output folder using globs

        artefacts = list(Path(output_folder).glob(artefact_stem))

        if not artefacts:
            raise Exception(f"No build artifact found in: {output_folder}")
        elif len(artefacts) > 1:
            raise Exception(f"Multiple build artifacts found in: {output_folder}")

        artifact = artefacts[0]
        if not artifact.is_file():
            raise Exception(f"Invalid artifact path (not a file): {artifact.as_posix()}")

        result = CondaBuildPackageDetails(
            cmd=rattler_build_bin,
            args=args[1:],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            base_dir=base_dir.as_posix(),
            build_dir=build_dir.as_posix(),
            meta_file=recipe_file.as_posix(),
            package=package,
            build_artifact=artifact.as_posix()
        )
        return result

    def upload_package(
            self,
            build_result: Union[CondaBuildPackageDetails, str, Path],
            channel: str,
            token: Union[str, None] = None,
            user: Union[None, str] = None,
    ):

        if isinstance(build_result, str):
            artifact = build_result
        elif isinstance(build_result, Path):
            artifact = build_result.as_posix()
        else:
            artifact = build_result.build_artifact

        build_env_details = self.get_state_details("rattler-build-available")
        rattler_build_bin = build_env_details["rattler_build_bin"]

        if token is None:
            token = os.getenv("ANACONDA_PUSH_TOKEN")
            if not token:
                raise Exception("Can't upload package, no api token provided.")

        if user is None:
            user = os.getenv("ANACONDA_OWNER")
            if not user:
                raise Exception("Can't upload package, no user provided.")

        args = ["upload", "anaconda", "--channel", channel]
        if user:
            args.extend(["--owner", user])

        args.append(os.path.expanduser(artifact))

        env = {
            "ANACONDA_OWNER": user,
            "ANACONDA_API_KEY": token
        }

        details = execute(
            rattler_build_bin,
            *args,
            stdout_callback=default_stdout_print,
            stderr_callback=default_stderr_print,
            env_vars=env
        )

        terminal_print("Uploaded package, details:")
        terminal_print(details)
