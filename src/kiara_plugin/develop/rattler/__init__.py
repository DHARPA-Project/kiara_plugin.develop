# -*- coding: utf-8 -*-
import os
import shutil
from pathlib import Path
from typing import List, Union

from diskcache import Cache

from kiara.utils.cli import terminal_print
from kiara_plugin.develop.conda.models import (
    PkgSpec,
    RattlerBuildPackageDetails,
    RunDetails,
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
        self, package: PkgSpec, python_version=DEFAULT_PYTHON_VERSION, package_formats: Union[str, List[str]] = ["tarbz2", "conda"], output_folder: Union[str, None]=None
    ) -> RattlerBuildPackageDetails:

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

        if isinstance(package_formats, str):
            package_formats = [package_formats]

        if not package_formats:
            raise Exception("No package formats provided.")

        all_run_details = []
        for package_format in package_formats:

            pkg_format_args = args.copy()
            pkg_format_args.append("--package-format")
            pkg_format_args.append(package_format)

            result = execute(
                rattler_build_bin,
                *pkg_format_args,
                stdout_callback=default_stdout_print,
                stderr_callback=default_stderr_print,
            )

            run_details = RunDetails(
                cmd=rattler_build_bin,
                args=pkg_format_args[1:],
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code
            )
            all_run_details.append(run_details)


        artefact_stem = f"{package.pkg_name}-{package.pkg_version}-*"
        build_output_folder = os.path.join(build_dir, "noarch")
        # find files matching artefact_stem in output folder using globs

        artefacts = list(Path(build_output_folder).glob(artefact_stem))

        if not artefacts:
            raise Exception(f"No build artifact found in: {build_output_folder}")
        elif len(artefacts) != len(package_formats):
            raise Exception(f"Invalid number of build artifacts found in: {build_output_folder}")

        for artifact in artefacts:
            if not artifact.is_file():
                raise Exception(f"Invalid artifact path (not a file): {artifact.as_posix()}")

        if output_folder:
            all_artifacts = []
            output_folder_path = Path(output_folder)  # type: ignore
            output_folder_path.mkdir(parents=True, exist_ok=True)
            for artifact in artefacts:
                artifact_path = shutil.copy(artifact, output_folder_path)
                all_artifacts.append(artifact_path)
        else:
            all_artifacts = [artifact.as_posix() for artifact in artefacts]

        result_details = RattlerBuildPackageDetails(
            run_details=all_run_details,
            base_dir=base_dir.as_posix(),
            build_dir=build_dir.as_posix(),
            meta_file=recipe_file.as_posix(),
            package=package,
            build_artifacts=all_artifacts
        )
        return result_details

    def upload_package(
            self,
            artifacts_or_folder: Union[str, List[str], Path],
            channel: Union[str, None] = None,
            token: Union[str, None] = None,
            user: Union[None, str] = None,
    ):

        if isinstance(artifacts_or_folder, str):
            artifacts_or_folder = [artifacts_or_folder]
        elif isinstance(artifacts_or_folder, Path):
            artifacts_or_folder = [artifacts_or_folder.as_posix()]

        artifacts: List[Path] = []
        for artifact in artifacts_or_folder:

            path = Path(os.path.expanduser(artifact)).absolute()

            if not path.exists():
                raise Exception(f"Path does not exist: {path}")

            if path.is_file():
                artifacts.append(path)
            elif path.is_dir():
                for f in path.iterdir():
                    if f.is_file() and (f.name.endswith(".tar.bz2") or f.name.endswith(".conda")):
                        artifacts.append(f)


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

        if not channel:
            raise Exception("Can't upload package, no channel provided.")

        args: List[str] = ["upload", "anaconda", "--channel", channel]
        if user:
            args.extend(["--owner", user])

        for artifact_path in artifacts:
            args.append(artifact_path.as_posix())

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

        terminal_print("Uploaded package(s), details:")
        terminal_print(details)
