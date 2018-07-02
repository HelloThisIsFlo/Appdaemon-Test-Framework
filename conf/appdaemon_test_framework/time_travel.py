
class TimeTravelWrapper:
    """
    Simulate going forward in time

    Format:
    > time_travel.fast_forward(10).minutes()
    > # Or
    > time_travel.fast_forward(30).seconds()

    WARNING: You can not chain the calls. Only call `time_travel` once per test
    """

    def __init__(self, hass_functions):
        self.run_in_mock = hass_functions['run_in']

    def fast_forward(self, duration):
        time_travel_wrapper = self

        class UnitsWrapper:
            def minutes(self):
                time_travel_wrapper._fast_forward_minutes(duration)

            def seconds(self):
                time_travel_wrapper._fast_forward_seconds(duration)

        return UnitsWrapper()

    def _fast_forward_minutes(self, minutes):
        self._fast_forward_seconds(minutes * 60)

    def _fast_forward_seconds(self, seconds_to_fast_forward):
        all_registered_callbacks = []
        for call in self.run_in_mock.call_args_list:
            args, _ = call
            callback, delay_in_s = args
            all_registered_callbacks.append({
                'callback_function': callback,
                'delay_in_s': delay_in_s
            })

            for registered_callback in all_registered_callbacks:
                if registered_callback['delay_in_s'] <= seconds_to_fast_forward:
                    registered_callback['callback_function']()
