import uuid

class TimeTravelWrapper:
    """
    AppDaemon Test Framework Utility to simulate going forward in time
    """

    def __init__(self, hass_mocks):
        # Access the `_hass_functions` through private member for now to avoid genearting deprecation
        # warnings while keeping compatibility.
        hass_functions = hass_mocks._hass_functions

        self.scheduler_mocks = SchedulerMocks()

        run_in_magic_mock = hass_functions['run_in']
        run_in_magic_mock.side_effect = self.scheduler_mocks.run_in_mock

        cancel_timer_magic_mock = hass_functions['cancel_timer']
        cancel_timer_magic_mock.side_effect = self.scheduler_mocks.cancel_timer_mock

    def fast_forward(self, duration):
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
        return UnitsWrapper(duration, self._fast_forward_seconds)

    def assert_current_time(self, expected_current_time):
        """
        Assert the current time is as expected

        Expected current time is expressed as a duration from T = 0

        Format:
        > time_travel.assert_current_time(10).minutes()
        > # Or
        > time_travel.assert_current_time(30).seconds()
        """
        return UnitsWrapper(expected_current_time, self._assert_current_time_seconds)


    def _fast_forward_seconds(self, seconds_to_fast_forward):
        self.scheduler_mocks.fast_forward(seconds_to_fast_forward)

    def _assert_current_time_seconds(self, expected_seconds_from_start):
        assert self.scheduler_mocks.now == expected_seconds_from_start


class UnitsWrapper:
    def __init__(self, duration, function_with_arg_in_seconds):
        self.duration = duration
        self.function_with_arg_in_seconds = function_with_arg_in_seconds

    def minutes(self):
        self.function_with_arg_in_seconds(self.duration * 60)

    def seconds(self):
        self.function_with_arg_in_seconds(self.duration)

class SchedulerMocks:
    """Class to provide functional mocks for the AppDaemon HASS scheduling functions"""
    def __init__(self):
        self.all_registered_callbacks = []
        self.now = 0

    def run_in_mock(self, callback, delay_in_s, **kwargs):
        handle = str(uuid.uuid4())
        self.all_registered_callbacks.append({
            'callback_function': callback,
            'delay_in_s': delay_in_s,
            'registered_at': self.now,
            'kwargs': kwargs,
            'handle': handle
        })
        return handle

    def cancel_timer_mock(self, handle):
        for callback in self.all_registered_callbacks:
            if callback['handle'] == handle:
                self.all_registered_callbacks.remove(callback)

    def fast_forward(self, seconds):
        self.now += seconds

        self._run_callbacks()

    def _run_callbacks(self):
        callback_run = []

        def _should_run(callback_registration):
            delay_in_s = callback_registration['delay_in_s']
            registered_at = callback_registration['registered_at']

            scheduled_time = registered_at + delay_in_s
            scheduled_now_or_before = scheduled_time <= self.now

            return scheduled_now_or_before

        def _run(callback_registration):
            kwargs = callback_registration['kwargs']
            callback_registration['callback_function'](kwargs)
            callback_run.append(callback_registration)

        def _remove_all_run():
            for registration in callback_run:
                self.all_registered_callbacks.remove(registration)

        for registration in self.all_registered_callbacks:
            if _should_run(registration):
                _run(registration)

        _remove_all_run()
