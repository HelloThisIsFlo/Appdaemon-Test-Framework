import appdaemon.plugins.hass.hassapi as hass

from appdaemontestframework import automation_fixture


class WithExtraHassFunctions(hass.Hass):
    def initialize(self):
        pass

    def call_notify(self):
        self.notify(message="test", name="html5")

    def call_now_is_between(self):
        self.now_is_between("sunset - 00:45:00", "sunrise + 00:45:00")

    def call_select_option(self):
        self.select_option("select_item", "value")


@automation_fixture(WithExtraHassFunctions)
def with_extra_hass_functions():
    pass


def test_now_is_between(given_that, with_extra_hass_functions, hass_mocks):
    with_extra_hass_functions.call_now_is_between()
    hass_mocks.hass_functions['now_is_between'].assert_called_with("sunset - 00:45:00", "sunrise + 00:45:00")


def test_notify(given_that, with_extra_hass_functions, hass_mocks):
    with_extra_hass_functions.call_notify()
    hass_mocks.hass_functions['notify'].assert_called_with(message="test", name="html5")

def test_select_option(given_that, with_extra_hass_functions, hass_mocks):
    with_extra_hass_functions.call_select_option()
    hass_mocks.hass_functions['select_option'].assert_called_with("select_item", "value")