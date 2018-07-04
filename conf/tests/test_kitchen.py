from apps.kitchen import Kitchen
import pytest
from mock import patch, MagicMock
from apps.entity_ids import ID

# TODO: Put this in config (through apps.yml, check doc)
PHONE_PUSHBULLET_ID = "device/OnePlus 5T"


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

        def click_button(self, type='single'):
            {
                'single': kitchen._new_button_click,
                'double': kitchen._new_button_double_click,
                'long': kitchen._new_button_long_press
            }[type](None, None, None)

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
            kitchen._new_button_double_click,
            'click',
            entity_id=ID['kitchen']['button'],
            click_type='double')

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


SHORT_DELAY = 10
LONG_DELAY = 30


@pytest.fixture
def assert_water_heater_notif_sent(assert_that):
    def assert_water_heater_sent_wrapper(message):
        assert_that('notify/pushbullet').was.called_with(
                    title="Water Heater",
                    message=message,
                    target=PHONE_PUSHBULLET_ID)

    return assert_water_heater_sent_wrapper

@pytest.fixture
def assert_water_heater_notif_NOT_sent(assert_that):
    def assert_water_heater_NOT_sent_wrapper(message):
        assert_that('notify/pushbullet').was_not.called_with(
                    title="Water Heater",
                    message=message,
                    target=PHONE_PUSHBULLET_ID)

    return assert_water_heater_NOT_sent_wrapper


class TestSingleClickOnButton:
    def test_turn_off_water_heater(self, when_new, assert_that):
        when_new.click_button()
        assert_that(ID['bathroom']['water_heater']).was.turned_off()

    def test_send_notification(self, when_new, assert_water_heater_notif_sent):
        when_new.click_button()
        assert_water_heater_notif_sent(f"was turned off for {SHORT_DELAY} minutes")

    class TestAfterDelay:
        def test_turn_water_heater_back_on(self, when_new, time_travel, assert_that):
            when_new.click_button()
            time_travel.fast_forward(SHORT_DELAY).minutes()
            assert_that(ID['bathroom']['water_heater']).was.turned_on()

        def test_send_notification(self, when_new, time_travel, assert_water_heater_notif_sent):
            when_new.click_button()
            time_travel.fast_forward(SHORT_DELAY).minutes()
            assert_water_heater_notif_sent("was turned back on")


class TestDoubleClickOnButton:
    def test_turn_off_water_heater(self, when_new, assert_that):
        when_new.click_button(type='double')
        assert_that(ID['bathroom']['water_heater']).was.turned_off()

    def test_send_notification(self, when_new, assert_water_heater_notif_sent):
        when_new.click_button(type='double')
        assert_water_heater_notif_sent(f"was turned off for {LONG_DELAY} minutes")

    class TestAfterShortDelay:
        def test_DOES_NOT_turn_water_heater_back_on(self, when_new, time_travel, assert_that):
            when_new.click_button(type='double')
            time_travel.fast_forward(SHORT_DELAY).minutes()
            assert_that(ID['bathroom']['water_heater']).was_not.turned_on()

        def test_DOES_NOT_send_notification(self, when_new, time_travel, assert_water_heater_notif_NOT_sent):
            when_new.click_button(type='double')
            time_travel.fast_forward(SHORT_DELAY).minutes()
            assert_water_heater_notif_NOT_sent("was turned back on")

    class TestAfterLongDelay:
        def test_turn_water_heater_back_on(self, when_new, time_travel, assert_that):
            when_new.click_button(type='double')
            time_travel.fast_forward(LONG_DELAY).minutes()
            assert_that(ID['bathroom']['water_heater']).was.turned_on()

        def test_send_notification(self, when_new, time_travel, assert_water_heater_notif_sent):
            when_new.click_button(type='double')
            time_travel.fast_forward(LONG_DELAY).minutes()
            assert_water_heater_notif_sent("was turned back on")
