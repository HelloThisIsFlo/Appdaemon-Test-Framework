
class TimeTravelWrapper:
    """
    Simulate going forward in time.

    It calls all the functions that have been registered with AppDaemon
    for a later schedule run. A function is only called if it's scheduled
    time is before or at the simulated time.

    You can chain the calls and call `fast_forward` multiple times in a single test


    Format:
    > time_travel.fast_forward(10).minutes()
    > # Or
    > time_travel.fast_forward(30).seconds()

    """

    def __init__(self, hass_functions):
        self.run_in_mock = RunInMock()

        run_in_magic_mock = hass_functions['run_in']
        run_in_magic_mock.side_effect = self.run_in_mock

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
        self.run_in_mock.fast_forward(seconds_to_fast_forward)


class RunInMock:
    #  self.run_in(self._after_delay, minutes * 60)
    def __init__(self):
        self.all_registered_callbacks = []
        self._now = 0

    def __call__(self, callback, delay_in_s):
        self.all_registered_callbacks.append({
            'callback_function': callback,
            'delay_in_s': delay_in_s,
            'registered_at': self._now
            # TODO: Add support for kwargs
        })

    def fast_forward(self, seconds):
        self._now += seconds

        self._run_callbacks()

    def _run_callbacks(self):
        def _should_run(callback_registration):
            delay_in_s = callback_registration['delay_in_s']
            registered_at = callback_registration['registered_at']

            scheduled_time = registered_at + delay_in_s
            scheduled_now_or_before = scheduled_time <= self._now

            return scheduled_now_or_before

        def _run(callback_registration):
            kwargs_to_pass_to_callback = {}  # TODO: Add support!
            registration['callback_function'](kwargs_to_pass_to_callback)

        def _remove(callback_registration):
            self.all_registered_callbacks.remove(callback_registration)

        for registration in self.all_registered_callbacks:
            if _should_run(registration):
                _run(registration)
                _remove(registration)
