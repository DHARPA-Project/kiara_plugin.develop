# -*- coding: utf-8 -*-

"""This module contains the value type classes that are used in the ``kiara_plugin.develop`` package.
"""
import os.path
from typing import Any, ClassVar, Mapping, Type

import structlog

from kiara.data_types import DataTypeConfig
from kiara.data_types.included_core_types import AnyType
from kiara.exceptions import KiaraException
from kiara.models.filesystem import KiaraFile
from kiara.models.module.pipeline import PipelineConfig
from kiara.models.values.value import SerializedData, Value

logger = structlog.getLogger()

class KiaraPipelineDataType(AnyType[PipelineConfig, DataTypeConfig]):

    _data_type_name: ClassVar[str] ="kiara_pipeline"
    @classmethod
    def python_class(cls) -> Type[PipelineConfig]:
        return PipelineConfig  # type: ignore

    def serialize(self, data: PipelineConfig) -> SerializedData:

        _data = {
            "data": {
                "type": "inline-json",
                "inline_data": data.get_raw_config(),
                "codec": "json",
            },
        }

        data_type_config = {
            "kiara_model_id": "instance.module_config.pipeline",
        }

        serialized_data = {
            "data_type": self.data_type_name,
            "data_type_config": data_type_config,
            "data": _data,
            "serialization_profile": "json",
            "metadata": {
                "environment": {},
                "deserialize": {
                    "python_object": {
                        "module_type": "load.pipeline",
                        "module_config": {
                            "value_type": "pipeline",
                            "target_profile": "python_object",
                            "serialization_profile": "json",
                        },
                    }
                },
            },
        }
        from kiara.models.values.value import SerializationResult

        serialized = SerializationResult(**serialized_data)
        return serialized
    def parse_python_obj(self, data: Any) -> PipelineConfig:

        if isinstance(data, PipelineConfig):
            return data
        elif isinstance(data, Mapping):
            return PipelineConfig.from_config(data=data)
        elif isinstance(data, KiaraFile):
            return PipelineConfig.from_file(data.path)  # type: ignore
        elif os.path.isfile(data):
            return PipelineConfig.from_file(data)  # type: ignore
        else:
            raise KiaraException(
                msg=f"Can't instantiate PipelineConfig with data of type '{type(data)}'."
            )

    def _validate(self, value: PipelineConfig) -> None:

        if not isinstance(value, PipelineConfig):
            raise Exception(f"Invalid type: {type(value)}.")

    def _pretty_print_as__terminal_renderable(
        self, value: "Value", render_config: Mapping[str, Any]
    ):

        pipeline_config: PipelineConfig = value.data
        return pipeline_config.create_renderable(**render_config)
