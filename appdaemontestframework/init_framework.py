import logging
import random
import mock
import sys
from appdaemon.plugins.hass.hassapi import Hass

def random_int(*args, **kwargs):
    #return pseudo random number, should be ok for testing
    return random.randrange(0, sys.maxsize)


def patch_hass():
    """
    Patch the Hass API and returns a tuple of:
    - The patched functions (as Dict)
    - A callback to un-patch all functions
    """
    class MockInfo:
        """Holds information about a function that will be mocked"""
        def __init__(self, object_to_patch, function_name, autospec=False, side_effect=None):
            self.object_to_patch = object_to_patch
            self.function_name = function_name
            # Autospec will include `self` in the mock signature.
            # Useful if you want a sideeffect that modifies the actual object instance.
            self.autospec = autospec
            self.side_effect = side_effect
    
    actionable_functions_to_patch = [
        # Meta
        MockInfo(Hass, '__init__', autospec=True),  # Patch the __init__ method to skip Hass initialization

        # Logging
        MockInfo(Hass, 'log'),
        MockInfo(Hass, 'error'),

        # Scheduler callback registrations functions
        MockInfo(Hass, 'run_in', side_effect=random_int),
        MockInfo(Hass, 'run_once', side_effect=random_int),
        MockInfo(Hass, 'run_at', side_effect=random_int),
        MockInfo(Hass, 'run_daily', side_effect=random_int),
        MockInfo(Hass, 'run_hourly', side_effect=random_int),
        MockInfo(Hass, 'run_minutely', side_effect=random_int),
        MockInfo(Hass, 'run_every', side_effect=random_int),
        MockInfo(Hass, 'cancel_timer'),

        # Sunrise and sunset functions
        MockInfo(Hass, 'run_at_sunrise', side_effect=random_int),
        MockInfo(Hass, 'run_at_sunset', side_effect=random_int),

        # Listener callback registrations functions
        MockInfo(Hass, 'listen_event', side_effect=random_int),
        MockInfo(Hass, 'listen_state', side_effect=random_int),

        # Sunrise and sunset functions
        MockInfo(Hass, 'run_at_sunrise', side_effect=random_int),
        MockInfo(Hass, 'run_at_sunset', side_effect=random_int),

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
        if mock_info.side_effect is not None:
            patched_function.side_effect = mock_info.side_effect
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
