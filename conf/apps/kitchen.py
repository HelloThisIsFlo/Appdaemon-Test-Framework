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
SHORT_DELAY = 10
LONG_DELAY = 10

MSG_TITLE = "Water Heater"
MSG_SHORT_OFF = f"was turned off for {SHORT_DELAY} minutes"
MSG_LONG_OFF =  f"was turned off for {LONG_DELAY} minutes"
MSG_ON = "was turned back on"

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
                          target=PHONE_PUSHBULLET_ID, 
                          title=MSG_TITLE,
                          message=MSG_SHORT_OFF)
        self.run_in(self._after_delay, SHORT_DELAY * 60)

    def _after_delay(self, _kwargs):
        self.turn_on(ID['bathroom']['water_heater'])
        self.call_service('notify/pushbullet',
                          target=PHONE_PUSHBULLET_ID,
                          title=MSG_TITLE,
                          message=MSG_ON)
