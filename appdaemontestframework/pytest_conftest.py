import textwrap
import warnings
from typing import Iterator

from pytest import fixture

import appdaemontestframework.assert_that
import appdaemontestframework.given_that
import appdaemontestframework.hass_mocks
from appdaemontestframework import (
    AssertThatWrapper,
    GivenThatWrapper,
    HassMocks,
    TimeTravelWrapper,
    WhenWrapper,
)

# Only expose the test fixtures and pytest needed things so `import *`
# doesn't pollute things
__all__ = [
    "pytest_plugins",
    "fixture",
    "hass_mocks",
    "hass_functions",
    "given_that",
    "assert_that",
    "time_travel",
    "when",
]

pytest_plugins = "pytester"


class DeprecatedDict(dict):
    """Deprecation warning when accessing any of it's members."""

    def __getitem__(self, key):
        message = textwrap.dedent(
            """
            Usage of the `hass_functions` test fixture is deprecated.
            Replace `hass_functions` with the `hass_mocks` test fixture and
            access the `hass_functions` property.
            hass_functions['{0}'] ==becomes==> hass_mocks.hass_functions['{0}']
            """.format(
                key
            )
        )
        warnings.warn(message, DeprecationWarning, stacklevel=2)
        return super().__getitem__(key)


@fixture
def hass_mocks() -> Iterator[appdaemontestframework.hass_mocks.HassMocks]:
    hass_mocks = HassMocks()
    yield hass_mocks
    hass_mocks.unpatch_mocks()


@fixture
def hass_functions(
    hass_mocks: appdaemontestframework.hass_mocks.HassMocks,
) -> DeprecatedDict:
    return DeprecatedDict(hass_mocks.hass_functions)


@fixture
def given_that(
    hass_mocks: appdaemontestframework.hass_mocks.HassMocks,
) -> appdaemontestframework.given_that.GivenThatWrapper:
    return GivenThatWrapper(hass_mocks)


@fixture
def when(given_that):
    return WhenWrapper(given_that)


@fixture
def assert_that(
    hass_mocks: appdaemontestframework.hass_mocks.HassMocks,
) -> appdaemontestframework.assert_that.AssertThatWrapper:
    return AssertThatWrapper(hass_mocks)


@fixture
def time_travel(hass_mocks):
    return TimeTravelWrapper(hass_mocks)
