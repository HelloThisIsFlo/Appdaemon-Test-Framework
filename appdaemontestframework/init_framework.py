import logging

import mock
from appdaemon.plugins.hass.hassapi import Hass

def patch_hass():
    """
    Patch the Hass API and returns a tuple of:
    - The patched functions (as Dict)
    - A callback to un-patch all functions
    """

    actionable_functions_to_patch = [
        # Meta
        '__init__',  # Patch the __init__ method to skip Hass initialisation

        # Logging
        'log',
        'error',

        # Callback registrations functions
        'run_daily',
        'run_minutely',
        'run_in',
        'cancel_timer',
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

    patches = []
    hass_functions = {}
    for function_name in actionable_functions_to_patch:
        autospec = False
        # spec the __init__ call se we get access to the instance object in the mock
        if function_name == '__init__':
            autospec = True
        patch_function = mock.patch.object(Hass, function_name, create=True, autospec=autospec)
        patches.append(patch_function)
        patched_function = patch_function.start()
        patched_function.return_value = None
        hass_functions[function_name] = patched_function

    def unpatch_callback():
        for patch in patches:
            patch.stop()

    _ensure_compatibility_with_previous_versions(hass_functions)
    _mock_logging(hass_functions)
    _mock_hass_init(hass_functions)

    return hass_functions, unpatch_callback


def _ensure_compatibility_with_previous_versions(hass_functions):
    hass_functions['passed_args'] = hass_functions['args']


def _mock_logging(hass_functions):
    # Renamed the function to remove confusion
    get_logging_level_from_name = logging.getLevelName

    def log_error(msg, level='ERROR'):
        log_log(msg, level)

    def log_log(msg, level='INFO'):
        logging.log(get_logging_level_from_name(level), msg)

    hass_functions['error'].side_effect = log_error
    hass_functions['log'].side_effect = log_log

def _mock_hass_init(hass_functions):
    """Mock the Hass object init and set up class attributes that are used by automations"""
    def hass_init_mock(self, ad, name, logger, error, args, config, app_config, global_vars):
        self.name = name

    hass_functions['__init__'].side_effect = hass_init_mock
