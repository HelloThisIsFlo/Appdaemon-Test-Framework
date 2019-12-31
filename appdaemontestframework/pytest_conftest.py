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
def given_that(hass_mocks):
    return GivenThatWrapper(hass_mocks)


@fixture
def assert_that(hass_mocks):
    return AssertThatWrapper(hass_mocks)


@fixture
def time_travel(hass_mocks):
    return TimeTravelWrapper(hass_mocks)


@fixture
def configure_appdaemontestframework_for_pytester(testdir):
    testdir.makeconftest(
        """
        from appdaemontestframework.pytest_conftest import *
    """)
