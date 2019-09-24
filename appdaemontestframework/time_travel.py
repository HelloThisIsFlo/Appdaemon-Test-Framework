import datetime


class TimeTravelWrapper:
    """
    AppDaemon Test Framework Utility to simulate going forward in time
    """

    def __init__(self, hass_mock):
        self._hass_mock = hass_mock

    def set_start_time(self, time):
        """Set the start time of the simulation. You can not call this once you have registed any callbacks

        if time is a datetime, it will set to that absolution time.
        if time is just a time, it will set the time, but leave the day the same.

        Format:
        > time_travel.set_start_time(datetime.datetime(2019, 04, 05, 14, 13))
        > # or if you don't care about the date
        > time_travel.set_start_time(datetime.time(14, 13))
        """
        #TODO: don't call private interface
        self._hass_mock._schedule_mocks.set_start_time(time)

    def fast_forward(self, duration=None):
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
        > # or
        > time_travel.fast_forward(3).hours()
        > # or
        > time_travel.fast_forward().to(datetime.time(14, 55))
        """
        if duration:
            return UnitsWrapper(duration, self._fast_forward_seconds)
        else:
            return AbsoluteWrapper(self._hass_mock._schedule_mocks.fast_forward)

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
        self._hass_mock._schedule_mocks.fast_forward(datetime.timedelta(seconds=seconds_to_fast_forward))

    def _assert_current_time_seconds(self, expected_seconds_from_start):
        assert self._hass_mock._schedule_mocks.elapsed_seconds() == expected_seconds_from_start


class AbsoluteWrapper:
    def __init__(self, function_for_to_set_absolute_time):
        self.function_for_to_set_absolute_time = function_for_to_set_absolute_time

    def to(self, time):
        self.function_for_to_set_absolute_time(time)


class UnitsWrapper:
    def __init__(self, duration, function_with_arg_in_seconds):
        self.duration = duration
        self.function_with_arg_in_seconds = function_with_arg_in_seconds

    def hours(self):
        self.function_with_arg_in_seconds(self.duration * 60 * 60)

    def minutes(self):
        self.function_with_arg_in_seconds(self.duration * 60)

    def seconds(self):
        self.function_with_arg_in_seconds(self.duration)




