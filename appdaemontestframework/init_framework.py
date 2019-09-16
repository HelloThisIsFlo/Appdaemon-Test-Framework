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

    patches = []
    hass_functions = {}
    for function_name in actionable_functions_to_patch:
        patch_function = mock.patch.object(Hass, function_name, create=True)
        patches.append(patch_function)
        patched_function = patch_function.start()
        patched_function.return_value = None
        hass_functions[function_name] = patched_function

    def unpatch_callback():
        for patch in patches:
            patch.stop()

    _ensure_compatibility_with_previous_versions(hass_functions)
    _mock_logging(hass_functions)

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
