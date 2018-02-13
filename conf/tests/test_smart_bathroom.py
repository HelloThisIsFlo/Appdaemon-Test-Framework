from apps.smart_bathroom import SmartBathroom, BATHROOM_VOLUMES, DEFAULT_VOLUMES, FAKE_MUTE_VOLUME
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
    # Set initial state
    speakers = [
        ID['bathroom']['speaker'],
        ID['kitchen']['speaker'],
        ID['living_room']['soundbar'],
        ID['living_room']['controller'],
        ID['cast_groups']['entire_flat']
    ]
    for speaker in speakers:
        given_that.state_of(speaker).is_set_to('off')

    given_that.time_is(time(hour=15))

    smart_bathroom = SmartBathroom(
        None, None, None, None, None, None, None, None)
    smart_bathroom.initialize()

    # Clear calls recorded during initialisation
    given_that.mock_functions_are_cleared()
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

        def no_more_motion_bathroom(self):
            smart_bathroom._no_more_motion_bathroom(
                None,  None, None, None, None)

        def debug(self):
            smart_bathroom.debug(None, {'click_type': 'single'}, None)
    return WhenNewWrapper()


# Start at different times
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

# For the rest of the tests, SmartBathroom was started at 3PM

class TestsDuringDay:
    @pytest.fixture
    def _during_day(self, when_new):
        # By default SmartBathroom is started at 3PM, it'll be 
        # during the day
        pass

    class TestEnterBathroom:
        def test_light_turn_on(self, given_that, when_new, assert_that, _during_day):
            when_new.motion_bathroom()
            assert_that(ID['bathroom']['led_light']
                        ).was_turned_on(color_name='WHITE')

        def test__bathroom_playing__unmute(self, given_that, when_new, assert_that, _during_day):
            given_that.state_of(ID['bathroom']['speaker']).is_set_to('playing')
            when_new.motion_bathroom()
            assert_bathroom_was_UNmuted(assert_that)

        def test__entire_flat_playing__unmute(self, given_that, when_new, assert_that, _during_day):
            given_that.state_of(
                ID['cast_groups']['entire_flat']).is_set_to('playing')
            when_new.motion_bathroom()
            assert_bathroom_was_UNmuted(assert_that)

        def test__nothing_playing__do_not_unmute(self, given_that, when_new, assert_that, _during_day):
            when_new.motion_bathroom()
            assert_that('media_player/volume_set').was_NOT_called_with(
                entity_id=ID['bathroom']['speaker'],
                volume_level=BATHROOM_VOLUMES['regular'])
    
    class TestLeaveBathroom:
        def test_mute_turn_off_light(self, given_that, when_new, assert_that, _during_day):
            scenarios = [
                when_new.motion_kitchen,
                when_new.motion_living_room,
                when_new.no_more_motion_bathroom,
            ]
            for scenario in scenarios:
                given_that.mock_functions_are_cleared(clear_mock_states=True)
                scenario()
                assert_bathroom_was_muted(assert_that)
                assert_that(ID['bathroom']['led_light']).was_turned_off()


def assert_bathroom_was_muted(assert_that):
    assert_that('media_player/volume_set').was_called_with(
        entity_id=ID['bathroom']['speaker'],
        volume_level=FAKE_MUTE_VOLUME)


def assert_bathroom_was_UNmuted(assert_that):
    assert_that('media_player/volume_set').was_called_with(
        entity_id=ID['bathroom']['speaker'],
        volume_level=BATHROOM_VOLUMES['regular'])


@pytest.mark.skip
def tests_todo():
    raise AssertionError("""
    TESTS TO IMPLEMENT:

    test_day_music_volume_unmute
    ...
    """)
