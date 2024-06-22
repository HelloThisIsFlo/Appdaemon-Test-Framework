import appdaemon.plugins.hass.hassapi as hass
import pytest

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

    def call_invalid_service_name(self):
        self.call_service(
            'switch.turn_off',
            entity_id=SWITCH
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


class TestServiceNameValidation:
    class TestValidServiceName:
        def test_valid_service_asserted_and_is_called_does_not_raise(self, assert_that, automation):
            automation.turn_off_switch(via_helper=False)
            assert_that('switch/turn_off') \
                .was.called_with(entity_id=SWITCH)

        def test_valid_service_asserted_and_is_not_called_raises_assertion_error(self, assert_that, automation):
            with pytest.raises(AssertionError):
                assert_that('switch/turn_off') \
                    .was.called_with(entity_id=SWITCH)

    class TestInvalidServiceName:
        def test_invalid_service_asserted_and_is_called_raises_value_error(self, assert_that, automation):
            automation.call_invalid_service_name()
            with pytest.raises(ValueError):
                assert_that('switch.turn_off')\
                    .was.called_with(entity_id=SWITCH)

        def test_invalid_service_asserted_and_is_not_called_raises_value_or_assertion_error(self, assert_that, automation):
            with pytest.raises((ValueError, AssertionError)):
                assert_that('switch.turn_off')\
                    .was.called_with(entity_id=SWITCH)
