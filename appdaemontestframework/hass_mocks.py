import logging
import mock
from appdaemon.plugins.hass.hassapi import Hass
import textwrap
import warnings


class HassMocks:
    def __init__(self):
        # Mocked out init for Hass class.
        # It needs to be in this scope so it can get access to variables used here like `_hass_instances`
        _hass_instances = [] # use a local variable so we can access it below in `_hass_init_mock`
        self._hass_instances = _hass_instances # list of all hass instances

        def _hass_init_mock(self, _ad, name, *_args):
            _hass_instances.append(self)
            self.name = name


        # This is a list of all mocked out functions.
        self._mock_handlers = [
            ### Meta
            # Patch the __init__ method to skip Hass initialization. Use autospec so we can access the `self` object
            MockHandler(Hass, '__init__', side_effect=_hass_init_mock, autospec=True),

            ### logging
            MockHandler(Hass, 'log', side_effect=self._log_log),
            MockHandler(Hass, 'error', side_effect=self._log_error),

            ### Scheduler callback registrations functions
            # Wrap all these so we can re-use the AppDaemon code, but check if they were called
            MockHandler(Hass, 'run_in'),
            MockHandler(Hass, 'run_once'),
            MockHandler(Hass, 'run_at'),
            MockHandler(Hass, 'run_daily'),
            MockHandler(Hass, 'run_hourly'),
            MockHandler(Hass, 'run_minutely'),
            MockHandler(Hass, 'run_every'),
            MockHandler(Hass, 'cancel_timer'),

            ### Sunrise and sunset functions
            MockHandler(Hass, 'run_at_sunrise'),
            MockHandler(Hass, 'run_at_sunset'),

            ### Listener callback registrations functions
            MockHandler(Hass, 'listen_event'),
            MockHandler(Hass, 'listen_state'),

            ### State functions / attr
            MockHandler(Hass, 'set_state'),
            MockHandler(Hass, 'get_state'),
            MockHandler(Hass, 'time'),
            MockHandler(Hass, 'args'),  # Not a function, attribute. But same patching logic

            ### Interactions functions
            MockHandler(Hass, 'call_service'),
            MockHandler(Hass, 'turn_on'),
            MockHandler(Hass, 'turn_off'),

            ### Custom callback functions
            MockHandler(Hass, 'register_constraint'),
            MockHandler(Hass, 'now_is_between'),
            MockHandler(Hass, 'notify'),

            ### Miscellaneous Helper Functions
            MockHandler(Hass, 'entity_exists'),
        ]

        # Generate a dictionary of mocked Hass functions for use by older code
        # Note: This interface is considered deprecated and should be replaced with calls to public
        # methods in the HassMocks object going forward.
        self._hass_functions = {}
        for mock_handler in self._mock_handlers:
            self._hass_functions[mock_handler.function_name] = mock_handler.mock

        # ensure compatibility with older versions of AppDaemon
        self._hass_functions['passed_args'] = self._hass_functions['args']

    ### Mock handling
    def unpatch_mocks(self):
        """Stops all mocks this class handles."""
        for mock_handler in self._mock_handlers:
            mock_handler.patch.stop()


    ### Access to the deprecated hass_functions dict.
    @property
    def hass_functions(self):
        return self._hass_functions

    ### Logging mocks
    @staticmethod
    def _log_error(msg, level='ERROR'):
        HassMocks._log_log(msg, level)

    @staticmethod
    def _log_log(msg, level='INFO'):
        # Renamed the function to remove confusion
        get_logging_level_from_name = logging.getLevelName
        logging.log(get_logging_level_from_name(level), msg)


class MockHandler:
    """A class for generating a mock in an object and holding on to info about it.
    :param object_to_patch: The object to patch
    :param function_name: the name of the function to patch in the object
    :param side_effect: side effect method to call. If not set, it will just return `None`
    :param autospec: If `True` will autospec the Mock signature. Useful for getting `self` in side effects.
    """
    def __init__(self, object_to_patch, function_name, side_effect=None, autospec=False):
        self.function_name = function_name
        return_value = None
        self.patch = mock.patch.object(object_to_patch, self.function_name, create=True,
                                       autospec=autospec, side_effect=side_effect, return_value=None)
        self.mock = self.patch.start()


class WrappedMockHandler(MockHandler):
    """Helper class that privides a 'wrapped' mock. This will automatically call the original function while still providing
    a Mock for asserts and the such."""
    def __init__(self, object_to_patch, function_name):
        original_function = getattr(object_to_patch, function_name)
        super().__init__(object_to_patch, function_name, side_effect=original_function, autospec=True)
