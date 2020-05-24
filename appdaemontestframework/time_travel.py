from appdaemontestframework.hass_mocks import HassMocks
import datetime

class TimeTravelWrapper:
    """
    AppDaemon Test Framework Utility to simulate going forward in time
    """

    def __init__(self, hass_mocks: HassMocks):
        self._hass_mocks = hass_mocks

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
        self._hass_mocks.AD.sched.sim_fast_forward(datetime.timedelta(seconds=seconds_to_fast_forward))

    def _assert_current_time_seconds(self, expected_seconds_from_start):
        sched = self._hass_mocks.AD.sched
        elapsed_seconds = (sched.get_now_sync() - sched.sim_get_start_time()).total_seconds()
        assert elapsed_seconds == expected_seconds_from_start


class UnitsWrapper:
    def __init__(self, duration, function_with_arg_in_seconds):
        self.duration = duration
        self.function_with_arg_in_seconds = function_with_arg_in_seconds

    def minutes(self):
        self.function_with_arg_in_seconds(self.duration * 60)

    def seconds(self):
        self.function_with_arg_in_seconds(self.duration)
