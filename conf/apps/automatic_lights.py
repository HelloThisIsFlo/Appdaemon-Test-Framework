import appdaemon.plugins.hass.hassapi as hass
from entity_ids import ID

class KitchenLight(hass.Hass):
    def initialize(self):
        self.listen_event(self.new_motion, 'motion', entity_id=ID['kitchen']['motion_sensor'])
        self.listen_state(self.no_more_motion, ID['kitchen']['motion_sensor'], new='off')
    def new_motion(self, _event, _data, _kwargs):
        self.turn_on(ID['kitchen']['light'])
    def no_more_motion(self, _entity, _attribute, _old, _new, _kwargs):
        self.turn_off(ID['kitchen']['light'])