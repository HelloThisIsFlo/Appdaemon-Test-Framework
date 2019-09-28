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
        with pytest.raises(RuntimeError) as cm:
            assert_that('foo')
        assert 'Uninitalized automation instances:' in str(cm.value)

    def test_init_passes_with_initialized_automations(self, automation, assert_that):
        assert_that('foo')

    @pytest.mark.parametrize(
        "method",
        (
            ('was'),
            ('was_not'),
            ('listens_to'),
            ('registered'),
        )
    )
    def test_calling_method_before_init_raises(self, assert_that, method):
        with pytest.raises(Exception) as cm:
            getattr(assert_that, method)()
        assert 'AssertThat has not been initialized!' in str(cm.value)
