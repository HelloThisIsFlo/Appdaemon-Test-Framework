from pytest import fixture

from appdaemontestframework import HassMock, AssertThatWrapper, GivenThatWrapper, TimeTravelWrapper

pytest_plugins = 'pytester'


@fixture
def hass_mock():
    hass_mock = HassMock()
    yield hass_mock
    hass_mock.unpatch_mocks()


@fixture
def given_that(hass_mock):
    return GivenThatWrapper(hass_mock._hass_functions)


@fixture
def assert_that(hass_mock):
    return AssertThatWrapper(hass_mock._hass_functions)


@fixture
def time_travel(hass_mock):
    return TimeTravelWrapper(hass_mock._hass_functions)


@fixture
def configure_appdaemontestframework_for_pytester(testdir):
    testdir.makeconftest(
        """
        from pytest import fixture
        from appdaemontestframework import HassMock, AssertThatWrapper, GivenThatWrapper, TimeTravelWrapper


        @fixture
        def hass_mock():
            hass_mock = HassMock()
            yield hass_mock
            hass_mock.unpatch_mocks()


        @fixture
        def given_that(hass_mock):
            return GivenThatWrapper(hass_mock._hass_functions)


        @fixture
        def assert_that(hass_mock):
            return AssertThatWrapper(hass_mock._hass_functions)


        @fixture
        def time_travel(hass_mock):
            return TimeTravelWrapper(hass_mock._hass_functions)
    """)
