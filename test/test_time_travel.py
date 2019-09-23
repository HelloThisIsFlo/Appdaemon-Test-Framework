from appdaemon.plugins.hass.hassapi import Hass
from appdaemontestframework import automation_fixture
import mock
import pytest
import datetime

class MockAutomation(Hass):
    def initialize(self):
        pass


@automation_fixture(MockAutomation)
def automation():
    pass


class Test_fast_forward:
    @staticmethod
    @pytest.fixture
    def automation_at_noon(automation, time_travel):
        time_travel.reset_time(datetime.datetime(2020, 1, 1, 12, 0))
        return automation

    class Test_to:
        def test_to_time_in_future(self, time_travel, automation_at_noon):
            time_travel.fast_forward().to(datetime.time(15, 0))
            assert automation_at_noon.datetime() == datetime.datetime(2020, 1, 1, 15, 0)

        def test_to_time_in_past_goes_to_tomorrow(self, time_travel, automation_at_noon):
            time_travel.fast_forward().to(datetime.time(11, 0))
            assert automation_at_noon.datetime() == datetime.datetime(2020, 1, 2, 11, 0)

        def test_to_datetime(self, time_travel, automation_at_noon):
            time_travel.fast_forward().to(datetime.datetime(2020, 1, 15, 11, 0))
            assert automation_at_noon.datetime() == datetime.datetime(2020, 1, 15, 11, 0)

        def test_to_datetime_in_past_raises_exception(self, time_travel, automation_at_noon):
            with pytest.raises(ValueError):
                time_travel.fast_forward().to(datetime.datetime(2009, 1, 15, 11, 0))

        def test_to_negative_timedelta_raises_exception(self, time_travel, automation_at_noon):
            with pytest.raises(ValueError):
                time_travel.fast_forward().to(datetime.timedelta(minutes=-10))

        def test_to_datetime(self, time_travel, automation_at_noon):
            time_travel.fast_forward().to(datetime.timedelta(hours=5))
            assert automation_at_noon.datetime() == datetime.datetime(2020, 1, 1, 17, 0)

    def test_seconds(self, time_travel, automation_at_noon):
        time_travel.fast_forward(600).seconds()
        assert automation_at_noon.datetime() == datetime.datetime(2020, 1, 1, 12, 10)

    def test_minutes(self, time_travel, automation_at_noon):
        time_travel.fast_forward(90).minutes()
        assert automation_at_noon.datetime() == datetime.datetime(2020, 1, 1, 13, 30)

    def test_hours(self, time_travel, automation_at_noon):
        time_travel.fast_forward(3).hours()
        assert automation_at_noon.datetime() == datetime.datetime(2020, 1, 1, 15, 00)


class Test_callback_execution:
    def test_callbacks_are_run_in_time_order(self, time_travel, automation):
        first_mock = mock.Mock()
        second_mock = mock.Mock()
        third_mock = mock.Mock()
        manager = mock.Mock()
        manager.attach_mock(first_mock, 'first_mock')
        manager.attach_mock(second_mock, 'second_mock')
        manager.attach_mock(third_mock, 'third_mock')

        automation.run_in(second_mock, 20)
        automation.run_in(third_mock, 30)
        automation.run_in(first_mock, 10)

        time_travel.fast_forward(30).seconds()

        expected_call_order = [mock.call.first_mock({}), mock.call.second_mock({}), mock.call.third_mock({})]
        assert manager.mock_calls == expected_call_order

    def test_callback_not_called_before_timeout(self, time_travel, automation):
        callback_mock = mock.Mock()
        automation.run_in(callback_mock, 10)
        time_travel.fast_forward(5).seconds()
        callback_mock.assert_not_called()

    def test_callback_called_after_timeout(self, time_travel, automation):
        scheduled_callback = mock.Mock(name="Scheduled Callback")
        automation.run_in(scheduled_callback, 10)
        time_travel.fast_forward(20).seconds()
        scheduled_callback.assert_called()

    def test_canceled_timer_does_not_run_callback(self, time_travel, automation):
        callback_mock = mock.Mock()
        handle = automation.run_in(callback_mock, 10)
        time_travel.fast_forward(5).seconds()
        automation.cancel_timer(handle)
        time_travel.fast_forward(10).seconds()
        callback_mock.assert_not_called()

    def test_time_is_correct_when_callback_it_run(self, time_travel, automation):
        time_travel.reset_time(datetime.datetime(2020, 1, 1, 12, 0))

        time_when_called = []
        def callback(kwargs):
            nonlocal time_when_called
            time_when_called.append(automation.datetime())

        automation.run_in(callback, 1)
        automation.run_in(callback, 15)
        automation.run_in(callback, 65)
        time_travel.fast_forward(90).seconds()

        expected_call_times = [
            datetime.datetime(2020, 1, 1, 12, 0, 1),
            datetime.datetime(2020, 1, 1, 12, 0, 15),
            datetime.datetime(2020, 1, 1, 12, 1, 5),
        ]
        assert expected_call_times == time_when_called

    def test_callback_called_with_correct_args(self, time_travel, automation):
        callback_mock = mock.Mock()
        automation.run_in(callback_mock, 1, arg1='asdf', arg2='qwerty')
        time_travel.fast_forward(10).seconds()
        callback_mock.assert_called_once_with({'arg1': 'asdf', 'arg2': 'qwerty'})

    def test_repeating_schedule_called_multiple_times(self, time_travel, automation):
        callback_mock = mock.Mock()
        automation.run_minutely(callback_mock, None)
        time_travel.fast_forward(10).minutes()
        assert callback_mock.call_count == 10


class Test_reset_time:
    def test_resets_to_proper_datetime(self, time_travel, automation):
        reset_time = datetime.datetime(2020, 1, 1, 12, 0)
        time_travel.reset_time(reset_time)
        assert automation.datetime() == reset_time

    def test_reset_time_in_past_throws_exception(self, time_travel):
        with pytest.raises(ValueError) as cm:
            time_travel.reset_time(datetime.datetime(1990, 1, 1, 0, 0))
        assert str(cm.value) == 'You can not fast forward to a time in the past.'


class Test_run_daily:
    def test_run_daily_runs_for_several_days(self, time_travel, automation):
        callback = mock.Mock()
        automation.run_daily(callback, start=datetime.time(18))
        days_to_run = 10
        for i in range(days_to_run):
            time_travel.fast_forward().to(datetime.time(18))
            callback.assert_called()
        assert callback.call_count == days_to_run