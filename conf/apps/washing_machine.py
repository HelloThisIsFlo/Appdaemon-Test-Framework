import appdaemon.plugins.hass.hassapi as hass
from apps.entity_ids import ID

class WashingMachine(hass.Hass):
    def initialize(self):
        self.listen_event(
            self.loaded_and_ready_to_wash,
            'click',
            click_type='hold',
            entity_id=ID['outside']['button'])

    def loaded_and_ready_to_wash(self, _event, _data, _kwargs):
        pass
