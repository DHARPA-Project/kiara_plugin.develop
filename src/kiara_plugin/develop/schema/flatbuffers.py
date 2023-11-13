# -*- coding: utf-8 -*-
import os
import typing
import uuid
from typing import Any, Dict, Mapping, Tuple, Type

from pydantic import BaseModel

from kiara.context import Kiara
from kiara.interfaces.python_api.models.info import (
    KiaraModelClassesInfo,
    KiaraModelTypeInfo,
)
from kiara.models import KiaraModel
from kiara_plugin.develop.schema import ModelSchemaExporter

TYPE_MAP = {
    str: "string",
    int: "long",
    bool: "bool",
    uuid.UUID: "UUID",
}


class FlatbuffersSchemaExporter(ModelSchemaExporter):
    def __init__(self, kiara: Kiara):

        # self.flatc_cmd: str = "flatc"
        # if not shutil.which(self.flatc_cmd):
        #     raise Exception(
        #         "flatc must be installed."
        #     )
        self._schema_def_template = kiara.render_registry.get_template(
            "flatbuffers/schema_def.fbs.j2", "kiara_plugin.develop"
        )
        super().__init__(kiara=kiara)

    def get_field_type(self, cls: Type):

        if cls == typing.Any:
            return "__ANY__"

        if isinstance(cls, typing.TypeVar):
            return "__TYPE_VAR__"

        if cls in TYPE_MAP.keys():
            return TYPE_MAP[cls]

        if isinstance(cls, type):
            if issubclass(cls, KiaraModel):
                return f"kiara_models.{cls._kiara_model_id}"  # type: ignore
            elif issubclass(cls, BaseModel):
                return f"__BASE_MODEL__({cls})"
            else:
                raise Exception(f"Can't handle field type: {cls}.")
        else:
            raise Exception(f"Can't handle field: {cls} (type: {type(cls)}).")

    def parse_child_model(self, model: Type[BaseModel]):

        raise NotImplementedError("Flatbuffer exporting not implemented yet.")

        # fields = {}
        # for field_name, field in model.model_fields.items():
        #     field_type = self.get_field_type(field.type_)
        #     fields[field_name] = {
        #         "type": field_type,
        #     }
        #
        # return fields

    def parse_dict(self, data: Mapping[str, Any]):

        fields = {}
        for field_name, field in data.items():
            field_type = self.get_field_type(field.type_)

            fields[field_name] = {
                "type": field_type,
            }

        return fields

    def export_model(self, model: KiaraModelTypeInfo) -> Tuple[str, str]:

        tokens = model.type_name.split(".", maxsplit=1)
        if len(tokens) == 1:
            namespace = "kiara_models"
            model_name = tokens[0]
        else:
            namespace = f"kiara_models.{tokens[0]}"
            model_name = tokens[1]

        cls = model.python_class.get_class()
        if issubclass(cls, BaseModel):
            fields = self.parse_child_model(cls)
        else:
            raise NotImplementedError()

        conf = {
            "namespace": namespace,
            "model_name": model_name,
            "fields": fields,
        }
        result = self._schema_def_template.render(**conf)
        full_path = os.path.join(*namespace.split("."), f"{model_name}.fbs")
        return full_path, result

    def export_models(self, all_models: KiaraModelClassesInfo) -> Dict[str, str]:

        result: Dict[str, str] = {}
        for model in all_models.item_infos.values():
            path, exported = self.export_model(model)
            result[path] = exported

        return result
