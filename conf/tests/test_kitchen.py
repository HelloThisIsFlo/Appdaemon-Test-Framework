from apps.kitchen import Kitchen
import pytest
from mock import patch, MagicMock
from apps.entity_ids import ID

# TODO: Put this in config (through apps.yml, check doc)
PHONE_PUSHBULLET_ID = "OnePlus 5T"


@pytest.fixture
def kitchen(given_that):
    kitchen = Kitchen(
        None, None, None, None, None, None, None, None)
    kitchen.initialize()

    given_that.mock_functions_are_cleared()
    return kitchen


@pytest.fixture
def when_new(kitchen):
    class WhenNewWrapper:
        def motion(self):
            kitchen._new_motion(None, None, None)

        def no_more_motion(self):
            kitchen._no_more_motion(
                None,  None, None, None, None)

        def click_button(self):
            kitchen._new_button_click(None, None, None)

    return WhenNewWrapper()


class TestInitialization:
    def test_callbacks_are_registered(self, kitchen, hass_functions):
        # Given: The mocked callback Appdaemon registration functions
        listen_event = hass_functions['listen_event']
        listen_state = hass_functions['listen_state']

        # When: Calling `initialize`
        kitchen.initialize()

        # Then: callbacks are registered
        listen_event.assert_any_call(
            kitchen._new_button_click,
            'click',
            entity_id=ID['kitchen']['button'],
            click_type='single')

        listen_event.assert_any_call(
            kitchen._new_motion,
            'motion',
            entity_id=ID['kitchen']['motion_sensor'])

        listen_state.assert_any_call(
            kitchen._no_more_motion,
            ID['kitchen']['motion_sensor'],
            new='off')


class TestAutomaticLights:
    def test_turn_on(self, when_new, assert_that):
        when_new.motion()
        assert_that(ID['kitchen']['light']).was.turned_on()

    def test_turn_off(self, when_new, assert_that):
        when_new.no_more_motion()
        assert_that(ID['kitchen']['light']).was.turned_off()


DELAY_IN_MINUTES_BEFORE_TURNING_BACK_ON_WATER_HEATER = 10


class TestClickOnButton:
    def test_turn_off_water_heater(self, when_new, assert_that):
        when_new.click_button()
        assert_that(ID['bathroom']['water_heater']).was.turned_off()

    def test_send_notification(self, when_new, assert_that):
        when_new.click_button()
        assert_that('notify/pushbullet').was.called_with(
            message="Water Heater was turned OFF",
            target="OnePlus 5T")

    class TestAfterDelay:
        def test_turn_water_heater_back_on(self, when_new, time_travel, assert_that):
            when_new.click_button()
            time_travel.fast_forward(
                DELAY_IN_MINUTES_BEFORE_TURNING_BACK_ON_WATER_HEATER).minutes()
            assert_that(ID['bathroom']['water_heater']).was.turned_on()

        def test_send_notification(self, when_new, time_travel, assert_that):
            when_new.click_button()
            time_travel.fast_forward(
                DELAY_IN_MINUTES_BEFORE_TURNING_BACK_ON_WATER_HEATER).minutes()
            assert_that('notify/pushbullet').was.called_with(
                message="Water Heater was turned back ON",
                target="OnePlus 5T")
