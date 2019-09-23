import logging
import mock
from appdaemon.plugins.hass.hassapi import Hass
from appdaemontestframework.scheduler_mocks import SchedulerMocks


class HassMock:
    def __init__(self):
        self._schedule_mocks = SchedulerMocks()

        insert_schedule_mock = self._schedule_mocks.insert_schedule_mock

        def _hass_init_mock(self, _ad, name, _logger, _error, _args, _config, _app_config, _global_vars):
            self.name = name
            class AD(object):
                pass
            mock.patch.object(AD, 'log', create=True).start()
            mock.patch.object(AD, 'insert_schedule', create=True, side_effect=insert_schedule_mock).start()
            self.AD = AD()
            #self.AD.insert_schedule('', 0, None, None, None)

        self._mock_handlers = [
            ### Meta
            # Patch the __init__ method to skip Hass initialization. Use autospec so we can access the `self` object
            MockHandler(Hass, '__init__', side_effect=_hass_init_mock, autospec=True),
            #MockHandler(Hass, '__init__'),

            ### logging
            MockHandler(Hass, 'log', side_effect=self._log_log),
            MockHandler(Hass, 'error', side_effect=self._log_error),

            ### Scheduler callback registrations functions
            # Wrap all these so we can re-use the AppDaemon code, but check if they were called
            MockHandler(Hass, 'run_in', wrapped=True),
            MockHandler(Hass, 'run_once', wrapped=True),
            MockHandler(Hass, 'run_at', wrapped=True),
            MockHandler(Hass, 'run_daily', wrapped=True),
            MockHandler(Hass, 'run_hourly', wrapped=True),
            MockHandler(Hass, 'run_minutely', wrapped=True),
            MockHandler(Hass, 'run_every', wrapped=True),

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

        # TODO: remove this temp convert the new _mocks into the old _hass_functions
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


class MockHandler:
    def __init__(self, object_to_patch, function_name, side_effect=None, wrapped=False, autospec=False):
        self.function_name = function_name
        # if wrapped is set to true, create a patch that wraps the original function
        return_value = None
        #wrapped_function =  None
        if wrapped:
            side_effect = getattr(object_to_patch, function_name)
            return_value = mock.DEFAULT
            autospec = True

        self.patch = mock.patch.object(object_to_patch, self.function_name, create=True,
                                       autospec=autospec, side_effect=side_effect, return_value=return_value)
        self.mock = self.patch.start()
