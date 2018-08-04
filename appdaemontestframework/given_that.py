from mock import MagicMock


class GivenThatWrapper:
    def __init__(self, hass_functions):
        self.hass_functions = hass_functions
        self._init_mocked_states()
        self._init_mocked_passed_args()

    def _init_mocked_states(self):
        self.mocked_states = dict()
        self.hass_functions['get_state'].side_effect = lambda entity_id: self.mocked_states[entity_id]

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
            def is_set_to(self, state_to_set):
                given_that_wrapper.mocked_states[entity_id] = state_to_set
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
