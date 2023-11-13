# -*- coding: utf-8 -*-
import abc
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Union

from pydantic import BaseModel, Field, PrivateAttr

from kiara.api import Kiara
from kiara.interfaces.python_api.models.info import (
    KiaraModelClassesInfo,
    KiaraModelTypeInfo,
)
from kiara.utils.cli import terminal_print


class ModelFilter(BaseModel):

    filter: Union[str, List[str]] = Field(
        description="The filter(s), either a string token, or a path to a file containing a list of tokens."
    )

    _filters: Union[None, List[str]] = PrivateAttr(default=None)

    @property
    def all_filter_tokens(self) -> List[str]:

        if self._filters is not None:
            return self._filters

        if isinstance(self.filter, str):
            filters = [self.filter]
        else:
            filters = self.filter

        final_filters: List[str] = []
        for f in filters:
            if os.path.isfile(os.path.realpath(f)):
                lines = Path(f).read_text().splitlines()
                final_filters.extend((line.strip() for line in lines))
            else:
                final_filters.append(f.strip())
        self._filters = final_filters
        return self._filters

    def model_matches(
        self, model_cls: KiaraModelTypeInfo, also_check_class_name: bool = False
    ) -> bool:

        if not self.all_filter_tokens:
            return True

        for f in self.all_filter_tokens:
            token = model_cls.type_name
            if f.lower() in token.lower() or f.lower() in token.lower():
                return True

            if also_check_class_name:
                token = model_cls.python_class.full_name
                if f.lower() in token.lower() or f.lower() in token.lower():
                    return True

        return False


class ModelSchemaExporter(abc.ABC):
    def __init__(self, kiara: Kiara):

        self._kiara: Kiara = kiara

    def translate(
        self,
        filters: Union[None, str, Iterable[str]] = None,
        exclude: Union[Iterable[str], None] = None,
    ) -> Dict[str, str]:

        if not filters:
            _filters = ModelFilter(filter=[])
        elif isinstance(filters, str):
            _filters = ModelFilter(filter=[filters])
        else:
            _filters = ModelFilter(filter=filters)

        final_filters = _filters.all_filter_tokens

        all_models = self._kiara.kiara_model_registry.all_models

        if final_filters:
            _temp = {}
            for model_id, model_cls in all_models.item_infos.items():

                match = _filters.model_matches(model_cls, also_check_class_name=True)
                if match:
                    _temp[model_id] = model_cls
            all_models = KiaraModelClassesInfo(
                group_title="Matching models", item_infos=_temp
            )

        if exclude:
            _temp = {}
            for model_id, model_cls in all_models.item_infos.items():
                for excl in exclude:
                    if (
                        excl.lower() in model_id.lower()
                        or excl.lower() in model_cls.__name__.lower()  # type: ignore
                    ):
                        break
                    else:
                        _temp[model_id] = model_cls
            all_models = KiaraModelClassesInfo(
                group_title="Matching models", item_infos=_temp
            )

        if not all_models:
            return {}

        return self.export_models(all_models)

    def export(
        self,
        output_folder: Union[None, str, Path] = None,
        filters: Union[None, str, Iterable[str]] = None,
        exclude: Union[Iterable[str], None] = None,
        force: bool = False,
    ):

        if not output_folder:
            _output_folder = Path.cwd()
        elif isinstance(output_folder, str):
            _output_folder = Path(output_folder)
        else:
            _output_folder = output_folder

        if _output_folder.is_file():
            raise Exception(
                f"Can't export models: output folder '{_output_folder}' is a file."
            )

        if not _output_folder.exists():
            _output_folder.mkdir(parents=True)

        translated = self.translate(filters=filters, exclude=exclude)
        if not translated:
            terminal_print()
            terminal_print(
                "No matching models found or translated by exporter. Doing nothing..."
            )
            sys.exit(1)

        if not force:
            exist = []
            for model_id, model in translated.items():
                output_file = _output_folder / f"{model_id}.ts"
                if output_file.exists():
                    exist.append(output_file)

            if exist:
                terminal_print()
                terminal_print(
                    "Can't export models, the following exported models already exist (and 'force' not set):\n"
                )
                for t in exist:
                    terminal_print(f" - [i]{t}[/i]")
                terminal_print()
                sys.exit(1)

        files = []
        for model_id, model in translated.items():
            output_file = _output_folder / f"{model_id}.ts"
            output_file.write_text(model)
            files.append(output_file)

        terminal_print()
        terminal_print("Exported models:\n")
        for t in files:
            terminal_print(f" - [i]{t}[/i]")

        terminal_print()

    @abc.abstractmethod
    def export_models(self, all_models: KiaraModelClassesInfo) -> Dict[str, str]:
        pass
