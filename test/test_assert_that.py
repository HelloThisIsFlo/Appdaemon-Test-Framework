from datetime import time, datetime

import appdaemon.plugins.hass.hassapi as hass
import pytest
from pytest import mark

from appdaemontestframework import automation_fixture


"""
Note:
The Appdaemon test framework was the fruit of a refactor of the tests
suite of one of the Appdaemon projects I was working on at the time.
Because it didn't start as a standalone project itself but was part of a test
suite, it didn't have tests itself.
(lessons learned, now my 'heavy' tests helpers are themselves tested :)

Anyways, what that means is: Most of the base functionality is tested only
through `integration_tests`.
New feature should come with the proper unit tests.
"""

LIGHT = 'light.some_light'
SWITCH = 'switch.some_switch'
TRANSITION_DURATION = 2


class MockAutomation(hass.Hass):
    def initialize(self):
        pass

    def turn_on_light(self, via_helper=False):
        if via_helper:
            self.turn_on(LIGHT)
        else:
            self.call_service('light/turn_on', entity_id=LIGHT)

    def turn_off_light(self, via_helper=False):
        if via_helper:
            self.turn_off(LIGHT)
        else:
            self.call_service('light/turn_off', entity_id=LIGHT)

    def turn_on_switch(self, via_helper=False):
        if via_helper:
            self.turn_on(SWITCH)
        else:
            self.call_service('switch/turn_on', entity_id=SWITCH)

    def turn_off_switch(self, via_helper=False):
        if via_helper:
            self.turn_off(SWITCH)
        else:
            self.call_service('switch/turn_off', entity_id=SWITCH)

    def turn_on_light_with_transition(self, via_helper=False):
        if via_helper:
            self.turn_on(LIGHT, transition=TRANSITION_DURATION)
        else:
            self.call_service(
                'light/turn_on',
                entity_id=LIGHT,
                transition=TRANSITION_DURATION
            )

    def turn_off_light_with_transition(self, via_helper=False):
        if via_helper:
            self.turn_off(LIGHT, transition=TRANSITION_DURATION)
        else:
            self.call_service(
                'light/turn_off',
                entity_id=LIGHT,
                transition=TRANSITION_DURATION
            )


@automation_fixture(MockAutomation)
def automation():
    pass


class TestTurnedOn:
    class TestViaService:
        def test_was_turned_on(self, assert_that, automation):
            assert_that(LIGHT).was_not.turned_on()
            automation.turn_on_light()
            assert_that(LIGHT).was.turned_on()

            assert_that(SWITCH).was_not.turned_on()
            automation.turn_on_switch()
            assert_that(SWITCH).was.turned_on()

        def test_with_kwargs(self, assert_that, automation):
            assert_that(LIGHT).was_not.turned_on()
            automation.turn_on_light_with_transition()
            assert_that(LIGHT).was.turned_on(transition=TRANSITION_DURATION)

    class TestViaHelper:
        def test_was_turned_on(self, assert_that, automation):
            assert_that(LIGHT).was_not.turned_on()
            automation.turn_on_light(via_helper=True)
            assert_that(LIGHT).was.turned_on()

            assert_that(SWITCH).was_not.turned_on()
            automation.turn_on_switch(via_helper=True)
            assert_that(SWITCH).was.turned_on()

        def test_with_kwargs(self, assert_that, automation):
            assert_that(LIGHT).was_not.turned_on()
            automation.turn_on_light_with_transition(via_helper=True)
            assert_that(LIGHT).was.turned_on(transition=TRANSITION_DURATION)


class TestTurnedOff:
    class TestViaService:
        def test_was_turned_off(self, assert_that, automation):
            assert_that(LIGHT).was_not.turned_off()
            automation.turn_off_light()
            assert_that(LIGHT).was.turned_off()

            assert_that(SWITCH).was_not.turned_off()
            automation.turn_off_switch()
            assert_that(SWITCH).was.turned_off()

        def test_with_kwargs(self, assert_that, automation):
            assert_that(LIGHT).was_not.turned_off()
            automation.turn_off_light_with_transition()
            assert_that(LIGHT).was.turned_off(transition=TRANSITION_DURATION)

    class TestViaHelper:
        def test_was_turned_off(self, assert_that, automation):
            assert_that(LIGHT).was_not.turned_off()
            automation.turn_off_light(via_helper=True)
            assert_that(LIGHT).was.turned_off()

            assert_that(SWITCH).was_not.turned_off()
            automation.turn_off_switch(via_helper=True)
            assert_that(SWITCH).was.turned_off()

        def test_with_kwargs(self, assert_that, automation):
            assert_that(LIGHT).was_not.turned_off()
            automation.turn_off_light_with_transition(via_helper=True)
            assert_that(LIGHT).was.turned_off(transition=TRANSITION_DURATION)
