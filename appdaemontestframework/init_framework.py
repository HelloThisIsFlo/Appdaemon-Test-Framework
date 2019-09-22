import logging

import mock
from appdaemon.plugins.hass.hassapi import Hass

class MockHandler:
    def __init__(self, object_to_patch, function_name, side_effect=None):
        self.function_name = function_name
        self.patch = mock.patch.object(object_to_patch, self.function_name, create=True)
        self.mock = self.patch.start()
        self.mock.return_value = None
        self.mock.side_effect = side_effect


class HassMock:
    def __init__(self):
        self._mock_handlers = [
            # Meta
            MockHandler(Hass, '__init__'),  # Patch the __init__ method to skip Hass initialization

            # Logging
            MockHandler(Hass, 'log'),
            MockHandler(Hass, 'error'),

            # Scheduler callback registrations functions
            MockHandler(Hass, 'run_in'),
            MockHandler(Hass, 'run_once'),
            MockHandler(Hass, 'run_at'),
            MockHandler(Hass, 'run_daily'),
            MockHandler(Hass, 'run_hourly'),
            MockHandler(Hass, 'run_minutely'),
            MockHandler(Hass, 'run_every'),
            MockHandler(Hass, 'cancel_timer'),

            # Sunrise and sunset functions
            MockHandler(Hass, 'run_at_sunrise'),
            MockHandler(Hass, 'run_at_sunset'),

            # Listener callback registrations functions
            MockHandler(Hass, 'listen_event'),
            MockHandler(Hass, 'listen_state'),

            # State functions / attr
            MockHandler(Hass, 'set_state'),
            MockHandler(Hass, 'get_state'),
            MockHandler(Hass, 'time'),
            MockHandler(Hass, 'args'),  # Not a function, attribute. But same patching logic

            # Interactions functions
            MockHandler(Hass, 'call_service'),
            MockHandler(Hass, 'turn_on'),
            MockHandler(Hass, 'turn_off'),

            # Custom callback functions
            MockHandler(Hass, 'register_constraint'),
            MockHandler(Hass, 'now_is_between'),
            MockHandler(Hass, 'notify'),

            # logging
            MockHandler(Hass, 'log', side_effect=self._log_log),
            MockHandler(Hass, 'error', side_effect=self._log_error),
        ]

        # TODO: remove this temp convert the new _mocks into the old _hass_functions
        self._hass_functions = {}
        for mock_handler in self._mock_handlers:
            self._hass_functions[mock_handler.function_name] = mock_handler.mock
        # ensure compatibility with older versions of AppDaemon
        self._hass_functions['passed_args'] = self._hass_functions['args']

    def unpatch_mocks(self):
        for mock_handler in self._mock_handlers:
            mock_handler.mock.stop()


    ### Logging mocks
    @staticmethod
    def _log_error(msg, level='ERROR'):
        HassMock._log_log(msg, level)

    @staticmethod
    def _log_log(msg, level='INFO'):
        # Renamed the function to remove confusion
        get_logging_level_from_name = logging.getLevelName
        logging.log(get_logging_level_from_name(level), msg)
