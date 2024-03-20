import logging as liblogging
import warnings

# Sorting these imports make the whole app to fail, so...
# flake8: noqa: I001
from appdaemontestframework.appdaemon_mock.appdaemon import MockAppDaemon
import appdaemon.utils
from unittest import mock
from appdaemon.plugins.hass.hassapi import Hass
from packaging.version import Version
from typing import Callable, Dict, Optional, Type, Union
from unittest.mock import MagicMock

CURRENT_APPDAEMON_VERSION = Version(appdaemon.utils.__version__)


def is_appdaemon_version_at_least(version_as_string: str) -> bool:
    expected_appdaemon_version = Version(version_as_string)
    return CURRENT_APPDAEMON_VERSION >= expected_appdaemon_version


class _DeprecatedAndUnsupportedAppdaemonCheck:
    already_warned_during_this_test_session = False
    min_supported_appdaemon_version = "4.0.0"
    min_deprecated_appdaemon_version = "4.0.0"

    @classmethod
    def show_warning_only_once(cls) -> None:
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
                    cls.min_supported_appdaemon_version,
                    CURRENT_APPDAEMON_VERSION,
                )
            )

        if appdaemon_version_deprecated:
            warnings.warn(
                "Appdaemon-Test-Framework will only support Appdaemon >={} "
                "until the next major release. "
                "Your current Appdemon version is {}".format(
                    cls.min_deprecated_appdaemon_version,
                    CURRENT_APPDAEMON_VERSION,
                ),
                DeprecationWarning,
            )


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
        self,
        object_to_patch: Type[Hass],
        function_or_field_name: str,
        side_effect: Optional[Callable] = None,
        autospec: bool = False,
    ) -> None:
        self.function_or_field_name = function_or_field_name
        patch_kwargs = self._patch_kwargs(side_effect, autospec)
        self.patch = mock.patch.object(
            object_to_patch, function_or_field_name, **patch_kwargs
        )
        self.mock = self.patch.start()

    def _patch_kwargs(
        self, side_effect: Optional[Callable], autospec: bool
    ) -> Dict[str, Optional[Union[bool, Callable]]]:
        return {
            "create": True,
            "side_effect": side_effect,
            "return_value": None,
            "autospec": autospec,
        }


class DictMockHandler(MockHandler):
    class MockDict(dict):
        def reset_mock(self) -> None:
            pass

    def __init__(self, object_to_patch: Type[Hass], field_name: str) -> None:
        super().__init__(object_to_patch, field_name)

    def _patch_kwargs(
        self, _side_effect: None, _autospec: bool
    ) -> Dict[str, Union[bool, MockDict]]:
        return {"create": True, "new": self.MockDict()}


class SpyMockHandler(MockHandler):
    """
    Mock Handler that provides a Spy. That is, when invoke it will call the
    original function but still provide all Mock-related functionality
    """

    def __init__(
        self, object_to_patch: Type[Hass], function_name: str
    ) -> None:
        original_function = getattr(object_to_patch, function_name)
        super().__init__(
            object_to_patch,
            function_name,
            side_effect=original_function,
            autospec=True,
        )


class HassMocks:
    def __init__(self) -> None:
        _DeprecatedAndUnsupportedAppdaemonCheck.show_warning_only_once()
        # Mocked out init for Hass class.
        self._hass_instances = []  # list of all hass instances

        hass_mocks = self
        AD = MockAppDaemon()
        self.AD = AD

        def _hass_init_mock(
            self, ad, name, logging, args, config, app_config, global_vars
        ):
            hass_mocks._hass_instances.append(self)
            self.name = name
            self.AD = AD
            self.logger = liblogging.getLogger(__name__)
            self._namespace = "default"
            if args:
                self.args = args

        # This is a list of all mocked out functions.
        self._mock_handlers = [
            # > Meta
            # Patch the __init__ method to skip Hass initialization.
            # Use autospec so we can access the `self` object
            MockHandler(
                Hass, "__init__", side_effect=_hass_init_mock, autospec=True
            ),
            # > logging
            MockHandler(Hass, "log", side_effect=self._log_log),
            MockHandler(Hass, "error", side_effect=self._log_error),
            # > Scheduler callback registrations functions
            # Wrap all these so we can re-use the AppDaemon code, but check
            # if they were called
            SpyMockHandler(Hass, "run_in"),
            MockHandler(Hass, "run_once"),
            MockHandler(Hass, "run_at"),
            MockHandler(Hass, "run_daily"),
            MockHandler(Hass, "run_hourly"),
            MockHandler(Hass, "run_minutely"),
            MockHandler(Hass, "run_every"),
            SpyMockHandler(Hass, "cancel_timer"),
            # > Sunrise and sunset functions
            MockHandler(Hass, "run_at_sunrise"),
            MockHandler(Hass, "run_at_sunset"),
            # > Listener callback registrations functions
            MockHandler(Hass, "listen_event"),
            MockHandler(Hass, "listen_state"),
            # > State functions / attr
            MockHandler(Hass, "set_state"),
            MockHandler(Hass, "get_state"),
            SpyMockHandler(Hass, "time"),
            DictMockHandler(Hass, "args"),
            # > Interactions functions
            MockHandler(Hass, "call_service"),
            MockHandler(Hass, "turn_on"),
            MockHandler(Hass, "turn_off"),
            MockHandler(Hass, "fire_event"),
            MockHandler(Hass, "toggle"),
            # > Custom callback functions
            MockHandler(Hass, "register_constraint"),
            MockHandler(Hass, "now_is_between"),
            MockHandler(Hass, "notify"),
            # > Miscellaneous Helper Functions
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

    # Mock handling
    def unpatch_mocks(self) -> None:
        """Stops all mocks this class handles."""
        for mock_handler in self._mock_handlers:
            mock_handler.patch.stop()

    # Access to the deprecated hass_functions dict.
    @property
    def hass_functions(
        self,
    ) -> Dict[str, Union[Callable, MagicMock, DictMockHandler.MockDict]]:
        return self._hass_functions

    # Logging mocks
    @staticmethod
    def _log_error(msg: str, level: str = "ERROR") -> None:
        HassMocks._log_log(msg, level)

    @staticmethod
    def _log_log(msg: str, level: str = "INFO") -> None:
        # Renamed the function to remove confusion
        get_logging_level_from_name = liblogging.getLevelName
        liblogging.log(get_logging_level_from_name(level), msg)
