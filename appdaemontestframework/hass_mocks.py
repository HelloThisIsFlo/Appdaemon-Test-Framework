import logging
import warnings
import mock
import appdaemon
import asyncio
import threading
import datetime
from packaging.version import Version
from appdaemontestframework.appdaemon_mock.appdaemon import MockAppDaemon
from appdaemon.plugins.hass.hassapi import Hass

_hass_instances = []

CURRENT_APPDAEMON_VERSION = Version(appdaemon.utils.__version__)


def is_appdaemon_version_at_least(version_as_string):
    expected_appdaemon_version = Version(version_as_string)
    return CURRENT_APPDAEMON_VERSION >= expected_appdaemon_version


class _DeprecatedAndUnsupportedAppdaemonCheck:
    already_warned_during_this_test_session = False
    min_supported_appdaemon_version = "4.0.0"
    min_deprecated_appdaemon_version = "4.0.0"

    @classmethod
    def show_warning_only_once(cls):
        if cls.already_warned_during_this_test_session is True:
            return
        cls.already_warned_during_this_test_session = True

        appdaemon_version_unsupported = not is_appdaemon_version_at_least(
            cls.min_supported_appdaemon_version
        )
        appdaemon_version_deprecated = not is_appdaemon_version_at_least(
            cls.min_deprecated_appdaemon_version
        )

        if appdaemon_version_unsupported:
            raise Exception(
                "Appdaemon-Test-Framework only support Appdemon >={} "
                "Your current Appdemon version is {}".format(
                    cls.min_supported_appdaemon_version, CURRENT_APPDAEMON_VERSION
                )
            )

        if appdaemon_version_deprecated:
            warnings.warn(
                "Appdaemon-Test-Framework will only support Appdaemon >={} "
                "until the next major release. "
                "Your current Appdemon version is {}".format(
                    cls.min_deprecated_appdaemon_version, CURRENT_APPDAEMON_VERSION
                ),
                DeprecationWarning,
            )


class AsyncSpyMockHandler(object):
    """
    Mock Handler that provides async spy functionality. When invoked, it will
    call our MockScheduler methods instead of the original async methods,
    but still provide all Mock-related functionality for tracking calls.
    """

    def __init__(self, object_to_patch, function_name, mock_scheduler_method=None):
        self.function_or_field_name = function_name
        self.mock_scheduler_method = mock_scheduler_method

        # Create a wrapper that does both: tracks the call AND executes our logic
        def async_side_effect(mock_self, *args, **kwargs):
            # The first argument is the mock itself when using side_effect
            # Let the mock record the call normally first
            # We can't use _mock_call directly, so we'll manually track
            if not hasattr(mock_self, "call_count"):
                mock_self.call_count = 0
            if not hasattr(mock_self, "call_args_list"):
                mock_self.call_args_list = []

            mock_self.call_count += 1
            call_obj = mock.call(*args, **kwargs)
            mock_self.call_args = call_obj
            mock_self.call_args_list.append(call_obj)

            # Now execute our custom logic
            method_args = args

            # Delegate to our mock scheduler method if provided
            if self.mock_scheduler_method:
                # Pass None as hass_self since our mock_scheduler_method will find the real instance
                result = self.mock_scheduler_method(None, *method_args, **kwargs)
            else:
                # For methods without custom implementation, return a suitable default
                if function_name in [
                    "run_in",
                    "run_at",
                    "run_daily",
                    "run_hourly",
                    "run_minutely",
                    "run_every",
                    "run_once",
                ]:
                    # Return a mock handle for scheduler methods
                    result = f"mock_handle_{function_name}_{id(method_args)}"
                else:
                    result = mock_self.return_value

            return result

        # Set up the patch with our wrapper as side_effect and autospec=True
        # so that mock_self is passed as first argument
        self.patch = mock.patch.object(
            object_to_patch,
            function_name,
            side_effect=async_side_effect,
            autospec=True,
        )
        self.mock = self.patch.start()


class HassMocks:
    def __init__(self):
        _DeprecatedAndUnsupportedAppdaemonCheck.show_warning_only_once()
        # Mocked out init for Hass class.
        self._hass_instances = []  # list of all hass instances

        hass_mocks = self
        AD = MockAppDaemon()
        self.AD = AD

        def _hass_init_mock(self, _ad, config_model, *_args):
            hass_mocks._hass_instances.append(self)
            # Store the config_model for new Appdaemon versions
            self._config_model = config_model
            # In new Appdaemon, name comes from config_model
            if hasattr(config_model, "name"):
                self._name = config_model.name
            else:
                # Fallback for old-style string name
                self._name = config_model
            self.AD = AD
            self.logger = logging.getLogger(__name__)

        # Create async-compatible scheduler method implementations
        def mock_datetime(hass_self_unused, *args, **kwargs):
            """Mock implementation of datetime that uses our MockScheduler"""
            # Find the real automation instance
            real_automation = None
            for instance in hass_mocks._hass_instances:
                if hasattr(instance, "AD") and hasattr(instance.AD, "sched"):
                    real_automation = instance
                    break

            if real_automation is None:
                raise RuntimeError("Could not find real automation instance")

            # Use our mock scheduler to get the current time
            current_time = real_automation.AD.sched.get_now_sync()
            # Convert to naive datetime as expected by the automation
            return real_automation.AD.sched.make_naive(current_time)

        def mock_time(hass_self_unused, *args, **kwargs):
            """Mock implementation of time that uses our MockScheduler"""
            # Find the real automation instance
            real_automation = None
            for instance in hass_mocks._hass_instances:
                if hasattr(instance, "AD") and hasattr(instance.AD, "sched"):
                    real_automation = instance
                    break

            if real_automation is None:
                raise RuntimeError("Could not find real automation instance")

            # Use our mock scheduler to get the current time
            current_time = real_automation.AD.sched.get_now_sync()
            # Convert to naive datetime and return just the time part
            naive_datetime = real_automation.AD.sched.make_naive(current_time)
            return naive_datetime.time()

        def mock_run_in(hass_self_unused, *args, **kwargs):
            """Mock implementation of run_in that uses our MockScheduler"""
            # Extract callback and delay from args
            # run_in(callback, delay) or run_in(callback, delay, **kwargs)
            callback = args[0] if len(args) > 0 else kwargs.get("callback")
            delay = (
                args[1]
                if len(args) > 1
                else kwargs.get("delay", kwargs.get("seconds", 0))
            )

            # Convert delay to seconds if needed
            if hasattr(delay, "total_seconds"):
                delay_seconds = delay.total_seconds()
            else:
                delay_seconds = float(delay)

            # Find the real automation instance from the hass_instances
            real_automation = None
            for instance in hass_mocks._hass_instances:
                if hasattr(instance, "AD") and hasattr(instance.AD, "sched"):
                    real_automation = instance
                    break

            if real_automation is None:
                raise RuntimeError("Could not find real automation instance")

            # Calculate target time using the real automation's scheduler
            current_time = real_automation.AD.sched.get_now_sync()
            target_time = current_time + datetime.timedelta(seconds=delay_seconds)

            # Use our mock scheduler
            return real_automation.AD.sched.insert_schedule_sync(
                name="run_in",
                aware_dt=target_time,
                callback=callback,
                repeat=False,
                type_="run_in",
                **kwargs,
            )

        def mock_cancel_timer(hass_self_unused, *args, **kwargs):
            """Mock implementation of cancel_timer"""
            handle = args[0] if len(args) > 0 else kwargs.get("handle")

            # Find the real automation instance
            real_automation = None
            for instance in hass_mocks._hass_instances:
                if hasattr(instance, "AD") and hasattr(instance.AD, "sched"):
                    real_automation = instance
                    break

            if real_automation is None:
                raise RuntimeError("Could not find real automation instance")

            return real_automation.AD.sched.cancel_timer_sync(
                name="cancel_timer", handle=handle
            )

        # This is a list of all mocked out functions.
        self._mock_handlers = [
            ### Meta
            # Patch the __init__ method to skip Hass initialization.
            # Use autospec so we can access the `self` object
            MockHandler(Hass, "__init__", side_effect=_hass_init_mock, autospec=True),
            ### logging
            MockHandler(Hass, "log", side_effect=self._log_log),
            MockHandler(Hass, "error", side_effect=self._log_error),
            ### Scheduler callback registrations functions - now with async support
            AsyncSpyMockHandler(Hass, "run_in", mock_scheduler_method=mock_run_in),
            MockHandler(Hass, "run_once"),
            MockHandler(Hass, "run_at"),
            MockHandler(Hass, "run_daily"),
            MockHandler(Hass, "run_hourly"),
            MockHandler(Hass, "run_minutely"),
            MockHandler(Hass, "run_every"),
            AsyncSpyMockHandler(
                Hass, "cancel_timer", mock_scheduler_method=mock_cancel_timer
            ),
            ### Sunrise and sunset functions
            MockHandler(Hass, "run_at_sunrise"),
            MockHandler(Hass, "run_at_sunset"),
            ### Listener callback registrations functions
            MockHandler(Hass, "listen_event"),
            MockHandler(Hass, "listen_state"),
            ### State functions / attr
            MockHandler(Hass, "set_state"),
            MockHandler(Hass, "get_state"),
            AsyncSpyMockHandler(Hass, "time", mock_scheduler_method=mock_time),
            AsyncSpyMockHandler(Hass, "datetime", mock_scheduler_method=mock_datetime),
            DictMockHandler(Hass, "args"),
            ### Interactions functions
            MockHandler(Hass, "call_service"),
            MockHandler(Hass, "turn_on"),
            MockHandler(Hass, "turn_off"),
            MockHandler(Hass, "fire_event"),
            ### Custom callback functions
            MockHandler(Hass, "register_constraint"),
            MockHandler(Hass, "now_is_between"),
            MockHandler(Hass, "notify"),
            ### Miscellaneous Helper Functions
            MockHandler(Hass, "entity_exists"),
        ]

        # Generate a dictionary of mocked Hass functions for use by older code
        # Note: This interface is considered deprecated and should be replaced
        # with calls to public methods in the HassMocks object going forward.
        self._hass_functions = {}
        for mock_handler in self._mock_handlers:
            self._hass_functions[mock_handler.function_or_field_name] = (
                mock_handler.mock
            )

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
    def _log_error(msg, level="ERROR"):
        HassMocks._log_log(msg, level)

    @staticmethod
    def _log_log(msg, level="INFO"):
        # Renamed the function to remove confusion
        get_logging_level_from_name = logging.getLevelName
        logging.log(get_logging_level_from_name(level), msg)


class MockHandler:
    """
    A class for generating a mock in an object and holding on to info about it.
    :param object_to_patch: The object to patch
    :param function_or_field_name: the name of the function to patch in the
    object
    :param side_effect: side effect method to call. If not set, it will just
    return `None`
    :param autospec: If `True` will autospec the Mock signature. Useful for
    getting `self` in side effects.
    """

    def __init__(
        self, object_to_patch, function_or_field_name, side_effect=None, autospec=False
    ):
        self.function_or_field_name = function_or_field_name
        patch_kwargs = self._patch_kwargs(side_effect, autospec)
        self.patch = mock.patch.object(
            object_to_patch, function_or_field_name, **patch_kwargs
        )
        self.mock = self.patch.start()

    def _patch_kwargs(self, side_effect, autospec):
        return {
            "create": True,
            "side_effect": side_effect,
            "return_value": None,
            "autospec": autospec,
        }


class DictMockHandler(MockHandler):
    class MockDict(dict):
        def reset_mock(self):
            pass

    def __init__(self, object_to_patch, field_name):
        super().__init__(object_to_patch, field_name)

    def _patch_kwargs(self, _side_effect, _autospec):
        return {"create": True, "new": self.MockDict()}


class SpyMockHandler(MockHandler):
    """
    Mock Handler that provides a Spy. That is, when invoke it will call the
    original function but still provide all Mock-related functionality
    """

    def __init__(self, object_to_patch, function_name):
        original_function = getattr(object_to_patch, function_name)
        super().__init__(
            object_to_patch, function_name, side_effect=original_function, autospec=True
        )
