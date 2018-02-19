import appdaemon.plugins.hass.hassapi as hass
try:
    # Module namespaces when Automation Modules are loaded in AppDaemon
    # is different from the 'real' python one.
    # Appdaemon doesn't seem to take into account packages
    from apps.entity_ids import ID
except ModuleNotFoundError:
    from entity_ids import ID

class WashingMachine(hass.Hass):
    def initialize(self):
        self.listen_event(
            self.loaded_and_ready_to_wash,
            'click',
            click_type='hold',
            entity_id=ID['outside']['button'])

    def loaded_and_ready_to_wash(self, _event, _data, _kwargs):
        pass
