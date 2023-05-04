"""Tests for When wrapper."""


import appdaemon.plugins.hass.hassapi as hass

from appdaemontestframework import automation_fixture


class LivingRoomMotionLight(hass.Hass):
    """Hass app for testing."""

    def initialize(self):
        """Initialise."""
        self.listen_state(self.light_on, "motion_sensor2")
        self.listen_state(self.light_on, "motion_sensor", new="on")
        self.listen_state(self.light_off, "motion_sensor", new="off")

    def light_on(
        self, entity: str, attribute: str, old: str, new: str, kwargs: dict
    ) -> None:
        """Turn light on."""
        # pylint: disable=too-many-arguments
        # ^^ method signature inherited from appdaemon
        self.turn_on("light_switch")

    def light_off(
        self, entity: str, attribute: str, old: str, new: str, kwargs: dict
    ) -> None:
        # pylint: disable=too-many-arguments
        # ^^ method signature inherited from appdaemon
        """Turn light off."""
        self.turn_off("light_switch")


@automation_fixture(LivingRoomMotionLight)
def living_room_motion_light():
    """App framework initialisation."""


def test_when(living_room_motion_light, given_that, when, assert_that):
    """Callback is called as expected."""
    given_that.state_of("motion_sensor").is_set_to("off")
    when.state_of("motion_sensor").is_set_to("on")
    assert_that("light_switch").was.turned_on()


def test_when_no_entity(
    living_room_motion_light, given_that, when, assert_that
):
    """Callback is not called as expected."""
    given_that.state_of("motion_sensor").is_set_to("off")
    when.state_of("motion_sensor").is_set_to("off")
    assert_that("light_switch").was_not.turned_on()


def test_when_no_specific_state(
    living_room_motion_light, given_that, when, assert_that
):
    """Callbacks with no state are called as expected."""
    given_that.state_of("motion_sensor2").is_set_to("something")
    when.state_of("motion_sensor2").is_set_to("whatever")
    assert_that("light_switch").was.turned_on()


def test_when_several_callbacks(
    living_room_motion_light, given_that, when, assert_that
):
    """`when` triggering Several callbacks work as expected."""
    given_that.state_of("motion_sensor").is_set_to("off")
    when.state_of("motion_sensor").is_set_to("off")
    assert_that("light_switch").was.turned_off()
    assert_that("light_switch").was_not.turned_on()
