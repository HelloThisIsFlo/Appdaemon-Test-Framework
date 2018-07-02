import appdaemon.plugins.hass.hassapi as hass
try:
    # Module namespaces when Automation Modules are loaded in AppDaemon
    # is different from the 'real' python one.
    # Appdaemon doesn't seem to take into account packages
    from apps.entity_ids import ID
except ModuleNotFoundError:
    from entity_ids import ID

# TODO: Put this in config (through apps.yml, check doc)
PHONE_PUSHBULLET_ID = "device/OnePlus 5T"

TURNED_OFF_MSG = "Water Heater was turned OFF"
TURNED_ON_MSG = "Water Heater was turned back ON"

DELAY_IN_MINUTES_BEFORE_TURNING_BACK_ON_WATER_HEATER = 10


class Kitchen(hass.Hass):
    def initialize(self):
        self.listen_event(self._new_motion, 'motion',
                          entity_id=ID['kitchen']['motion_sensor'])
        self.listen_state(self._no_more_motion,
                          ID['kitchen']['motion_sensor'], new='off')
        self.listen_event(self._new_button_click, 'click',
                          entity_id=ID['kitchen']['button'], click_type='single')

    def _new_motion(self, _event, _data, _kwargs):
        self.turn_on(ID['kitchen']['light'])

    def _no_more_motion(self, _entity, _attribute, _old, _new, _kwargs):
        self.turn_off(ID['kitchen']['light'])

    def _new_button_click(self, _e, _d, _k):
        self.turn_off(ID['bathroom']['water_heater'])
        self.call_service('notify/pushbullet',
                          target=PHONE_PUSHBULLET_ID, message=TURNED_OFF_MSG)
        self.run_in(self._after_delay,
                    DELAY_IN_MINUTES_BEFORE_TURNING_BACK_ON_WATER_HEATER * 60)

    def _after_delay(self, **_kwargs):
        self.turn_on(ID['bathroom']['water_heater'])
        self.call_service('notify/pushbullet',
                          target=PHONE_PUSHBULLET_ID, message=TURNED_ON_MSG)
