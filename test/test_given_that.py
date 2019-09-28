from appdaemon.plugins.hass.hassapi import Hass
from appdaemontestframework import automation_fixture
import pytest
import datetime


class MockAutomation(Hass):
    def initialize(self):
        pass


@automation_fixture(MockAutomation)
def automation():
    pass


class Test_time_is:
    def test_sets_to_proper_datetime(self, given_that, automation):
        set_time = datetime.datetime(2020, 1, 1, 12, 0)
        given_that.time_is(set_time)
        assert automation.datetime() == set_time

    def test_set_time_while_callbacks_scheduled_throws_exception(self, given_that, automation):
        automation.run_in(lambda: None, 15)
        with pytest.raises(RuntimeError) as cm:
            given_that.time_is(datetime.datetime(2010, 1, 1, 0, 0))
        assert str(cm.value) == "You can not set start time while callbacks are scheduled"