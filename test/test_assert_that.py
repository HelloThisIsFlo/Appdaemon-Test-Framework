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


@automation_fixture(MockAutomation, initialize=False)
def uninited_automation():
    pass


class Test_init:
    def test_init_raises_with_uninitialized_automations(self, uninited_automation, assert_that):
        pass

    def test_init_raises_with_uninitialized_wrapper(self, assert_that):
        pass