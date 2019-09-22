import logging

import mock
from appdaemon.plugins.hass.hassapi import Hass


class HassMock:
    def __init__(self):
        actionable_functions_to_patch = [
            # Meta
            '__init__',  # Patch the __init__ method to skip Hass initialisation

            # Logging
            'log',
            'error',

            # Scheduler callback registrations functions
            'run_in',
            'run_once',
            'run_at',
            'run_daily',
            'run_hourly',
            'run_minutely',
            'run_every',
            'cancel_timer',

            # Sunrise and sunset functions
            'run_at_sunrise',
            'run_at_sunset',

            # Listener callback registrations functions
            'listen_event',
            'listen_state',

            # State functions / attr
            'set_state',
            'get_state',
            'time',
            'args',  # Not a function, attribute. But same patching logic

            # Interactions functions
            'call_service',
            'turn_on',
            'turn_off',

            # Custom callback functions
            'register_constraint',
            'now_is_between',
            'notify'
        ]

        self._patches = []
        self._hass_functions = {}
        for function_name in actionable_functions_to_patch:
            patch_function = mock.patch.object(Hass, function_name, create=True)
            self._patches.append(patch_function)
            patched_function = patch_function.start()
            patched_function.return_value = None
            self._hass_functions[function_name] = patched_function

        self._ensure_compatibility_with_previous_versions()
        self._mock_logging()

    def _ensure_compatibility_with_previous_versions(self):
        self._hass_functions['passed_args'] = self._hass_functions['args']


    def _mock_logging(self):
        # Renamed the function to remove confusion
        get_logging_level_from_name = logging.getLevelName

        def log_error(msg, level='ERROR'):
            log_log(msg, level)

        def log_log(msg, level='INFO'):
            logging.log(get_logging_level_from_name(level), msg)

        self._hass_functions['error'].side_effect = log_error
        self._hass_functions['log'].side_effect = log_log

    def unpatch_mocks(self):
        for patch in self._patches:
            patch.stop()