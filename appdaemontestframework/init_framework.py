import logging

import mock
from appdaemon.plugins.hass.hassapi import Hass


def patch_hass():
    """
    Patch the Hass API and returns a tuple of:
    - The patched functions (as Dict)
    - A callback to un-patch all functions
    """
    class MockInfo:
        """Holds information about a function that will be mocked"""
        def __init__(self, object_to_patch, function_name, autospec=False):
            self.object_to_patch = object_to_patch
            self.function_name = function_name
            # Autospec will include `self` in the mock signature.
            # Useful if you want a sideeffect that modifies the actual object instance.
            self.autospec = autospec

    actionable_functions_to_patch = [
        # Meta
        MockInfo(Hass, '__init__', autospec=True),  # Patch the __init__ method to skip Hass initialization

        # Logging
        MockInfo(Hass, 'log'),
        MockInfo(Hass, 'error'),

        # Scheduler callback registrations functions
        MockInfo(Hass, 'run_in'),
        MockInfo(Hass, 'run_once'),
        MockInfo(Hass, 'run_at'),
        MockInfo(Hass, 'run_daily'),
        MockInfo(Hass, 'run_hourly'),
        MockInfo(Hass, 'run_minutely'),
        MockInfo(Hass, 'run_every'),
        MockInfo(Hass, 'cancel_timer'),

        # Sunrise and sunset functions
        MockInfo(Hass, 'run_at_sunrise'),
        MockInfo(Hass, 'run_at_sunset'),

        # Listener callback registrations functions
        MockInfo(Hass, 'listen_event'),
        MockInfo(Hass, 'listen_state'),

        # Sunrise and sunset functions
        MockInfo(Hass, 'run_at_sunrise'),
        MockInfo(Hass, 'run_at_sunset'),

        # Listener callback registrations functions

        # State functions / attr
        MockInfo(Hass, 'set_state'),
        MockInfo(Hass, 'get_state'),
        MockInfo(Hass, 'time'),
        MockInfo(Hass, 'args'),  # Not a function, attribute. But same patching logic

        # Interactions functions
        MockInfo(Hass, 'call_service'),
        MockInfo(Hass, 'turn_on'),
        MockInfo(Hass, 'turn_off'),

        # Custom callback functions
        MockInfo(Hass, 'register_constraint'),
        MockInfo(Hass, 'now_is_between'),
        MockInfo(Hass, 'notify'),

        # Miscellaneous Helper Functions
        MockInfo(Hass, 'entity_exists')
    ]

    patches = []
    hass_functions = {}
    for mock_info in actionable_functions_to_patch:
        patch_function = mock.patch.object(mock_info.object_to_patch, mock_info.function_name, create=True,
                                           autospec=mock_info.autospec)
        patches.append(patch_function)
        patched_function = patch_function.start()
        patched_function.return_value = None
        hass_functions[mock_info.function_name] = patched_function

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
    def hass_init_mock(self, _ad, name, _logger, _error, _args, _config, _app_config, _global_vars):
        self.name = name

    hass_functions['__init__'].side_effect = hass_init_mock
