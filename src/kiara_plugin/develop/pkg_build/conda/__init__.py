# -*- coding: utf-8 -*-
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, List, Union

from diskcache import Cache

from kiara.utils.cli import terminal_print
from kiara_plugin.develop.conda.models import (
    CondaBuildPackageDetails,
    PkgSpec,
)
from kiara_plugin.develop.conda.states import (
    MambaEnvironment,
    MicroMambaAvailable,
)
from kiara_plugin.develop.defaults import (
    DEFAULT_PYTHON_VERSION,
    KIARA_DEV_CACHE_FOLDER,
    KIARA_DEV_MICROMAMBA_ENV,
    KIARA_DEV_MICROMAMBA_TARGET_PREFIX,
)
from kiara_plugin.develop.pkg_build.states import States

CACHE_DIR = os.path.join(KIARA_DEV_CACHE_FOLDER, "pypi_cache")
cache = Cache(CACHE_DIR)





class CondaEnvMgmt(object):
    def __init__(self) -> None:

        self._states: States = States()
        self._states.add_state(
            MicroMambaAvailable(
                "micromamba_available", root_path=KIARA_DEV_CACHE_FOLDER, version="1.4.6"
            )
        )
        channels = ["conda-forge", "dharpa", "anaconda"]
        # deps = [f"python=={DEFAULT_PYTHON_VERSION}", "boa", "mamba", "anaconda"]
        deps = ["python==3.9", "boa", "mamba", "anaconda-client", "conda-verify"]
        conda_build_env = MambaEnvironment(
            "conda-build-env",
            env_name="conda-build-env",
            channels=channels,
            dependencies=deps,
            mamba_prefix=KIARA_DEV_MICROMAMBA_TARGET_PREFIX,
        )
        self._states.add_state(conda_build_env)
        channels = ["conda-forge", "dharpa"]
        deps = [f"python=={DEFAULT_PYTHON_VERSION}", "pip"]
        test_env = MambaEnvironment(
            "test-env",
            env_name="test-env",
            channels=channels,
            dependencies=deps,
            mamba_prefix=KIARA_DEV_MICROMAMBA_TARGET_PREFIX,
        )
        self._states.add_state(test_env)

    def get_state_detail(self, state_id: str, key: str) -> Any:

        return self._states.get_state_detail(state_id, key)

    def get_state_details(self, state_id: str):
        return self._states.get_state_details(state_id)

    def get_state(self, state_id: str):
        return self._states.get_state(state_id)

    def list_conda_envs(self) -> List[str]:

        micromamba_path = self.get_state_detail(
            "micromamba_available", "micromamba_bin"
        )

        args = [micromamba_path, "env", "list", "--json"]
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
            shell=False,
            env=KIARA_DEV_MICROMAMBA_ENV,
        )

        envs = json.loads(result.stdout)
        return [
            x[len(KIARA_DEV_MICROMAMBA_TARGET_PREFIX) + 1 :]
            for x in envs["envs"]
            if x.startswith(KIARA_DEV_MICROMAMBA_TARGET_PREFIX)
        ]

    def build_package(
        self, package: PkgSpec, python_version=DEFAULT_PYTHON_VERSION
    ) -> CondaBuildPackageDetails:

        from kiara_plugin.develop.utils import execute
        from kiara_plugin.develop.utils.pkg_utils import (
            default_stderr_print,
            default_stdout_print,
        )

        build_env_details = self.get_state_details("conda-build-env")
        env_name = build_env_details["env_name"]
        prefix = build_env_details["mamba_prefix"]
        conda_bin = os.path.join(prefix, env_name, "bin", "conda")

        # tempdir = tempfile.TemporaryDirectory()
        # base_dir = tempdir.name
        base_dir = os.path.join(
            KIARA_DEV_CACHE_FOLDER,
            "build",
            package.pkg_name,
            package.pkg_version,
            f"python-{python_version}",
        )

        build_dir = Path(base_dir) / "build"
        if build_dir.is_dir():
            shutil.rmtree(build_dir)
        build_dir.mkdir(parents=True, exist_ok=False)

        meta_file = Path(base_dir) / "meta.yaml"
        recipe = package.create_conda_spec()
        with open(meta_file, "wt") as f:
            f.write(recipe)

        channels = [
            item
            for tokens in (("--channel", channel) for channel in package.pkg_channels)
            for item in tokens
        ]

        args = ["mambabuild", "--py", python_version]
        args.extend(channels)
        args.extend(["--output-folder", build_dir.as_posix(), base_dir])

        result = execute(
            conda_bin,
            *args,
            stdout_callback=default_stdout_print,
            stderr_callback=default_stderr_print,
        )

        artifact = os.path.join(
            build_dir,
            "noarch",
            f"{package.pkg_name}-{package.pkg_version}-py_0.tar.bz2",
        )
        if not Path(artifact).is_file():
            raise Exception(f"Invalid artifact path: {artifact}")

        result_details: CondaBuildPackageDetails = CondaBuildPackageDetails(
            cmd=conda_bin,
            args=args[1:],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            base_dir=base_dir,
            build_dir=build_dir.as_posix(),
            meta_file=meta_file.as_posix(),
            package=package,
            build_artifact=artifact,
        )
        return result_details

    def upload_package(
            self,
            build_result: Union[CondaBuildPackageDetails, str, Path],
            token: Union[str, None] = None,
            user: Union[None, str] = None,
    ):

        from kiara_plugin.develop.utils import execute
        from kiara_plugin.develop.utils.pkg_utils import (
            default_stderr_print,
            default_stdout_print,
        )


        if isinstance(build_result, str):
            artifact = build_result
        elif isinstance(build_result, Path):
            artifact = build_result.as_posix()
        else:
            artifact = build_result.build_artifact

        build_env_details = self.get_state_details("conda-build-env")
        env_name = build_env_details["env_name"]
        prefix = build_env_details["mamba_prefix"]
        anaconda_bin = os.path.join(prefix, env_name, "bin", "anaconda")

        if token is None:
            token = os.getenv("ANACONDA_PUSH_TOKEN")
            if not token:
                raise Exception("Can't upload package, no api token provided.")

        args = ["-t", token, "upload"]
        if user:
            args.extend(["-u", user])

        args.append(os.path.expanduser(artifact))

        details = execute(
            anaconda_bin,
            *args,
            stdout_callback=default_stdout_print,
            stderr_callback=default_stderr_print,
        )

        terminal_print("Uploaded package, details:")
        terminal_print(details)
