# -*- coding: utf-8 -*-
from kiara import KiaraModule
from kiara.models.values.value import ValueMap
from kiara.modules import ValueSetSchema


class ExampleModule(KiaraModule):

    _module_type_name = "dict_test"

    def create_input_schema(
        self,
    ) -> ValueSetSchema:
        return {"dict": {"type": "dict"}}

    def create_outputs_schema(
        self,
    ) -> ValueSetSchema:

        return {"dict": {"type": "dict"}}

    def process(self, inputs: ValueMap, outputs: ValueMap):

        d = inputs.get_value_data("dict")

        outputs.set_values(dict=d.dict_data)
