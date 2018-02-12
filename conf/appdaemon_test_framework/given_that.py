class GivenThatWrapper:
    def __init__(self, hass_functions):
        self.hass_functions = hass_functions

    def state_of(self, entity_id):
        get_state_function = self.hass_functions['get_state']
        class IsWrapper:
            def is_set_to(self, state_to_set):
                get_state_function.return_value = state_to_set
        return IsWrapper()
    
    def time_is(self, time_as_datetime):
        self.hass_functions['time'].return_value = time_as_datetime
