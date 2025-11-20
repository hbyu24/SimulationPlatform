from concordia.typing import entity_component
from concordia.typing import logging as logging_typing

class Observation(entity_component.ContextComponent):
    def __init__(self, clock_now, timeframe, pre_act_key: str, logging_channel: logging_typing.LoggingChannel):
        self._logging_channel = logging_channel
        self._pre_act_key = pre_act_key
    def set_entity(self, entity: entity_component.EntityWithComponents) -> None:
        pass
    def get_pre_act_value(self) -> str:
        return ''
    def pre_act(self, unused_action_spec) -> str:
        return ''

class ObservationSummary(entity_component.ContextComponent):
    def __init__(self, model, clock_now, timeframe_delta_from, timeframe_delta_until, components, pre_act_key: str, logging_channel: logging_typing.LoggingChannel):
        self._logging_channel = logging_channel
        self._pre_act_key = pre_act_key
    def set_entity(self, entity: entity_component.EntityWithComponents) -> None:
        pass
    def get_pre_act_value(self) -> str:
        return ''
    def pre_act(self, unused_action_spec) -> str:
        return ''
