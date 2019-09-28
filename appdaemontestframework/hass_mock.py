import logging
import mock
from appdaemon.plugins.hass.hassapi import Hass
from appdaemontestframework.scheduler_mocks import SchedulerMocks
import textwrap


class HassMock:
    def __init__(self):
        # Make instances of encapsulated mock functionality
        self._schedule_mocks = SchedulerMocks()

        # Mocked out init for Hass. It needs to be in this scope so it can get access to the scheduler mock instance
        insert_schedule_mock = self._schedule_mocks.insert_schedule_mock # to avoid `self` shadowing in `_hass_init_mock`
        _hass_instances = []
        self._hass_instances = _hass_instances # list of all hass instances
        def _hass_init_mock(self, _ad, name, _logger, _error, _args, _config, _app_config, _global_vars):
            _hass_instances.append(self)
            self.name = name

            # Wrap initilize in a Mock so we check if it was run
            self.initialize_mock = WrappedMockHandler(self, 'initialize')

            # Mock out the AD instance so we can re-use Hass internal scheduling functions as-is
            class AD(object):
                pass
            mock.patch.object(AD, 'log', create=True).start()
            mock.patch.object(AD, 'insert_schedule', create=True, side_effect=insert_schedule_mock).start()
            self.AD = AD()

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
            WrappedMockHandler(Hass, 'run_in'),
            WrappedMockHandler(Hass, 'run_once'),
            WrappedMockHandler(Hass, 'run_at'),
            WrappedMockHandler(Hass, 'run_daily'),
            WrappedMockHandler(Hass, 'run_hourly'),
            WrappedMockHandler(Hass, 'run_minutely'),
            WrappedMockHandler(Hass, 'run_every'),

            MockHandler(Hass, 'cancel_timer', side_effect=self._schedule_mocks.cancel_timer_mock),

            ### Sunrise and sunset functions
            MockHandler(Hass, 'run_at_sunrise'),
            MockHandler(Hass, 'run_at_sunset'),

            ### Listener callback registrations functions
            MockHandler(Hass, 'listen_event'),
            MockHandler(Hass, 'listen_state'),

            ### State functions / attr
            MockHandler(Hass, 'set_state'),
            MockHandler(Hass, 'get_state'),
            MockHandler(Hass, 'get_now', side_effect=self._schedule_mocks.get_now_mock),
            MockHandler(Hass, 'get_now_ts', side_effect=self._schedule_mocks.get_now_ts_mock),
            MockHandler(Hass, 'args'),  # Not a function, attribute. But same patching logic

            ### Interactions functions
            MockHandler(Hass, 'call_service'),
            MockHandler(Hass, 'turn_on'),
            MockHandler(Hass, 'turn_off'),

            ### Custom callback functions
            MockHandler(Hass, 'register_constraint'),
            MockHandler(Hass, 'now_is_between'),
            MockHandler(Hass, 'notify'),
        ]

        # Generate a dictionary of mocked Hass functions for use by `assert_that` and `given_that`
        self._hass_functions = {}
        for mock_handler in self._mock_handlers:
            self._hass_functions[mock_handler.function_name] = mock_handler.mock
        # ensure compatibility with older versions of AppDaemon
        self._hass_functions['passed_args'] = self._hass_functions['args']

    def unpatch_mocks(self):
        for mock_handler in self._mock_handlers:
            mock_handler.patch.stop()

    ### Logging mocks
    @staticmethod
    def _log_error(msg, level='ERROR'):
        HassMock._log_log(msg, level)

    @staticmethod
    def _log_log(msg, level='INFO'):
        # Renamed the function to remove confusion
        get_logging_level_from_name = logging.getLevelName
        logging.log(get_logging_level_from_name(level), msg)

    ### Access to internal scheduler
    def set_start_time(self, time):
        self._schedule_mocks.set_start_time(time)

    ### Internal state checkers
    def assert_automataions_initialized(self):
        """raises an exception if any automations haven't been initialized"""
        uninited_automations = []
        for instance in self._hass_instances:
            if not instance.initialize_mock.mock.called:
                uninited_automations.append(instance)
        if uninited_automations:
            error = textwrap.dedent("""\
                    AssertThat called before all automations initialized. Either directly call `initialize()` on
                    objects or use a test fixtures that does this for use.

                    Uninitalized automation instances:""")
            for automation in uninited_automations:
                error += "\n\tClass: {}, Name: {}".format(automation.__class__.__name__, automation.name)
            raise RuntimeError(error)


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
    """Heper class that privides a 'wrapped' mock. This will automatically call the original function while still providing
    a Mock for asserts and the stuch."""
    def __init__(self, object_to_patch, function_name):
        super().__init__(object_to_patch, function_name, side_effect=getattr(object_to_patch, function_name), autospec=True)
