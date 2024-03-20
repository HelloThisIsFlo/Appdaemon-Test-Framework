from datetime import datetime

from appdaemontestframework.common import AppdaemonTestFrameworkError
from appdaemontestframework.hass_mocks import HassMocks


class StateNotSetError(AppdaemonTestFrameworkError):
    def __init__(self, entity_id: str) -> None:
        super().__init__(
            f"""
            State for entity: '{entity_id}' was never set!
            Please make sure to set the state with
            `given_that.state_of({entity_id}).is_set_to(STATE)`
            before trying to access the mocked state
            """
        )


class AttributeNotSetError(AppdaemonTestFrameworkError):
    pass


class GivenThatWrapper:
    def __init__(self, hass_mocks: HassMocks) -> None:
        self._hass_mocks = hass_mocks
        self._init_mocked_states()
        self._init_mocked_passed_args()

    def _init_mocked_states(self) -> None:
        self.mocked_states = {}

        def get_state_mock(entity_id=None, *, attribute=None):
            if entity_id is None:
                resdict = dict()
                for entityid in self.mocked_states:
                    state = self.mocked_states[entityid]
                    resdict.update(
                        {
                            entityid: {
                                "state": state["main"],
                                "attributes": state["attributes"],
                            }
                        }
                    )
                return resdict
            else:
                if entity_id not in self.mocked_states:
                    raise StateNotSetError(entity_id)

                state = self.mocked_states[entity_id]

                if attribute is None:
                    return state["main"]
                elif attribute == "all":

                    def format_time(timestamp: datetime):
                        if not timestamp:
                            return None
                        return timestamp.isoformat()

                    return {
                        "last_updated": format_time(state["last_updated"]),
                        "last_changed": format_time(state["last_changed"]),
                        "state": state["main"],
                        "attributes": state["attributes"],
                        "entity_id": entity_id,
                    }
                else:
                    return state["attributes"].get(attribute)

        self._hass_mocks.hass_functions["get_state"].side_effect = (
            get_state_mock
        )

        def entity_exists_mock(entity_id):
            return entity_id in self.mocked_states

        self._hass_mocks.hass_functions["entity_exists"].side_effect = (
            entity_exists_mock
        )

    def _init_mocked_passed_args(self) -> None:
        self.mocked_passed_args = self._hass_mocks.hass_functions["args"]
        self.mocked_passed_args.clear()

    def state_of(self, entity_id):
        given_that_wrapper = self

        class IsWrapper:
            def is_set_to(
                self,
                state,
                attributes=None,
                last_updated: datetime = None,
                last_changed: datetime = None,
            ):
                if not attributes:
                    attributes = {}
                given_that_wrapper.mocked_states[entity_id] = {
                    "main": state,
                    "attributes": attributes,
                    "last_updated": last_updated,
                    "last_changed": last_changed,
                }

        return IsWrapper()

    def passed_arg(self, argument_key):
        given_that_wrapper = self

        class IsWrapper:
            @staticmethod
            def is_set_to(argument_value):
                given_that_wrapper.mocked_passed_args[argument_key] = (
                    argument_value
                )

        return IsWrapper()

    def time_is(self, time_as_datetime) -> None:
        self._hass_mocks.AD.sched.sim_set_start_time(time_as_datetime)

    def mock_functions_are_cleared(
        self,
        clear_mock_states: bool = False,
        clear_mock_passed_args: bool = False,
    ) -> None:
        for mocked_function in self._hass_mocks.hass_functions.values():
            mocked_function.reset_mock()
        if clear_mock_states:
            self._init_mocked_states()
        if clear_mock_passed_args:
            self._init_mocked_passed_args()
