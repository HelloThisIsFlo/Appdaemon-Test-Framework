import appdaemon.plugins.hass.hassapi as hass
from datetime import time
from entity_ids import ID

BATHROOM_VOLUMES = {
    'fake_mute': 0.1,
    'regular': 0.4,
    'shower': 0.7
}

DEFAULT_VOLUMES = {
    'kitchen': 0.37,
    'living_room_soundbar': 0.25,
    'living_room_controller': 0.37,
    'bathroom': BATHROOM_VOLUMES['fake_mute']
}

class SmartBathroom(hass.Hass):
    def initialize(self):
        # Reset state
        # self.reset_all_volumes_at_4am([])

        # Schedule call at 4AM
        self.run_daily(self.reset_all_volumes_at_4am, time(hour=4))

        # Listen to Motion
        self.listen_event(self.new_motion_bathroom, 'motion', entity_id=ID['bathroom']['motion_sensor'])
        self.listen_event(self.new_motion_kitchen, 'motion', entity_id=ID['kitchen']['motion_sensor'])
        self.listen_event(self.new_motion_living_room, 'motion', entity_id=ID['living_room']['motion_sensor'])
        self.listen_state(self.no_more_motion_bathroom, ID['bathroom']['motion_sensor'], new='off')

        self.some_variable = 0

        self.listen_event(
            self.debug,
            'flic_click',
            entity_id=ID['debug']['flic_black'])
        
    def debug(self, _e, data, _k):
        if data['click_type'] == 'single':
            self.call_service(
                'xiaomi_aqara/play_ringtone',
                ringtone_id=10001,
                ringtone_vol=20)


            self.some_variable += 1
            self.log(self.some_variable)
            self.reset_all_volumes_at_4am([])
            # pass
        elif data['click_type'] == 'double':
            self._decrease_volume_bathroom()


    def reset_all_volumes_at_4am(self, _kwargs):
        self.log("It's 4AM, resetting all the volumes")
        self._set_volume(ID['kitchen']['speaker'], DEFAULT_VOLUMES['kitchen'])
        self._set_volume(ID['bathroom']['speaker'], DEFAULT_VOLUMES['bathroom'])
        self._set_volume(ID['living_room']['soundbar'], DEFAULT_VOLUMES['living_room_soundbar'])
        self._set_volume(ID['living_room']['controller'], DEFAULT_VOLUMES['living_room_controller'])


    def new_motion_bathroom(self, _e, _d, _k):
        if self._media_casting_in_bathroom():
            self._increase_volume_bathroom()
    def no_more_motion_bathroom(self, _e, _a, _o, _n, _k):
        self._decrease_volume_bathroom()
    def new_motion_kitchen(self, _e, _d, _k):
        self._decrease_volume_bathroom()
    def new_motion_living_room(self, _e, _d, _k):
        self._decrease_volume_bathroom()


    def _increase_volume_bathroom(self):
        self._set_volume(ID['bathroom']['speaker'], BATHROOM_VOLUMES['regular'])
    def _decrease_volume_bathroom(self):
        self._set_volume(ID['bathroom']['speaker'], BATHROOM_VOLUMES['fake_mute'])
    def _media_casting_in_bathroom(self):
        return (self._media_casting(ID['bathroom']['speaker'])
                or self._media_casting(ID['cast_groups']['entire_flat']))
    def _media_casting(self, media_player_id):
        return self.get_state(media_player_id) != 'off'

    def _set_volume(self, entity_id, volume):
        self.call_service(
            'media_player/volume_set',
            entity_id=entity_id,
            volume_level=volume)