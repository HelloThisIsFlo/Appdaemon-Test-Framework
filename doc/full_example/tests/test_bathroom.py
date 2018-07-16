from apps.bathroom import Bathroom, BATHROOM_VOLUMES, DEFAULT_VOLUMES, FAKE_MUTE_VOLUME
from appdaemon.plugins.hass.hassapi import Hass
from mock import patch, MagicMock
import pytest
from datetime import time
from apps.entity_ids import ID

MORNING_STEP1_COLOR = 'BLUE'
SHOWER_COLOR = 'GREEN'
MORNING_STEP3_COLOR = 'YELLOW'
DAY_COLOR = 'WHITE'
EVENING_COLOR = 'RED'
EVENING_HOUR = 20
DAY_HOUR = 4


@pytest.fixture
def bathroom(given_that):
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

    bathroom = Bathroom(
        None, None, None, None, None, None, None, None)
    bathroom.initialize()

    # Clear calls recorded during initialisation
    given_that.mock_functions_are_cleared()
    return bathroom


@pytest.fixture
def when_new(bathroom):
    class WhenNewWrapper:
        def time(self, hour=None):
            bathroom._time_triggered({'hour': hour})

        def motion_bathroom(self):
            bathroom._new_motion_bathroom(None, None, None)

        def motion_kitchen(self):
            bathroom._new_motion_kitchen(None, None, None)

        def motion_living_room(self):
            bathroom._new_motion_living_room(None, None, None)

        def no_more_motion_bathroom(self):
            bathroom._no_more_motion_bathroom(
                None,  None, None, None, None)

        def click_bathroom_button(self):
            bathroom._new_click_bathroom_button(None, None, None)

        def debug(self):
            bathroom.debug(None, {'click_type': 'single'}, None)
    return WhenNewWrapper()


# Start at different times
class TestInitialize:

    def test_start_during_day(self, given_that, when_new, assert_that, bathroom, assert_day_mode_started):
        given_that.time_is(time(hour=13))
        bathroom.initialize()
        assert_day_mode_started()

    def test_start_during_evening(self, given_that, when_new, assert_that, bathroom, assert_evening_mode_started):
        given_that.time_is(time(hour=20))
        bathroom.initialize()
        assert_evening_mode_started()

    def test_callbacks_are_registered(self, bathroom, hass_functions):
        # Given: The mocked callback Appdaemon registration functions
        listen_event = hass_functions['listen_event']
        listen_state = hass_functions['listen_state']
        run_daily = hass_functions['run_daily']

        # When: Calling `initialize`
        bathroom.initialize()

        # Then: callbacks are registered
        listen_event.assert_any_call(
            bathroom._new_click_bathroom_button,
            'click',
            entity_id=ID['bathroom']['button'],
            click_type='single')

        listen_event.assert_any_call(
            bathroom._new_motion_bathroom,
            'motion',
            entity_id=ID['bathroom']['motion_sensor'])
        listen_event.assert_any_call(
            bathroom._new_motion_kitchen,
            'motion',
            entity_id=ID['kitchen']['motion_sensor'])
        listen_event.assert_any_call(
            bathroom._new_motion_living_room,
            'motion',
            entity_id=ID['living_room']['motion_sensor'])
        listen_state.assert_any_call(
            bathroom._no_more_motion_bathroom,
            ID['bathroom']['motion_sensor'],
            new='off')

        run_daily.assert_any_call(
            bathroom._time_triggered,
            time(hour=DAY_HOUR),
            hour=DAY_HOUR)
        run_daily.assert_any_call(
            bathroom._time_triggered,
            time(hour=EVENING_HOUR),
            hour=EVENING_HOUR)


##################################################################################
## For the rest of the tests, Bathroom WAS STARTED DURING THE DAY (at 3PM) ##
## For the rest of the tests, Bathroom WAS STARTED DURING THE DAY (at 3PM) ##
## For the rest of the tests, Bathroom WAS STARTED DURING THE DAY (at 3PM) ##
##################################################################################

class TestDuringEvening:
    @pytest.fixture
    def start_evening_mode(self, when_new, given_that):
        given_that.mock_functions_are_cleared()
        # Provide a trigger to switch to evening mode
        return lambda: when_new.time(hour=EVENING_HOUR)

    class TestEnterBathroom:
        def test_light_turn_on(self, given_that, when_new, assert_that, start_evening_mode):
            start_evening_mode()
            when_new.motion_bathroom()
            assert_that(ID['bathroom']['led_light']
                        ).was.turned_on(color_name=EVENING_COLOR)

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
            assert_that('media_player/volume_set').was_not.called_with(
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
                assert_that(ID['bathroom']['led_light']).was.turned_off()


class TestsDuringDay:
    @pytest.fixture
    def start_day_mode(self, when_new, given_that):
        # Switch to Evening mode and provide
        # a trigger to start the Day mode

        # Switch to: Evening mode
        when_new.time(hour=EVENING_HOUR)
        given_that.mock_functions_are_cleared()

        # Trigger to switch to Day mode
        return lambda: when_new.time(hour=DAY_HOUR)

    class TestAtStart:
        def test_turn_on_water_heater(self, assert_that, start_day_mode):
            start_day_mode()
            assert_that(ID['bathroom']['water_heater']).was.turned_on()

        def test_turn_off_bathroom_light(self, assert_that, start_day_mode):
            start_day_mode()
            assert_that(ID['bathroom']['led_light']).was.turned_off()

        def test_reset_volumes(self, assert_that, start_day_mode):
            pass
            start_day_mode()
            assert_that('media_player/volume_set').was.called_with(
                entity_id=ID['bathroom']['speaker'],
                volume_level=DEFAULT_VOLUMES['bathroom'])
            assert_that('media_player/volume_set').was.called_with(
                entity_id=ID['kitchen']['speaker'],
                volume_level=DEFAULT_VOLUMES['kitchen'])
            assert_that('media_player/volume_set').was.called_with(
                entity_id=ID['living_room']['soundbar'],
                volume_level=DEFAULT_VOLUMES['living_room_soundbar'])
            assert_that('media_player/volume_set').was.called_with(
                entity_id=ID['living_room']['controller'],
                volume_level=DEFAULT_VOLUMES['living_room_controller'])

    class TestEnterBathroom:
        def test_light_turn_on(self, given_that, when_new, assert_that, start_day_mode):
            start_day_mode()
            when_new.motion_bathroom()
            assert_that(ID['bathroom']['led_light']
                        ).was.turned_on(color_name=DAY_COLOR)

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
            assert_that('media_player/volume_set').was_not.called_with(
                entity_id=ID['bathroom']['speaker'],
                volume_level=BATHROOM_VOLUMES['regular'])

    class TestLeaveBathroom:
        def test__no_more_motion__mute_turn_off_light(self, given_that, when_new, assert_that, start_day_mode):
            start_day_mode()
            when_new.no_more_motion_bathroom()
            assert_bathroom_was_muted(assert_that)
            assert_that(ID['bathroom']['led_light']).was.turned_off()

        def test__motion_anywhere_except_bathroom__do_NOT_mute_turn_off_light(self, given_that, when_new, assert_that, start_day_mode):
            scenarios = [
                when_new.motion_kitchen,
                when_new.motion_living_room
            ]
            for scenario in scenarios:
                start_day_mode()
                given_that.mock_functions_are_cleared()
                scenario()
                assert_bathroom_was_NOT_muted(assert_that)
                assert_that(ID['bathroom']['led_light']).was_not.turned_off()

    class TestSwitchToNextState:
        def test_click_activate_shower_state(self, start_day_mode, when_new, assert_shower_state_started):
            start_day_mode()
            when_new.click_bathroom_button()
            assert_shower_state_started()

        def test_8pm_activate_evening_state(self, start_day_mode, when_new, assert_evening_mode_started):
            start_day_mode()
            when_new.time(hour=EVENING_HOUR)
            assert_evening_mode_started()


class TestDuringShower:
    @pytest.fixture
    def start_shower_mode(self, when_new, given_that):
        # Provide a trigger to start shower mode
        given_that.mock_functions_are_cleared()
        return lambda: when_new.click_bathroom_button()

    class TestAtStart:
        def test_light_indicator(self, given_that, when_new, assert_that, start_shower_mode):
            start_shower_mode()
            assert_that(ID['bathroom']['led_light']).was.turned_on(
                color_name=SHOWER_COLOR)

        def test_notif_sound(self, assert_that, start_shower_mode):
            notif_sound_id = 10001
            volume = 20
            xiaomi_gateway_mac_address = ID['bathroom']['gateway_mac_address']
            start_shower_mode()
            assert_that('xiaomi_aqara/play_ringtone').was.called_with(
                ringtone_id=notif_sound_id, ringtone_vol=volume, gw_mac=xiaomi_gateway_mac_address)

        def test_mute_all_except_bathroom(self, given_that, assert_that, start_shower_mode):
            # Bug with sound bar firmware: Can only increase the volume by 10% at a time
            # to prevent this being a problem, we're not muting it
            all_speakers_except_bathroom = [
                # ID['living_room']['soundbar'],
                ID['kitchen']['speaker'],
                ID['living_room']['controller']
            ]

            start_shower_mode()
            for speaker in all_speakers_except_bathroom:
                assert_that('media_player/volume_set').was.called_with(
                    entity_id=speaker,
                    volume_level=FAKE_MUTE_VOLUME)

        def test_set_shower_volume_bathroom(self, given_that, assert_that, start_shower_mode):
            start_shower_mode()
            assert_that('media_player/volume_set').was.called_with(
                entity_id=ID['bathroom']['speaker'],
                volume_level=BATHROOM_VOLUMES['shower'])

    class TestClickButton:
        def test__activate_after_shower(self, given_that, when_new, assert_that, start_shower_mode):
            def assert_after_shower_started():
                assert_that(ID['bathroom']['led_light']).was.turned_on(
                    color_name=MORNING_STEP3_COLOR)

            start_shower_mode()
            when_new.click_bathroom_button()
            assert_after_shower_started()


class TestDuringAfterShower:
    @pytest.fixture
    def start_after_shower_mode(self, when_new, given_that):
        # Return callback to trigger AfterShower mode
        def trigger_after_shower_mode():
            when_new.click_bathroom_button()
            given_that.mock_functions_are_cleared()
            when_new.click_bathroom_button()
        return trigger_after_shower_mode

    class TestAtStart:
        def test_light_indicator(self, given_that, when_new, assert_that, start_after_shower_mode):
            start_after_shower_mode()
            assert_that(ID['bathroom']['led_light']).was.turned_on(
                color_name=MORNING_STEP3_COLOR)

        def test_notif_sound(self, assert_that, start_after_shower_mode):
            notif_sound_id = 10001
            volume = 20
            xiaomi_gateway_mac_address = ID['bathroom']['gateway_mac_address']
            start_after_shower_mode()
            assert_that('xiaomi_aqara/play_ringtone').was.called_with(
                ringtone_id=notif_sound_id, ringtone_vol=volume, gw_mac=xiaomi_gateway_mac_address)

        def test_pause_podcast(self, assert_that, start_after_shower_mode):
            start_after_shower_mode()
            for playback_device in [
                    ID['bathroom']['speaker'],
                    ID['cast_groups']['entire_flat']]:
                assert_that('media_player/media_pause').was.called_with(
                    entity_id=playback_device)

        def test_mute_bathroom(self, assert_that, start_after_shower_mode):
            start_after_shower_mode()
            assert_bathroom_was_muted(assert_that)

        def test_turn_off_water_heater(self, assert_that, start_after_shower_mode):
            start_after_shower_mode()
            assert_that(ID['bathroom']['water_heater']).was.turned_off()

    class TestMotionAnywhereExceptBathroom:
        def test_resume_podcast_playback(self, given_that, when_new, assert_that, assert_day_mode_started, start_after_shower_mode):
            scenarios = [
                when_new.motion_kitchen,
                when_new.motion_living_room,
                when_new.no_more_motion_bathroom
            ]
            for scenario in scenarios:
                # Given: In shower mode
                start_after_shower_mode()
                # When: Motion
                scenario()
                # Assert: Playback resumed
                for playback_device in [
                        ID['bathroom']['speaker'],
                        ID['cast_groups']['entire_flat']]:
                    assert_that('media_player/media_play').was.called_with(
                        entity_id=playback_device)

        def test_during_day_activate_day_mode(self, given_that, when_new, assert_that, assert_day_mode_started, start_after_shower_mode):
            scenarios = [
                when_new.motion_kitchen,
                when_new.motion_living_room,
                when_new.no_more_motion_bathroom
            ]
            for scenario in scenarios:
                given_that.time_is(time(hour=14))
                start_after_shower_mode()
                scenario()
                assert_day_mode_started()

        def test_during_evening_activate_evening_mode(self, given_that, when_new, assert_that, assert_evening_mode_started, start_after_shower_mode):
            scenarios = [
                when_new.motion_kitchen,
                when_new.motion_living_room,
                when_new.no_more_motion_bathroom
            ]
            for scenario in scenarios:
                given_that.time_is(time(hour=20))
                start_after_shower_mode()
                scenario()
                assert_evening_mode_started()

def assert_bathroom_was_muted(assert_that):
    assert_that('media_player/volume_set').was.called_with(
        entity_id=ID['bathroom']['speaker'],
        volume_level=FAKE_MUTE_VOLUME)


def assert_bathroom_was_NOT_muted(assert_that):
    assert_that('media_player/volume_set').was_not.called_with(
        entity_id=ID['bathroom']['speaker'],
        volume_level=FAKE_MUTE_VOLUME)


def assert_bathroom_was_UNmuted(assert_that):
    assert_that('media_player/volume_set').was.called_with(
        entity_id=ID['bathroom']['speaker'],
        volume_level=BATHROOM_VOLUMES['regular'])


def assert_bathroom_light_reacts_to_movement_with_color(color, when_new, assert_that):
    when_new.motion_bathroom()
    assert_that(ID['bathroom']['led_light']
                ).was.turned_on(color_name=color)


@pytest.fixture
def assert_day_mode_started(when_new, assert_that):
    return lambda: assert_bathroom_light_reacts_to_movement_with_color(
        DAY_COLOR,
        when_new,
        assert_that)


@pytest.fixture
def assert_evening_mode_started(when_new, assert_that):
    return lambda: assert_bathroom_light_reacts_to_movement_with_color(
        EVENING_COLOR,
        when_new,
        assert_that)


@pytest.fixture
def assert_shower_state_started(assert_that):
    return lambda: assert_that(ID['bathroom']['led_light']).was.turned_on(
        color_name=SHOWER_COLOR)
