import pytest
from appdaemon.plugins.hass.hassapi import Hass
from pytest import raises

from appdaemontestframework import automation_fixture
from appdaemontestframework.given_that import StateNotSetError

LIGHT = 'light.some_light'


class MockAutomation(Hass):
    def initialize(self):
        pass

    def is_light_turned_on(self) -> bool:
        return self.get_state(LIGHT) == 'on'

    def get_light_brightness(self) -> int:
        return self.get_state(LIGHT, attribute='brightness')

    def get_all_attributes_from_light(self):
        return self.get_state(LIGHT, attribute='all')

    def get_without_using_keyword(self):
        return self.get_state(LIGHT, 'brightness')


@automation_fixture(MockAutomation)
def automation():
    pass


def test_state_was_never_set__raise_error(given_that, automation: MockAutomation):
    with raises(StateNotSetError, match=r'.*State.*was never set.*'):
        automation.get_light_brightness()


def test_set_and_get_state(given_that, automation: MockAutomation):
    given_that.state_of(LIGHT).is_set_to('off')
    assert not automation.is_light_turned_on()

    given_that.state_of(LIGHT).is_set_to('on')
    assert automation.is_light_turned_on()


def test_attribute_was_never_set__raise_error(given_that, automation: MockAutomation):
    given_that.state_of(LIGHT).is_set_to('on')
    assert automation.get_light_brightness() is None


def test_set_and_get_attribute(given_that, automation: MockAutomation):
    given_that.state_of(LIGHT).is_set_to('on', attributes={'brightness': 11})
    assert automation.get_light_brightness() == 11

    given_that.state_of(LIGHT).is_set_to('on', {'brightness': 22})
    assert automation.get_light_brightness() == 22


def test_set_and_get_all_attribute(given_that, automation: MockAutomation):
    given_that.state_of(LIGHT).is_set_to('on', attributes={'brightness': 11, 'color': 'blue'})
    assert automation.get_all_attributes_from_light() == {'brightness': 11, 'color': 'blue'}


@pytest.mark.only
def test_throw_typeerror_when_attributes_arg_not_passed_via_keyword(given_that, automation: MockAutomation):
    given_that.state_of(LIGHT).is_set_to('on', attributes={'brightness': 11, 'color': 'blue'})
    with pytest.raises(TypeError):
        automation.get_without_using_keyword()
