# -*- coding: utf-8 -*-
import shutil
from subprocess import PIPE, Popen
from typing import TYPE_CHECKING, Dict, List, Type

from pydantic2ts.cli.script import generate_json_schema

from kiara.context import Kiara
from kiara.interfaces.python_api.models.info import KiaraModelClassesInfo
from kiara_plugin.develop.schema import ModelSchemaExporter

if TYPE_CHECKING:
    from pydantic import BaseModel


class TypeScriptModelExporter(ModelSchemaExporter):
    def __init__(self, kiara: Kiara):

        self.json2ts_cmd: str = "json2ts"
        if not shutil.which(self.json2ts_cmd):
            raise Exception(
                "json2ts must be installed. Instructions can be found here: "
                "https://www.npmjs.com/package/json-schema-to-typescript"
            )

        super().__init__(kiara=kiara)

    def export_models(self, all_models: KiaraModelClassesInfo) -> Dict[str, str]:

        models: List[Type[BaseModel]] = [x.python_class.get_class() for x in all_models.item_infos.values()]  # type: ignore

        schema = generate_json_schema(models)

        # schema_dir = mkdtemp()
        # schema_file_path = os.path.join(schema_dir, "schema.json")
        # with open(schema_file_path, "w") as f:
        #     f.write(schema)

        p = Popen([self.json2ts_cmd], stdout=PIPE, stdin=PIPE, stderr=PIPE)
        stdout_data = p.communicate(input=schema.encode())[0]

        type_script_models = stdout_data.decode()

        return {"kiara_models.ts": type_script_models}

        # output = "/tmp/markus"
        # os.system(f'{self.json2ts_cmd} -i {schema_file_path} -o {output} --bannerComment ""')
        # shutil.rmtree(schema_dir)
        # clean_output_file(output)

        # all_content = []
        # all_model_paths = set()
        # for model in models:
        #     model_path = model.python_class.get_python_module().__file__
        #     all_model_paths.add(model_path)
        #
        # for model_path in all_model_paths:
        #     temp = tempfile.NamedTemporaryFile(suffix='_temp', prefix='kiara_model_gen_')
        #     generate_typescript_defs(module=model_path, output=temp.name)
        #     all_content.append(Path(temp.name).read_text())
        #     temp.close()
        # with output_file.open(mode='ta') as f:
        #     for c in all_content:
        #         f.write(c + "\n\n")
