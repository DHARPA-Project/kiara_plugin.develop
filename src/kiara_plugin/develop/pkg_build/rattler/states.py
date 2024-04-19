# -*- coding: utf-8 -*-
import os
import platform
from pathlib import Path
from typing import Any, Dict, Mapping, Union
from urllib.request import urlopen

from kiara.utils.cli import terminal_print
from kiara_plugin.develop.pkg_build.states import State


class RattlerBuildAvailable(State):

    def _check(self) -> Union[None, Mapping[str, Any]]:

        root_path: str = self.get_config("root_path")
        bin_path = os.path.join(root_path, "bin", "rattler-build")
        if Path(bin_path).is_file():
            return {"rattler_build_bin": bin_path}
        else:
            return None

    def _purge(self) -> None:

            root_path: str = self.get_config("root_path")
            bin_path = os.path.join(root_path, "bin", "rattler-build")

            os.unlink(bin_path)

    def _resolve(self) -> Mapping[str, Any]:

        current = self._check()
        if current is not None:
            return current

        this_arch = platform.machine().lower()
        this_os = platform.system().lower()

        ARCH_MAP: Dict[str, Dict[str, str]] = {
            "linux": {
                "x86_64": "x86_64-unknown-linux-musl",
                "amd64": "x86_64-unknown-linux-musl",
                "64bit": "x86_64-unknown-linux-musl",
                "aarch64": "aarch64-unknown-linux-musl",
                "ppc64": "powerpc64le-unknown-linux-gnu",
            },
            "darwin": {
                "arm64": "aarch64-apple-darwin",
                "x86": "x86_64-apple-darwin",
                "64bit": "x86_64-apple-darwin",
                "amd64": "x86_64-apple-darwin",
            },
            "windows": {},
        }

        token = ARCH_MAP.get(this_os, {}).get(this_arch, None)
        if token is None:
            raise Exception(
                f"No micromamba executable available for: {this_os} / {this_arch}."
            )

        try:
            version = self.get_config("version")
        except Exception:
            version = "latest"

        url = f"https://github.com/prefix-dev/rattler-build/releases/download/v{version}/rattler-build-{token}"


        root_path: Path = self.get_config("root_path")
        # bin_path = root_path / "bin" / "micromamba"
        # bin_path.parent.mkdir(parents=True, exist_ok=True)
        terminal_print(f"Downloading rattler-build from '{url}'...")

        target_path = Path(os.path.join(root_path, "bin", "rattler-build"))
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with urlopen(url) as response:  # noqa
            with open(target_path, "wb") as f:  # open a file in write-binary mode
                f.write(response.read())  # write the content to the file

        os.chmod(target_path, 0o755)  # noqa

        current = self._check()
        if current is not None:
            return current
        else:
            raise Exception("Something went wrong.")
