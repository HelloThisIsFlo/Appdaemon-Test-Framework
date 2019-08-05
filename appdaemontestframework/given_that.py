from mock import MagicMock

from appdaemontestframework.common import AppdaemonTestFrameworkError


class StateNotSetError(AppdaemonTestFrameworkError):
    def __init__(self, entity_id):
        super().__init__(f"""
        State for entity: '{entity_id}' was never set!
        Please make sure to set the state with `given_that.state_of({entity_id}).is_set_to(STATE)` 
        before trying to access the mocked state
        """)


class AttributeNotSetError(AppdaemonTestFrameworkError):
    pass


class GivenThatWrapper:
    def __init__(self, hass_functions):
        self.hass_functions = hass_functions
        self._init_mocked_states()
        self._init_mocked_passed_args()

    def _init_mocked_states(self):
        self.mocked_states = {}

        def get_state_mock(entity_id, *, attribute=None):
            if entity_id not in self.mocked_states:
                raise StateNotSetError(entity_id)

            state = self.mocked_states[entity_id]

            if attribute is None:
                return state['main']
            elif attribute == 'all':
                return state['attributes']
            else:
                return state['attributes'].get(attribute)

        self.hass_functions['get_state'].side_effect = get_state_mock

    def _init_mocked_passed_args(self):
        def make_magic_mock_behave_like_a_dict(magic_mock, dict_to_simulate):
            def should_mock(dict_method):
                dict_method_in_magic_mock = getattr(magic_mock, dict_method)
                return isinstance(dict_method_in_magic_mock, MagicMock)

            for dict_method in dir(dict_to_simulate):
                if should_mock(dict_method):
                    dict_method_in_magic_mock = getattr(
                        magic_mock, dict_method)
                    dict_method_in_magic_mock.side_effect = getattr(
                        dict_to_simulate, dict_method)

        self.mocked_passed_args = dict()
        make_magic_mock_behave_like_a_dict(
            self.hass_functions['passed_args'], self.mocked_passed_args)

    def state_of(self, entity_id):
        given_that_wrapper = self

        class IsWrapper:
            def is_set_to(self, state, attributes=None):
                if not attributes:
                    attributes = {}
                given_that_wrapper.mocked_states[entity_id] = {'main': state,
                                                               'attributes': attributes}

        return IsWrapper()

    def passed_arg(self, argument_key):
        given_that_wrapper = self

        class IsWrapper:
            def is_set_to(self, argument_value):
                given_that_wrapper.mocked_passed_args[argument_key] = argument_value

        return IsWrapper()

    def time_is(self, time_as_datetime):
        self.hass_functions['time'].return_value = time_as_datetime

    def mock_functions_are_cleared(self, clear_mock_states=False, clear_mock_passed_args=False):
        for mocked_function in self.hass_functions.values():
            mocked_function.reset_mock()
        if clear_mock_states:
            self._init_mocked_states()
        if clear_mock_passed_args:
            self._init_mocked_passed_args()
