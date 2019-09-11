from appdaemon.plugins.hass.hassapi import Hass
from appdaemontestframework import automation_fixture
import mock


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
