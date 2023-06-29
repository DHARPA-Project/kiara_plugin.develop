# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, Any, Mapping, Type

import orjson

from kiara.models.module.jobs import JobLog
from kiara.models.module.pipeline import PipelineConfig
from kiara.models.values.value import SerializedData, Value, ValueMap
from kiara.modules import KiaraModule, ValueMapSchema
from kiara.modules.included_core_modules.create_from import CreateFromModule
from kiara.modules.included_core_modules.serialization import DeserializeValueModule

if TYPE_CHECKING:
    from kiara.models.filesystem import KiaraFile, KiaraFileBundle


class CreatePipelineModule(CreateFromModule):

    _module_type_name = "create.pipeline"

    def create__pipeline__from__file(self, source_value: Value) -> Any:

        from kiara.models.module.pipeline import PipelineConfig

        file: KiaraFile = source_value.data
        pipeline_config = PipelineConfig.from_file(path=file.path)

        return pipeline_config


class LoadPipelineConfig(DeserializeValueModule):

    _module_type_name = "load.pipeline"

    @classmethod
    def retrieve_supported_target_profiles(cls) -> Mapping[str, Type]:
        return {"python_object": PipelineConfig}

    @classmethod
    def retrieve_supported_serialization_profile(cls) -> str:
        return "json"

    @classmethod
    def retrieve_serialized_value_type(cls) -> str:
        return "pipeline"

    def to__python_object(self, data: SerializedData, **config: Any) -> PipelineConfig:

        chunks = data.get_serialized_data("data")
        assert chunks.get_number_of_chunks() == 1
        _chunks = list(chunks.get_chunks(as_files=False))
        assert len(_chunks) == 1

        bytes_string: bytes = _chunks[0]  # type: ignore
        model_data = orjson.loads(bytes_string)

        obj = PipelineConfig.from_config(model_data)
        return obj

class CollectPipelines(KiaraModule):

    _module_type_name = "collect.pipelines"

    def create_inputs_schema(
        self,
    ) -> ValueMapSchema:

        return {
            "pipeline_files": {
                "type": "file_bundle",
                "doc": "A file bundle containing pipeline files in json or yaml format.",
            }
        }

    def create_outputs_schema(
        self,
    ) -> ValueMapSchema:

        return {
            "pipelines": {
                "type": "table",
                "doc": "A table with the  pipeline data.",
            }
        }

    def process(self, inputs: ValueMap, outputs: ValueMap, job_log: JobLog):

        pipeline_files: KiaraFileBundle = inputs["pipeline_files"].data

        pipelines = {}
        for path, pipeline_file in pipeline_files.included_files.items():
            if pipeline_file.file_extension in ["json", "yaml", "yml"]:
                try:
                    pipeline_config = PipelineConfig.from_file(path=pipeline_file.path)
                    pipelines[path] = pipeline_config
                    job_log.add_log(f"parsed pipeline for: {path}")
                except Exception as e:
                    job_log.add_log(f"ignoring invalid pipeline file '{path}': {e}")

        from kiara.utils.cli import terminal_print
        for path, pipeline_config in pipelines.items():
            terminal_print(pipeline_config.create_renderable())
        pipelines_table = None
        outputs.set_value("pipelines", pipelines_table)
