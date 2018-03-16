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
    'living_room_controller': 0.52,
    'bathroom': FAKE_MUTE_VOLUME
}
"""
4 Behaviors as States of a State Machine:

* Day: The normal mode
* Evening: Same as Day. Using red light instead.
* Shower: Volume up, it's shower time!
* AfterShower: Turn off all devices while using the HairDryer


Detail of each State:

* Day: Normal mode - Activated at 4AM by EveningState
  - Light on-off WHITE
  - Bathroom mute / un-mute when entering & leaving bathroom. If media playing
  - Water heater back on
  ACTIVATE NEXT STEP:
   - 8PM => EveningState
     - TODO: Will use luminosity instead of time in the future
   - Click => ShowerState

* Evening: Evening Mode
  - Light on-off RED
  - Bathroom mute / un-mute when entering & leaving bathroom. If media playing
  ACTIVATE NEXT STEP:
   - 4AM => DayState
   - Click => ShowerState

* Shower: GREEN - Shower time
  - Sound notif at start
  - Light always on GREEN
  - Volume 70% Bathroom
  - Volume 0% everywhere else
  - Do not react to motion
  ACTIVATE NEXT STEP:
   - Click => AfterShower

* AfterShower: YELLOW - Using Hair dryer :)
  - Sound notif at start
  - Light always on YELLOW
  - Volume 'fake mute'
  - Water heater off
  - Music / podcast paused
  ACTIVATE NEXT STEP:
   - MABB & Time  in [8PM, 4AM[ => EveningState
   - MABB & Time out [8PM, 4AM[ => DayState
"""


class BathroomBehavior:
    def start(self):
        pass

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


class SmartBathroom(hass.Hass):
    def initialize(self):
        self.behaviors = None
        self._initialize_behaviors()

        self.current_behavior = None
        self.start_initial_behavior()

        self._register_time_callbacks()
        self._register_motion_callbacks()
        self._register_button_click_callback()

        self._register_debug_callback()

    def _initialize_behaviors(self):
        self.behaviors = {
            'day': DayBehavior(self),
            'evening': EveningBehavior(self),
            'shower': ShowerBehavior(self),
            'after_shower': AfterShowerBehavior(self)
        }

    def start_initial_behavior(self):
        current_hour = self.time().hour
        if current_hour < 4 or current_hour >= 20:
            self.start_behavior('evening')
        else:
            self.start_behavior('day')

    def _register_time_callbacks(self):
        self.run_daily(self._time_triggered, time(hour=4), hour=4)
        self.run_daily(self._time_triggered, time(hour=20), hour=20)

    def _register_motion_callbacks(self):
        self.listen_event(self._new_motion_bathroom, 'motion',
                          entity_id=ID['bathroom']['motion_sensor'])
        self.listen_event(self._new_motion_kitchen, 'motion',
                          entity_id=ID['kitchen']['motion_sensor'])
        self.listen_event(self._new_motion_living_room, 'motion',
                          entity_id=ID['living_room']['motion_sensor'])
        self.listen_state(self._no_more_motion_bathroom,
                          ID['bathroom']['motion_sensor'], new='off')

    def _register_button_click_callback(self):
        self.listen_event(self._new_click_bathroom_button, 'click',
                          entity_id=ID['bathroom']['button'],
                          click_type='single')

    def _register_debug_callback(self):
        def _debug(self, _e, data, _k):
            if data['click_type'] == 'single':
                self.call_service('xiaomi_aqara/play_ringtone',
                                  ringtone_id=10001, ringtone_vol=20)
                # self.pause_media_entire_flat()
                # self.turn_on_bathroom_light('blue')
            elif data['click_type'] == 'double':
                pass

        self.listen_event(_debug, 'flic_click',
                          entity_id=ID['debug']['flic_black'])

    """
    Callbacks
    """

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
        self.current_behavior.click_on_bathroom_button()

    """
    SmartBathroom Services
    """

    def start_behavior(self, behavior):
        self.log("Starting Behavior: " + behavior)
        self.current_behavior = self.behaviors[behavior]
        self.current_behavior.start()

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
                          ringtone_id=10001, ringtone_vol=20, gw_mac=ID['bathroom']['gateway_mac_address'])

    """
    Private functions
    """

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


class ShowerBehavior(BathroomBehavior):
    def __init__(self, smart_bathroom):
        self.smart_bathroom = smart_bathroom

    def start(self):
        self.smart_bathroom.play_notification_sound()
        self.smart_bathroom.turn_on_bathroom_light('GREEN')
        self.smart_bathroom.set_shower_volume_bathroom()
        self.smart_bathroom.mute_all_except_bathroom()

    def click_on_bathroom_button(self):
        self.smart_bathroom.start_behavior('after_shower')


class AfterShowerBehavior(BathroomBehavior):
    def __init__(self, smart_bathroom):
        self.smart_bathroom = smart_bathroom

    def start(self):
        self.smart_bathroom.play_notification_sound()
        self.smart_bathroom.turn_on_bathroom_light('YELLOW')
        self.smart_bathroom.pause_media_playback_entire_flat()
        self.smart_bathroom.mute_bathroom()
        self.smart_bathroom.turn_off_water_heater()

    def new_motion_kitchen_living_room(self):
        self._activate_next_state()

    def no_more_motion_bathroom(self):
        self._activate_next_state()

    def _activate_next_state(self):
        self.smart_bathroom.resume_media_playback_entire_flat()
        self.smart_bathroom.start_initial_behavior()



class DayBehavior(BathroomBehavior):
    def __init__(self, smart_bathroom):
        self.smart_bathroom = smart_bathroom

    def start(self):
        self.smart_bathroom.turn_on_water_heater()
        self.smart_bathroom.turn_off_bathroom_light()
        self.smart_bathroom.reset_all_volumes()

    def new_motion_bathroom(self):
        self.smart_bathroom.turn_on_bathroom_light('WHITE')
        if self.smart_bathroom.is_media_casting_bathroom():
            self.smart_bathroom.unmute_bathroom()

    def no_more_motion_bathroom(self):
        self.smart_bathroom.turn_off_bathroom_light()
        self.smart_bathroom.mute_bathroom()

    def time_triggered(self, hour_of_day):
        if hour_of_day == 20:
            self.smart_bathroom.start_behavior('evening')

    def click_on_bathroom_button(self):
        self.smart_bathroom.start_behavior('shower')


class EveningBehavior(BathroomBehavior):
    def __init__(self, smart_bathroom):
        self.smart_bathroom = smart_bathroom

    def new_motion_bathroom(self):
        self.smart_bathroom.turn_on_bathroom_light('RED')
        if self.smart_bathroom.is_media_casting_bathroom():
            self.smart_bathroom.unmute_bathroom()

    def new_motion_kitchen_living_room(self):
        self.smart_bathroom.turn_off_bathroom_light()
        self.smart_bathroom.mute_bathroom()

    def no_more_motion_bathroom(self):
        self.smart_bathroom.turn_off_bathroom_light()
        self.smart_bathroom.mute_bathroom()

    def time_triggered(self, hour_of_day):
        if hour_of_day == 4:
            self.smart_bathroom.start_behavior('day')
