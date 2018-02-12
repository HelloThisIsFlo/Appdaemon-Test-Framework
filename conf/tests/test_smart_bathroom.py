from apps.smart_bathroom import SmartBathroom
from appdaemon.plugins.hass.hassapi import Hass
from mock import patch, MagicMock
import pytest
from datetime import time
from apps.entity_ids import ID

"""
TODO: Add fixture to 'set_state' (will actually patch the 'get_state' method)
"""

@pytest.fixture
def smart_bathroom(given_that):
    smart_bathroom = SmartBathroom(
        None, None, None, None, None, None, None, None)
    # Set initial time to 3PM
    given_that.time_is(time(hour=15))
    smart_bathroom.initialize()
    return smart_bathroom


@pytest.fixture
def when_new(smart_bathroom):
    class WhenNewWrapper:
        def time(self, hour=None):
            smart_bathroom._time_triggered(hour=hour)
        def motion_bathroom(self):
            smart_bathroom._new_motion_bathroom(None, None, None)
        def motion_kitchen(self):
            smart_bathroom._new_motion_kitchen(None, None, None)
        def motion_living_room(self):
            smart_bathroom._new_motion_living_room(None, None, None)
        def debug(self):
            smart_bathroom.debug(None, {'click_type': 'single'}, None)
    return WhenNewWrapper()


### Start at different times
def test_automatic_lights_start_during_day(given_that, when_new, assert_that, smart_bathroom):
    given_that.time_is(time(hour=13))
    smart_bathroom.initialize()
    when_new.motion_bathroom()
    assert_that(ID['bathroom']['led_light']).was_turned_on(color_name='WHITE')

def test_automatic_lights_start_during_night(given_that, when_new, assert_that, smart_bathroom):
    given_that.time_is(time(hour=22))
    smart_bathroom.initialize()
    when_new.motion_bathroom()
    assert_that(ID['bathroom']['led_light']).was_turned_on(color_name='RED')

### For the rest of the tests, SmartBathroom was started at 3PM
def tests_todo():
    raise AssertionError("""
    TESTS TO IMPLEMENT:

    test_day_light_turn_on
    test_day_light_turn_off
    test_day_music_volume_unmute
    test_day_nothing_playing_no_mute
    test_day_music_volume_mute
    ...
    """)