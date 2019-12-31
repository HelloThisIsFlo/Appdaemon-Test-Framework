from pytest import fixture

from appdaemontestframework import HassMocks, AssertThatWrapper, GivenThatWrapper, TimeTravelWrapper

pytest_plugins = 'pytester'


@fixture
def hass_mocks():
    hass_mocks = HassMocks()
    yield hass_mocks
    hass_mocks.unpatch_mocks()


@fixture
def hass_functions(hass_mocks):
    return hass_mocks.hass_functions


@fixture
def given_that(hass_functions):
    return GivenThatWrapper(hass_functions)


@fixture
def assert_that(hass_functions):
    return AssertThatWrapper(hass_functions)


@fixture
def time_travel(hass_functions):
    return TimeTravelWrapper(hass_functions)


@fixture
def configure_appdaemontestframework_for_pytester(testdir):
    testdir.makeconftest(
        """
        from appdaemontestframework.pytest_conftest import *
    """)
