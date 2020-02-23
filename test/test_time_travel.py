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


def test_callback_not_called_before_timeout(time_travel, automation):
    foo = mock.Mock()
    automation.run_in(foo, 10)
    time_travel.fast_forward(5).seconds()
    foo.assert_not_called()


def test_callback_called_after_timeout(time_travel, automation):
    foo = mock.Mock()
    automation.run_in(foo, 10)
    time_travel.fast_forward(20).seconds()
    foo.assert_called()


def test_canceled_timer_does_not_run_callback(time_travel, automation):
    foo = mock.Mock()
    handle = automation.run_in(foo, 10)
    time_travel.fast_forward(5).seconds()
    automation.cancel_timer(handle)
    time_travel.fast_forward(10).seconds()
    foo.assert_not_called()


class Test_fast_forward:
    @staticmethod
    @pytest.fixture
    def automation_at_noon(automation, time_travel, given_that):
        given_that.time_is(datetime.datetime(2020, 1, 1, 12, 0))
        return automation

    def test_seconds(self, time_travel, automation_at_noon):
        time_travel.fast_forward(600).seconds()
        assert automation_at_noon.datetime() == datetime.datetime(2020, 1, 1, 12, 10)

    def test_minutes(self, time_travel, automation_at_noon):
        time_travel.fast_forward(90).minutes()
        assert automation_at_noon.datetime() == datetime.datetime(2020, 1, 1, 13, 30)


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

    def test_time_is_correct_when_callback_it_run(self, time_travel, given_that, automation):
        given_that.time_is(datetime.datetime(2020, 1, 1, 12, 0))

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