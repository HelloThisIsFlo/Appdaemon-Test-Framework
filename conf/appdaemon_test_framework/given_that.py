class GivenThatWrapper:
    def __init__(self, hass_functions):
        self.hass_functions = hass_functions

        self.mocked_states = dict()

        def get_state_mock(entity_id):
            return self.mocked_states[entity_id]
        self.hass_functions['get_state'].side_effect = get_state_mock

    def state_of(self, entity_id):
        given_that_wrapper = self
        class IsWrapper:
            def is_set_to(self, state_to_set):
                given_that_wrapper.mocked_states[entity_id] = state_to_set
        return IsWrapper()

    def time_is(self, time_as_datetime):
        self.hass_functions['time'].return_value = time_as_datetime

    def mock_functions_are_cleared(self, clear_mock_states=False):
        for mocked_function in self.hass_functions.values():
            mocked_function.reset_mock()
        if clear_mock_states:
            self.mocked_states = dict()
