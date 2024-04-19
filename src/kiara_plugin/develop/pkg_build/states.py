# -*- coding: utf-8 -*-
import abc
from typing import Any, Dict, Mapping, Union


class State(abc.ABC):
    def __init__(self, state_id: str, **config):

        self._state_id: str = state_id
        self._config: Mapping[str, Any] = config
        self._states: Union[None, "States"] = None
        self._state_details: Union[None, Mapping[str, None]] = None

    @property
    def state_id(self):
        return self._state_id

    def ensure_state(self, state_id: str):

        if self._states is None:
            raise Exception("States not set (yet). This is a bug.")

        self._states.get_state(state_id).resolve()

    def get_other_state_detail(self, state_id: str, key: str):

        if self._states is None:
            raise Exception("States not set (yet). This is a bug.")

        return self._states.get_state(state_id).get_detail(key)

    def get_config(self, key: str) -> Any:

        if key not in self._config.keys():
            raise Exception(
                f"No config key '{key}' in state type '{self.__class__.__name__}'."
            )
        return self._config[key]

    def resolve(self) -> Mapping[str, Any]:

        if self._state_details is not None:
            return self._state_details

        self._state_details = self._resolve()
        if self._state_details is None:
            raise Exception(
                f"No state details for: {self.__class__.__name__}. This is a bug."
            )
        return self._state_details

    def purge(self):

        self._purge()
        self._state_details = None

    @abc.abstractmethod
    def _resolve(self) -> Mapping[str, Any]:
        pass

    @abc.abstractmethod
    def _purge(self):
        pass

    def get_detail(self, key: str):

        details = self.resolve()
        return details[key]

    def get_details(self) -> Mapping[str, Any]:
        return self.resolve()


class States(object):
    def __init__(self) -> None:

        self._states: Dict[str, State] = {}

    def add_state(self, state: State):

        if state.state_id in self._states.keys():
            raise Exception(
                f"Can't add state with id '{state.state_id}: id already registered."
            )
        self._states[state.state_id] = state
        state._states = self

    def resolve(self, state_id: str):
        self._states[state_id].resolve()

    def get_state(self, state_id: str):
        return self._states[state_id]

    def get_state_detail(self, state_id: str, key: str):
        return self._states[state_id].get_detail(key)

    def get_state_details(self, state_id: str) -> Mapping[str, Any]:
        return self._states[state_id].get_details()
