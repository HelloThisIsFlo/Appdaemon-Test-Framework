from pytest import fixture
from appdaemontestframework import HassMocks, AssertThatWrapper, GivenThatWrapper, TimeTravelWrapper
import warnings
import textwrap

# Only expose the test fixtures and pytest needed things so `import *` doesn't pollute things
__all__ = [
    'pytest_plugins',
    'fixture',
    'hass_mocks',
    'hass_functions',
    'given_that',
    'assert_that',
    'time_travel',
]

pytest_plugins = 'pytester'


class DeprecatedDict(dict):
    """Helper class that will give a deprectaion warning when accessing any of it's members"""
    def __getitem__(self, key):
        message = textwrap.dedent(
            """
            Usage of the `hass_functions` test fixture is deprecated.
            Replace `hass_functions` with the `hass_mocks` test fixture and access the `hass_functions` property.
                hass_functions['{0}'] ==becomes==> hass_mocks.hass_functions['{0}']
            """.format(key))
        warnings.warn(message, DeprecationWarning, stacklevel=2)
        return super().__getitem__(key)


@fixture
def hass_mocks():
    hass_mocks = HassMocks()
    yield hass_mocks
    hass_mocks.unpatch_mocks()


@fixture
def hass_functions(hass_mocks):
    return DeprecatedDict(hass_mocks.hass_functions)


@fixture
def given_that(hass_mocks):
    return GivenThatWrapper(hass_mocks)


@fixture
def assert_that(hass_mocks):
    return AssertThatWrapper(hass_mocks)


@fixture
def time_travel(hass_mocks):
    return TimeTravelWrapper(hass_mocks)
