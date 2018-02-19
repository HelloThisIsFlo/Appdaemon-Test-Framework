from apps.smart_bathroom import SmartBathroom, BATHROOM_VOLUMES, DEFAULT_VOLUMES, FAKE_MUTE_VOLUME
from appdaemon.plugins.hass.hassapi import Hass
from mock import patch, MagicMock
import pytest
from datetime import time
from apps.entity_ids import ID

"""
TODO: Add fixture to 'set_state' (will actually patch the 'get_state' method)
"""

MORNING_STEP1_COLOR = 'BLUE'
MORNING_STEP2_COLOR = 'GREEN'
MORNING_STEP3_COLOR = 'YELLOW'
DAY_COLOR = 'WHITE'
EVENING_COLOR = 'RED'
EVENING_HOUR = 20
RESET_NIGHT_HOUR = 4


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
            smart_bathroom._time_triggered({'hour': hour})

        def motion_bathroom(self):
            smart_bathroom._new_motion_bathroom(None, None, None)

        def motion_kitchen(self):
            smart_bathroom._new_motion_kitchen(None, None, None)

        def motion_living_room(self):
            smart_bathroom._new_motion_living_room(None, None, None)

        def no_more_motion_bathroom(self):
            smart_bathroom._no_more_motion_bathroom(
                None,  None, None, None, None)

        def click_bathroom_button(self):
            smart_bathroom._new_click_bathroom_button(None, None, None)

        def debug(self):
            smart_bathroom.debug(None, {'click_type': 'single'}, None)
    return WhenNewWrapper()


# Start at different times
class TestInitialize:
    def assert_bathroom_light_reacts_to_movement_with_color(self, color, when_new, assert_that):
        when_new.motion_bathroom()
        assert_that(ID['bathroom']['led_light']
                    ).was_turned_on(color_name=color)

    def test_start_during_day(self, given_that, when_new, assert_that, smart_bathroom):
        # Given: Starting during the day
        given_that.time_is(time(hour=13))

        # When: SmartBathroom is initialized
        smart_bathroom.initialize()

        # Then: Day mode is started
        self.assert_bathroom_light_reacts_to_movement_with_color(
            DAY_COLOR,
            when_new,
            assert_that)

    def test_start_during_evening(self, given_that, when_new, assert_that, smart_bathroom):
        # Given: Starting during the day
        given_that.time_is(time(hour=22))

        # When: SmartBathroom is initialized
        smart_bathroom.initialize()

        # Then: Evening mode is started
        self.assert_bathroom_light_reacts_to_movement_with_color(
            EVENING_COLOR,
            when_new,
            assert_that)

    def test_callbacks_are_registered(self, smart_bathroom, hass_functions):
        # Given: The mocked callback Appdaemon registration functions
        listen_event = hass_functions['listen_event']
        listen_state = hass_functions['listen_state']
        run_daily = hass_functions['run_daily']

        # When: Calling `initialize`
        smart_bathroom.initialize()

        # Then: callbacks are registered
        listen_event.assert_any_call(
            smart_bathroom._new_click_bathroom_button,
            'click',
            entity_id=ID['bathroom']['button'],
            click_type='single')

        listen_event.assert_any_call(
            smart_bathroom._new_motion_bathroom,
            'motion',
            entity_id=ID['bathroom']['motion_sensor'])
        listen_event.assert_any_call(
            smart_bathroom._new_motion_kitchen,
            'motion',
            entity_id=ID['kitchen']['motion_sensor'])
        listen_event.assert_any_call(
            smart_bathroom._new_motion_living_room,
            'motion',
            entity_id=ID['living_room']['motion_sensor'])
        listen_state.assert_any_call(
            smart_bathroom._no_more_motion_bathroom,
            ID['bathroom']['motion_sensor'],
            new='off')

        run_daily.assert_any_call(
            smart_bathroom._time_triggered,
            time(hour=RESET_NIGHT_HOUR),
            hour=RESET_NIGHT_HOUR)
        run_daily.assert_any_call(
            smart_bathroom._time_triggered,
            time(hour=EVENING_HOUR),
            hour=EVENING_HOUR)


##################################################################################
## For the rest of the tests, SmartBathroom WAS STARTED DURING THE DAY (at 3PM) ##
## For the rest of the tests, SmartBathroom WAS STARTED DURING THE DAY (at 3PM) ##
## For the rest of the tests, SmartBathroom WAS STARTED DURING THE DAY (at 3PM) ##
##################################################################################

class TestDuringEvening:
    @pytest.fixture
    def start_evening_mode(self, when_new, given_that):
        # Provide a trigger to switch to evening mode
        given_that.mock_functions_are_cleared()
        return lambda: when_new.time(hour=EVENING_HOUR)

    class TestEnterBathroom:
        def test_light_turn_on(self, given_that, when_new, assert_that, start_evening_mode):
            start_evening_mode()
            when_new.motion_bathroom()
            assert_that(ID['bathroom']['led_light']
                        ).was_turned_on(color_name=EVENING_COLOR)

        def test__bathroom_playing__unmute(self, given_that, when_new, assert_that, start_evening_mode):
            start_evening_mode()
            given_that.state_of(ID['bathroom']['speaker']).is_set_to('playing')
            when_new.motion_bathroom()
            assert_bathroom_was_UNmuted(assert_that)

        def test__entire_flat_playing__unmute(self, given_that, when_new, assert_that, start_evening_mode):
            start_evening_mode()
            given_that.state_of(
                ID['cast_groups']['entire_flat']).is_set_to('playing')
            when_new.motion_bathroom()
            assert_bathroom_was_UNmuted(assert_that)

        def test__nothing_playing__do_not_unmute(self, given_that, when_new, assert_that, start_evening_mode):
            start_evening_mode()
            when_new.motion_bathroom()
            assert_that('media_player/volume_set').was_NOT_called_with(
                entity_id=ID['bathroom']['speaker'],
                volume_level=BATHROOM_VOLUMES['regular'])

    class TestLeaveBathroom:
        def test_mute_turn_off_light(self, given_that, when_new, assert_that, start_evening_mode):
            scenarios = [
                when_new.motion_kitchen,
                when_new.motion_living_room,
                when_new.no_more_motion_bathroom
            ]
            for scenario in scenarios:
                given_that.mock_functions_are_cleared(clear_mock_states=True)
                start_evening_mode()
                scenario()
                assert_bathroom_was_muted(assert_that)
                assert_that(ID['bathroom']['led_light']).was_turned_off()


class TestDuringNight:
    @pytest.fixture
    def start_night_mode(self, when_new, given_that):
        # Switch to evening mode
        when_new.time(hour=EVENING_HOUR)
        given_that.mock_functions_are_cleared()
        return lambda: when_new.time(hour=RESET_NIGHT_HOUR)

    class TestMotionAnywhere:
        def test__activate_morning_step1(self, given_that, when_new, assert_that, start_night_mode):
            def assert_morning_step1_started():
                assert_that(ID['bathroom']['led_light']).was_turned_on(
                    color_name=MORNING_STEP1_COLOR)
            scenarios = [
                when_new.motion_bathroom,
                when_new.motion_kitchen,
                when_new.motion_living_room
            ]
            start_night_mode()
            for scenario in scenarios:
                scenario()
                assert_morning_step1_started()


class TestDuringMorningStep1:
    @pytest.fixture
    def start_morning_step1_mode(self, when_new, given_that):
        # Switch to morning step1_mode mode
        when_new.time(hour=EVENING_HOUR)
        when_new.time(hour=RESET_NIGHT_HOUR)
        given_that.mock_functions_are_cleared()
        return lambda: when_new.motion_bathroom()

    class TestAtStart:
        def test_light_indicator(self, given_that, when_new, assert_that, start_morning_step1_mode):
            start_morning_step1_mode()
            assert_that(ID['bathroom']['led_light']).was_turned_on(
                color_name=MORNING_STEP1_COLOR)

        def test__bathroom_playing__unmute(self, given_that, when_new, assert_that, start_morning_step1_mode):
            given_that.state_of(ID['bathroom']['speaker']).is_set_to('playing')
            start_morning_step1_mode()
            assert_bathroom_was_UNmuted(assert_that)

        def test__entire_flat_playing__unmute(self, given_that, when_new, assert_that, start_morning_step1_mode):
            given_that.state_of(
                ID['cast_groups']['entire_flat']).is_set_to('playing')
            start_morning_step1_mode()
            assert_bathroom_was_UNmuted(assert_that)

        def test__nothing_playing__do_not_unmute(self, given_that, when_new, assert_that, start_morning_step1_mode):
            start_morning_step1_mode()
            assert_that('media_player/volume_set').was_NOT_called_with(
                entity_id=ID['bathroom']['speaker'],
                volume_level=BATHROOM_VOLUMES['regular'])

    class TestEnterBathroom:
        def test__bathroom_playing__unmute(self, given_that, when_new, assert_that, start_morning_step1_mode):
            start_morning_step1_mode()
            given_that.state_of(ID['bathroom']['speaker']).is_set_to('playing')
            when_new.motion_bathroom()
            assert_bathroom_was_UNmuted(assert_that)

        def test__entire_flat_playing__unmute(self, given_that, when_new, assert_that, start_morning_step1_mode):
            start_morning_step1_mode()
            given_that.state_of(
                ID['cast_groups']['entire_flat']).is_set_to('playing')
            when_new.motion_bathroom()
            assert_bathroom_was_UNmuted(assert_that)

        def test__nothing_playing__do_not_unmute(self, given_that, when_new, assert_that, start_morning_step1_mode):
            start_morning_step1_mode()
            when_new.motion_bathroom()
            assert_that('media_player/volume_set').was_NOT_called_with(
                entity_id=ID['bathroom']['speaker'],
                volume_level=BATHROOM_VOLUMES['regular'])

    class TestLeaveBathroom:
        def test__mute_turn_off_light(self, given_that, when_new, assert_that, start_morning_step1_mode):
            scenarios = [
                when_new.motion_kitchen,
                when_new.motion_living_room,
                when_new.no_more_motion_bathroom
            ]
            for scenario in scenarios:
                given_that.mock_functions_are_cleared()
                start_morning_step1_mode()
                scenario()
                assert_bathroom_was_muted(assert_that)
                assert_that(ID['bathroom']['led_light']).was_turned_off()

    class TestClickButton:
        def test__activate_morning_step2(self, given_that, when_new, assert_that, start_morning_step1_mode):
            def assert_morning_step2_started():
                assert_that(ID['bathroom']['led_light']).was_turned_on(
                    color_name=MORNING_STEP2_COLOR)

            start_morning_step1_mode()
            when_new.click_bathroom_button()
            assert_morning_step2_started()


class TestDuringMorningStep2:
    @pytest.fixture
    def start_morning_step2_mode(self, when_new, given_that):
        # Switch to morning step2_mode mode
        when_new.time(hour=EVENING_HOUR)
        when_new.time(hour=RESET_NIGHT_HOUR)
        when_new.motion_bathroom()
        given_that.mock_functions_are_cleared()
        return lambda: when_new.click_bathroom_button()

    class TestAtStart:
        def test_light_indicator(self, given_that, when_new, assert_that, start_morning_step2_mode):
            start_morning_step2_mode()
            assert_that(ID['bathroom']['led_light']).was_turned_on(
                color_name=MORNING_STEP2_COLOR)

        def test_notif_sound(self, assert_that, start_morning_step2_mode):
            notif_sound_id = 10001
            volume = 20
            start_morning_step2_mode()
            assert_that('xiaomi_aqara/play_ringtone').was_called_with(
                ringtone_id=notif_sound_id, ringtone_vol=volume)

        def test_mute_all_except_bathroom(self, given_that, assert_that, start_morning_step2_mode):
            # Bug with sound bar firmware: Can only increase the volume by 10% at a time
            # to prevent this being a problem, we're not muting it
            all_speakers_except_bathroom = [
                # ID['living_room']['soundbar'],
                ID['kitchen']['speaker'],
                ID['living_room']['controller']
            ]

            start_morning_step2_mode()
            for speaker in all_speakers_except_bathroom:
                assert_that('media_player/volume_set').was_called_with(
                    entity_id=speaker,
                    volume_level=FAKE_MUTE_VOLUME)

        def test_set_shower_volume_bathroom(self, given_that, assert_that, start_morning_step2_mode):
            start_morning_step2_mode()
            assert_that('media_player/volume_set').was_called_with(
                entity_id=ID['bathroom']['speaker'],
                volume_level=BATHROOM_VOLUMES['shower'])

    class TestClickButton:
        def test__activate_morning_step3(self, given_that, when_new, assert_that, start_morning_step2_mode):
            def assert_morning_step3_started():
                assert_that(ID['bathroom']['led_light']).was_turned_on(
                    color_name=MORNING_STEP3_COLOR)

            start_morning_step2_mode()
            when_new.click_bathroom_button()
            assert_morning_step3_started()


class TestDuringMorningStep3:
    @pytest.fixture
    def start_morning_step3_mode(self, when_new, given_that):
        # Switch to morning step2_mode mode and return callback to trigger step3
        when_new.time(hour=EVENING_HOUR)
        when_new.time(hour=RESET_NIGHT_HOUR)
        when_new.motion_bathroom()
        when_new.click_bathroom_button()
        given_that.mock_functions_are_cleared()
        return lambda: when_new.click_bathroom_button()

    class TestAtStart:
        def test_light_indicator(self, given_that, when_new, assert_that, start_morning_step3_mode):
            start_morning_step3_mode()
            assert_that(ID['bathroom']['led_light']).was_turned_on(
                color_name=MORNING_STEP3_COLOR)

        def test_notif_sound(self, assert_that, start_morning_step3_mode):
            notif_sound_id = 10001
            volume = 20
            start_morning_step3_mode()
            assert_that('xiaomi_aqara/play_ringtone').was_called_with(
                ringtone_id=notif_sound_id, ringtone_vol=volume)

        def test_pause_podcast(self, assert_that, start_morning_step3_mode):
            start_morning_step3_mode()
            for playback_device in [
                    ID['bathroom']['speaker'],
                    ID['cast_groups']['entire_flat']]:
                assert_that('media_player/media_pause').was_called_with(
                    entity_id=playback_device)

        def test_mute_bathroom(self, assert_that, start_morning_step3_mode):
            start_morning_step3_mode()
            assert_bathroom_was_muted(assert_that)

        def test_turn_off_water_heater(self, assert_that, start_morning_step3_mode):
            start_morning_step3_mode()
            assert_that(ID['bathroom']['water_heater']).was_turned_off()

    class TestMotionAnywhereExceptBathroom:
        @pytest.fixture
        def assert_day_mode_started(self, when_new, assert_that):
            def wrapped():
                when_new.motion_bathroom()
                assert_that(ID['bathroom']['led_light']
                            ).was_turned_on(color_name=DAY_COLOR)
            return wrapped

        def test__motion_kitchen__activate_day_mode(self, when_new, assert_day_mode_started, start_morning_step3_mode):
            start_morning_step3_mode()
            when_new.motion_kitchen()
            assert_day_mode_started()

        def test__motion_living_room__activate_day_mode(self, when_new, assert_day_mode_started, start_morning_step3_mode):
            start_morning_step3_mode()
            when_new.motion_living_room()
            assert_day_mode_started()

class TestsDuringDay:
    @pytest.fixture
    def start_day_mode(self, when_new, given_that):
        # Switch to Morning Step 3 and provide 
        # a trigger to start the day mode

        # SmartBathroom is started during the day by default (see fixture)
        # Switch to: Evening mode
        when_new.time(hour=EVENING_HOUR)
        # Switch to: Night mode
        when_new.time(hour=RESET_NIGHT_HOUR)
        # Switch to: Morning Step 1
        when_new.motion_bathroom()
        # Switch to: Morning Step 2
        when_new.click_bathroom_button()
        # Switch to: Morning Step 3
        when_new.click_bathroom_button()

        given_that.mock_functions_are_cleared()
        return lambda: when_new.motion_living_room()

    class TestAtStart:
        def test_turn_on_water_heater(self, assert_that, start_day_mode):
            start_day_mode()
            assert_that(ID['bathroom']['water_heater']).was_turned_on()

        def test_turn_off_bathroom_light(self, assert_that, start_day_mode):
            start_day_mode()
            assert_that(ID['bathroom']['led_light']).was_turned_off()

        def test_resume_podcast_playback(self, assert_that, start_day_mode):
            start_day_mode()
            for playback_device in [
                    ID['bathroom']['speaker'],
                    ID['cast_groups']['entire_flat']]:
                assert_that('media_player/media_play').was_called_with(
                    entity_id=playback_device)

    class TestEnterBathroom:
        def test_light_turn_on(self, given_that, when_new, assert_that, start_day_mode):
            start_day_mode()
            when_new.motion_bathroom()
            assert_that(ID['bathroom']['led_light']
                        ).was_turned_on(color_name=DAY_COLOR)

        def test__bathroom_playing__unmute(self, given_that, when_new, assert_that, start_day_mode):
            start_day_mode()
            given_that.state_of(ID['bathroom']['speaker']).is_set_to('playing')
            when_new.motion_bathroom()
            assert_bathroom_was_UNmuted(assert_that)

        def test__entire_flat_playing__unmute(self, given_that, when_new, assert_that, start_day_mode):
            start_day_mode()
            given_that.state_of(
                ID['cast_groups']['entire_flat']).is_set_to('playing')
            when_new.motion_bathroom()
            assert_bathroom_was_UNmuted(assert_that)

        def test__nothing_playing__do_not_unmute(self, given_that, when_new, assert_that, start_day_mode):
            start_day_mode()
            when_new.motion_bathroom()
            assert_that('media_player/volume_set').was_NOT_called_with(
                entity_id=ID['bathroom']['speaker'],
                volume_level=BATHROOM_VOLUMES['regular'])

    class TestLeaveBathroom:
        def test_mute_turn_off_light(self, given_that, when_new, assert_that, start_day_mode):
            scenarios = [
                when_new.motion_kitchen,
                when_new.motion_living_room,
                when_new.no_more_motion_bathroom
            ]
            for scenario in scenarios:
                given_that.mock_functions_are_cleared()
                start_day_mode()
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
