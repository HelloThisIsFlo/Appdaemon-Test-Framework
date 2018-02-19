from abc import ABC, abstractmethod
import appdaemon.plugins.hass.hassapi as hass
from datetime import time
try:
    # Module namespaces when Automation Modules are loaded in AppDaemon
    # is different from the 'real' python one.
    # Appdaemon doesn't seem to take into account packages
    from apps.entity_ids import ID
except ModuleNotFoundError:
    from entity_ids import ID

FAKE_MUTE_VOLUME = 0.1
BATHROOM_VOLUMES = {
    'regular': 0.4,
    'shower': 0.7
}
DEFAULT_VOLUMES = {
    'kitchen': 0.37,
    'living_room_soundbar': 0.25,
    'living_room_controller': 0.37,
    'bathroom': FAKE_MUTE_VOLUME
}
"""
6 Behaviors:

* Night: NO LIGHT - Awaiting Wakeup - INITIAL BEHAVIOR
  - Reset volumes at startup
  - Wait for any movement to trigger Step 1
  ACTIVATE NEXT STEP: First movement anywhere

* Morning - Step 1: BLUE - First lights
  - Light always on BLUE
  - Bathroom mute / un-mute when entering & leaving bathroom. If media playing. Mute always
  ACTIVATE NEXT STEP: Button bathroom click

* Morning - Step 2: GREEN - Shower time
  - Sound notif at start
  - Light always on GREEN
  - Volume 70% Bathroom
  - Volume 0% everywhere else
  - Do not react to motion
  ACTIVATE NEXT STEP: Button bathroom click

* Morning - Step 3: YELLOW - Using Hair dryer :)
  - Sound notif at start
  - Light always on YELLOW
  - Volume 'fake mute'
  - Water heater off
  - Music / podcast paused
  ACTIVATE NEXT STEP: Movement anywhere but bathroom, or no more movement bathroom

* Day: NO LIGHT - During the Day
  - Water heater back on
  - Light on-off WHITE
  ACTIVATE NEXT STEP: Time: 9PM (for now) TODO: Activate using luminosity in living room.

* Evening: NO LIGHT - Evening
  - Bathroom mute / un-mute when entering & leaving bathroom. If media playing
  - Light on-off RED
  ACTIVATE NEXT STEP: (Going back to Night Behavior) Time: 4AM

TODO: Add logging when switching step
"""


class BathroomBehavior(ABC):
    @abstractmethod
    def new_motion_bathroom(self):
        pass

    @abstractmethod
    def new_motion_kitchen_living_room(self):
        pass

    @abstractmethod
    def no_more_motion_bathroom(self):
        pass

    @abstractmethod
    def click_on_bathroom_button(self):
        pass

    @abstractmethod
    def time_triggered(self, hour_of_day):
        pass

    @abstractmethod
    def detach_callbacks(self):
        pass


class SmartBathroom(hass.Hass):
    def initialize(self):
        self.current_behavior = EmptyBehavior()
        self._start_initial_behavior()

        # Listen to Time
        self.run_daily(self._time_triggered, time(hour=4), hour=4)
        self.run_daily(self._time_triggered, time(hour=20), hour=20)

        # Listen to Motion
        self.listen_event(self._new_motion_bathroom, 'motion',
                          entity_id=ID['bathroom']['motion_sensor'])
        self.listen_event(self._new_motion_kitchen, 'motion',
                          entity_id=ID['kitchen']['motion_sensor'])
        self.listen_event(self._new_motion_living_room, 'motion',
                          entity_id=ID['living_room']['motion_sensor'])
        self.listen_state(self._no_more_motion_bathroom,
                          ID['bathroom']['motion_sensor'], new='off')
        
        # Listen to button click
        self.listen_event(self._new_click_bathroom_button, 'click',
                          entity_id=ID['bathroom']['button'],
                          click_type='single')

        # Debug remove
        self.listen_event(self.debug, 'flic_click',
                          entity_id=ID['debug']['flic_black'])

    def debug(self, _e, data, _k):
        if data['click_type'] == 'single':
            self.call_service('xiaomi_aqara/play_ringtone',
                              ringtone_id=10001, ringtone_vol=20)
            # self.pause_media_entire_flat()
            # self.turn_on_bathroom_light('blue')
        elif data['click_type'] == 'double':
            pass

    def _time_triggered(self, kwargs):
        self.current_behavior.time_triggered(kwargs['hour'])

    def _new_motion_bathroom(self, _e, _d, _k):
        self.current_behavior.new_motion_bathroom()

    def _new_motion_kitchen(self, _e, _d, _k):
        self.current_behavior.new_motion_kitchen_living_room()

    def _new_motion_living_room(self, _e, _d, _k):
        self.current_behavior.new_motion_kitchen_living_room()

    def _no_more_motion_bathroom(self, _e, _a, _o, _n, _k):
        self.current_behavior.no_more_motion_bathroom()
    
    def _new_click_bathroom_button(self, _e, _d, _k):
        pass

    """
    Start the different Behaviors
    """

    def _start_initial_behavior(self):
        current_hour = self.time().hour
        if current_hour < 4 or current_hour > 21:
            self._start_evening_behavior()
        else:
            self._start_day_behavior()

    def _start_night_behavior(self):
        self.log("Starting Night Behavior")
        self.current_behavior.detach_callbacks()
        self.current_behavior = NightBehavior(
            self.turn_off_bathroom_light,
            self.reset_all_volumes,
            self._start_morning_step1_behavior)

    def _start_morning_step1_behavior(self):
        self.log("Starting Morning Step1 Behavior")
        self.current_behavior.detach_callbacks()
        self.current_behavior = MorningStep1Behavior(
            self.mute_bathroom,
            self.unmute_bathroom,
            self.is_media_casting_bathroom,
            self.turn_on_bathroom_light,
            self.turn_off_bathroom_light,
            self._start_morning_step2_behavior)

    def _start_morning_step2_behavior(self):
        self.log("Starting Morning Step2 Behavior")
        self.current_behavior.detach_callbacks()
        self.current_behavior = MorningStep2Behavior(
            self.set_shower_volume_bathroom,
            self.mute_all_except_bathroom,
            self.turn_on_bathroom_light,
            self.play_notification_sound,
            self._start_morning_step3_behavior)

    def _start_morning_step3_behavior(self):
        self.log("Starting Morning Step3 Behavior")
        self.current_behavior.detach_callbacks()
        self.current_behavior = MorningStep3Behavior(
            self.mute_bathroom,
            self.turn_off_water_heater,
            self.pause_media_playback_entire_flat,
            self.turn_on_bathroom_light,
            self.play_notification_sound,
            self._start_day_behavior)

    def _start_day_behavior(self):
        self.log("Starting Day Behavior")
        self.current_behavior.detach_callbacks()
        self.current_behavior = DayBehavior(
            self.turn_on_bathroom_light,
            self.turn_off_bathroom_light,
            self.resume_media_playback_entire_flat,
            self.mute_bathroom,
            self.unmute_bathroom,
            self.is_media_casting_bathroom,
            self.turn_on_water_heater,
            self._start_evening_behavior)

    def _start_evening_behavior(self):
        self.log("Starting Evening Behavior")
        self.current_behavior.detach_callbacks()
        self.current_behavior = EveningBehavior(
            self.turn_on_bathroom_light,
            self.turn_off_bathroom_light,
            self.mute_bathroom,
            self.unmute_bathroom,
            self.is_media_casting_bathroom,
            self._start_night_behavior)

    """
    Utility / Callback functions
    """

    def reset_all_volumes(self):
        self._set_volume(ID['kitchen']['speaker'], DEFAULT_VOLUMES['kitchen'])
        self._set_volume(ID['bathroom']['speaker'],
                         DEFAULT_VOLUMES['bathroom'])
        self._set_volume(ID['living_room']['soundbar'],
                         DEFAULT_VOLUMES['living_room_soundbar'])
        self._set_volume(ID['living_room']['controller'],
                         DEFAULT_VOLUMES['living_room_controller'])

    def mute_all_except_bathroom(self):
        # Bug with sound bar firmware: Can only increase the volume by 10% at a time
        # to prevent this being a problem, we're not muting it
        # self._set_volume(ID['living_room']['soundbar'], FAKE_MUTE_VOLUME)
        self._set_volume(ID['living_room']['controller'], FAKE_MUTE_VOLUME)
        self._set_volume(ID['kitchen']['speaker'], FAKE_MUTE_VOLUME)

    def mute_bathroom(self):
        self._set_volume(ID['bathroom']['speaker'], FAKE_MUTE_VOLUME)

    def unmute_bathroom(self):
        self._set_volume(ID['bathroom']['speaker'],
                         BATHROOM_VOLUMES['regular'])

    def set_shower_volume_bathroom(self):
        self._set_volume(ID['bathroom']['speaker'], BATHROOM_VOLUMES['shower'])

    def is_media_casting_bathroom(self):
        return (self._is_media_casting(ID['bathroom']['speaker'])
                or self._is_media_casting(ID['cast_groups']['entire_flat']))

    def pause_media_playback_entire_flat(self):
        self._pause_media(ID['bathroom']['speaker'])
        self._pause_media(ID['cast_groups']['entire_flat'])

    def resume_media_playback_entire_flat(self):
        self._play_media(ID['bathroom']['speaker'])
        self._play_media(ID['cast_groups']['entire_flat'])

    def turn_on_bathroom_light(self, color_name):
        self.turn_on(ID['bathroom']['led_light'], color_name=color_name)

    def turn_off_bathroom_light(self):
        self.turn_off(ID['bathroom']['led_light'])

    def turn_off_water_heater(self):
        self.turn_off(ID['bathroom']['water_heater'])

    def turn_on_water_heater(self):
        self.turn_on(ID['bathroom']['water_heater'])

    def play_notification_sound(self):
        self.call_service('xiaomi_aqara/play_ringtone',
                          ringtone_id=10001, ringtone_vol=20)

    def _set_volume(self, entity_id, volume):
        self.call_service('media_player/volume_set',
                          entity_id=entity_id,
                          volume_level=volume)

    def _is_media_casting(self, media_player_id):
        return self.get_state(media_player_id) != 'off'

    def _pause_media(self, entity_id):
        self.call_service('media_player/media_pause',
                          entity_id=entity_id)

    def _play_media(self, entity_id):
        self.call_service('media_player/media_play',
                          entity_id=entity_id)


"""
Behavior Implementations
"""


class EmptyBehavior(BathroomBehavior):
    def new_motion_bathroom(self):
        pass

    def new_motion_kitchen_living_room(self):
        pass

    def no_more_motion_bathroom(self):
        pass

    def click_on_bathroom_button(self):
        pass

    def time_triggered(self, hour_of_day):
        pass

    def detach_callbacks(self):
        pass


class NightBehavior(BathroomBehavior):
    def __init__(self,
                 turn_off_bathroom_light_cb,
                 reset_all_volumes_cb,
                 start_morning_step1_behavior_cb):
        self.turn_off_bathroom_light_cb = turn_off_bathroom_light_cb
        self.reset_all_volumes_cb = reset_all_volumes_cb
        self.start_morning_step1_behavior_cb = start_morning_step1_behavior_cb

        # Initial state
        self.reset_all_volumes_cb()
        self.turn_off_bathroom_light_cb()

    def detach_callbacks(self):
        self.turn_off_bathroom_light_cb = None
        self.reset_all_volumes_cb = None
        self.start_morning_step1_behavior_cb = None

    def new_motion_bathroom(self):
        self.start_morning_step1_behavior_cb()

    def new_motion_kitchen_living_room(self):
        self.start_morning_step1_behavior_cb()

    def no_more_motion_bathroom(self):
        pass

    def click_on_bathroom_button(self):
        pass

    def time_triggered(self, hour_of_day):
        pass


class MorningStep1Behavior(BathroomBehavior):
    def __init__(self,
                 mute_bathroom_cb,
                 unmute_bathroom_cb,
                 is_media_casting_bathroom_cb,
                 turn_on_bathroom_light_cb,
                 turn_off_bathroom_light_cb,
                 start_morning_step2_behavior_cb):
        # Callbacks
        self.mute_bathroom_cb = mute_bathroom_cb
        self.unmute_bathroom_cb = unmute_bathroom_cb
        self.is_media_casting_bathroom_cb = is_media_casting_bathroom_cb
        self.turn_on_bathroom_light_cb = turn_on_bathroom_light_cb
        self.turn_off_bathroom_light_cb = turn_off_bathroom_light_cb
        self.start_morning_step2_behavior_cb = start_morning_step2_behavior_cb

        # Initial state
        self.turn_on_bathroom_light_cb('BLUE')
        if self.is_media_casting_bathroom_cb():
            self.unmute_bathroom_cb()

    def detach_callbacks(self):
        self.mute_bathroom_cb = None
        self.unmute_bathroom_cb = None
        self.is_media_casting_bathroom_cb = None
        self.turn_on_bathroom_light_cb = None
        self.turn_off_bathroom_light_cb = None
        self.start_morning_step2_behavior_cb = None

    def new_motion_bathroom(self):
        if self.is_media_casting_bathroom_cb():
            self.unmute_bathroom_cb()

    def new_motion_kitchen_living_room(self):
        self.mute_bathroom_cb()
        self.turn_off_bathroom_light_cb()

    def no_more_motion_bathroom(self):
        self.mute_bathroom_cb()
        self.turn_off_bathroom_light_cb()

    def click_on_bathroom_button(self):
        self.start_morning_step2_behavior_cb()

    def time_triggered(self, hour_of_day):
        pass


class MorningStep2Behavior(BathroomBehavior):
    def __init__(self,
                 set_shower_volume_bathroom_cb,
                 mute_all_except_bathroom_cb,
                 turn_on_bathroom_light_cb,
                 play_notification_sound_cb,
                 start_morning_step3_behavior_cb):
        self.set_shower_volume_bathroom_cb = set_shower_volume_bathroom_cb
        self.mute_all_except_bathroom_cb = mute_all_except_bathroom_cb
        self.turn_on_bathroom_light_cb = turn_on_bathroom_light_cb
        self.play_notification_sound_cb = play_notification_sound_cb
        self.start_morning_step3_behavior_cb = start_morning_step3_behavior_cb

        # Initial state
        self.play_notification_sound_cb()
        self.turn_on_bathroom_light_cb('GREEN')
        self.set_shower_volume_bathroom_cb()
        self.mute_all_except_bathroom_cb()

    def detach_callbacks(self):
        self.set_shower_volume_bathroom_cb = None
        self.mute_all_except_bathroom_cb = None
        self.turn_on_bathroom_light_cb = None
        self.play_notification_sound_cb = None
        self.start_morning_step3_behavior_cb = None

    def click_on_bathroom_button(self):
        self.start_morning_step3_behavior_cb()

    def new_motion_bathroom(self):
        pass

    def new_motion_kitchen_living_room(self):
        pass

    def no_more_motion_bathroom(self):
        pass

    def time_triggered(self, hour_of_day):
        pass


class MorningStep3Behavior(BathroomBehavior):
    def __init__(self,
                 mute_bathroom_cb,
                 turn_off_water_heater_cb,
                 pause_media_cb,
                 turn_on_bathroom_light_cb,
                 play_notification_sound_cb,
                 start_day_behavior_cb):
        self.mute_bathroom_cb = mute_bathroom_cb
        self.turn_off_water_heater_cb = turn_off_water_heater_cb
        self.pause_media_cb = pause_media_cb
        self.turn_on_bathroom_light_cb = turn_on_bathroom_light_cb
        self.play_notification_sound_cb = play_notification_sound_cb
        self.start_day_behavior_cb = start_day_behavior_cb

        # Initial state
        self.play_notification_sound_cb()
        self.turn_on_bathroom_light_cb('YELLOW')
        self.pause_media_cb()
        self.mute_bathroom_cb()
        self.turn_off_water_heater_cb()

    def detach_callbacks(self):
        self.mute_bathroom_cb = None
        self.turn_off_water_heater_cb = None
        self.pause_media_cb = None
        self.turn_on_bathroom_light_cb = None
        self.play_notification_sound_cb = None
        self.start_day_behavior_cb = None

    def new_motion_kitchen_living_room(self):
        self.start_day_behavior_cb()

    def no_more_motion_bathroom(self):
        self.start_day_behavior_cb()

    def new_motion_bathroom(self):
        pass

    def click_on_bathroom_button(self):
        pass

    def time_triggered(self, hour_of_day):
        pass


class DayBehavior(BathroomBehavior):
    def __init__(self,
                 turn_on_bathroom_light_cb,
                 turn_off_bathroom_light_cb,
                 resume_media_playback_cb,
                 mute_bathroom_cb,
                 unmute_bathroom_cb,
                 is_media_casting_bathroom_cb,
                 turn_on_water_heater_cb,
                 start_evening_behavior_cb):
        self.turn_on_bathroom_light_cb = turn_on_bathroom_light_cb
        self.turn_off_bathroom_light_cb = turn_off_bathroom_light_cb
        self.resume_media_playback_cb = resume_media_playback_cb
        self.mute_bathroom_cb = mute_bathroom_cb
        self.unmute_bathroom_cb = unmute_bathroom_cb
        self.is_media_casting_bathroom_cb = is_media_casting_bathroom_cb
        self.turn_on_water_heater_cb = turn_on_water_heater_cb
        self.start_evening_behavior_cb = start_evening_behavior_cb

        # Initial state
        self.turn_on_water_heater_cb()
        self.turn_off_bathroom_light_cb()
        self.mute_bathroom_cb()
        self.resume_media_playback_cb()

    def detach_callbacks(self):
        self.turn_on_bathroom_light_cb = None
        self.turn_off_bathroom_light_cb = None
        self.resume_media_playback_cb = None
        self.mute_bathroom_cb = None
        self.unmute_bathroom_cb = None
        self.is_media_casting_bathroom_cb = None
        self.turn_on_water_heater_cb = None
        self.start_evening_behavior_cb = None

    def new_motion_bathroom(self):
        self.turn_on_bathroom_light_cb('WHITE')
        if self.is_media_casting_bathroom_cb():
            self.unmute_bathroom_cb()

    def new_motion_kitchen_living_room(self):
        self.turn_off_bathroom_light_cb()
        self.mute_bathroom_cb()

    def no_more_motion_bathroom(self):
        self.turn_off_bathroom_light_cb()
        self.mute_bathroom_cb()

    def time_triggered(self, hour_of_day):
        if hour_of_day == 20:
            self.start_evening_behavior_cb()

    def click_on_bathroom_button(self):
        pass


class EveningBehavior(BathroomBehavior):
    def __init__(self,
                 turn_on_bathroom_light_cb,
                 turn_off_bathroom_light_cb,
                 mute_bathroom_cb,
                 unmute_bathroom_cb,
                 is_media_casting_bathroom_cb,
                 start_night_behavior_cb):
        self.turn_on_bathroom_light_cb = turn_on_bathroom_light_cb
        self.turn_off_bathroom_light_cb = turn_off_bathroom_light_cb
        self.mute_bathroom_cb = mute_bathroom_cb
        self.unmute_bathroom_cb = unmute_bathroom_cb
        self.is_media_casting_bathroom_cb = is_media_casting_bathroom_cb
        self.start_night_behavior_cb = start_night_behavior_cb

    def detach_callbacks(self):
        self.turn_on_bathroom_light_cb = None
        self.turn_off_bathroom_light_cb = None
        self.mute_bathroom_cb = None
        self.unmute_bathroom_cb = None
        self.is_media_casting_bathroom_cb = None
        self.start_night_behavior_cb = None

    def new_motion_bathroom(self):
        self.turn_on_bathroom_light_cb('RED')
        if self.is_media_casting_bathroom_cb():
            self.unmute_bathroom_cb()

    def new_motion_kitchen_living_room(self):
        self.turn_off_bathroom_light_cb()
        self.mute_bathroom_cb()

    def no_more_motion_bathroom(self):
        self.turn_off_bathroom_light_cb()
        self.mute_bathroom_cb()

    def time_triggered(self, hour_of_day):
        if hour_of_day == 4:
            self.start_night_behavior_cb()

    def click_on_bathroom_button(self):
        pass
