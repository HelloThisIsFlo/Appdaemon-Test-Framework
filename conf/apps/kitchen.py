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
LONG_DELAY = 30

MSG_TITLE = "Water Heater"
MSG_SHORT_OFF = f"was turned off for {SHORT_DELAY} minutes"
MSG_LONG_OFF = f"was turned off for {LONG_DELAY} minutes"
MSG_ON = "was turned back on"


class Kitchen(hass.Hass):
    def initialize(self):
        self.listen_event(self._new_motion, 'motion',
                          entity_id=ID['kitchen']['motion_sensor'])
        self.listen_state(self._no_more_motion,
                          ID['kitchen']['motion_sensor'], new='off')
        self.listen_event(self._new_button_click, 'click',
                          entity_id=ID['kitchen']['button'], click_type='single')
        self.listen_event(self._new_button_double_click, 'click',
                          entity_id=ID['kitchen']['button'], click_type='double')

        self.clicked_X_times = 0

    def _new_motion(self, _event, _data, _kwargs):
        self.turn_on(ID['kitchen']['light'])

    def _no_more_motion(self, _entity, _attribute, _old, _new, _kwargs):
        self.turn_off(ID['kitchen']['light'])

    def _new_button_click(self, _e, _d, _k):
        self.clicked_X_times += 1
        self._turn_off_water_heater_for_X_minutes(SHORT_DELAY)
        self._send_water_heater_notification(MSG_SHORT_OFF)

    def _new_button_double_click(self, _e, _d, _k):
        self.clicked_X_times += 1
        self._turn_off_water_heater_for_X_minutes(LONG_DELAY)
        self._send_water_heater_notification(MSG_LONG_OFF)

    def _new_button_long_press(self, _e, _d, _k):
        pass

    def _turn_off_water_heater_for_X_minutes(self, minutes):
        self.turn_off(ID['bathroom']['water_heater'])
        self.run_in(self._after_delay, minutes * 60)

    def _send_water_heater_notification(self, message):
        self.call_service('notify/pushbullet',
                          target=PHONE_PUSHBULLET_ID,
                          title=MSG_TITLE,
                          message=message)

    def _after_delay(self, _kwargs):
        if self.clicked_X_times > 1:
            self.clicked_X_times -= 1
        else:
            self.turn_on(ID['bathroom']['water_heater'])
            self._send_water_heater_notification(MSG_ON)
