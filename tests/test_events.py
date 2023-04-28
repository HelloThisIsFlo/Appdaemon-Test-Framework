from appdaemon.plugins.hass.hassapi import Hass

from appdaemontestframework import automation_fixture

LIGHT = 'light.some_light'
COVER = 'cover.some_cover'


class MockAutomation(Hass):
    def initialize(self):
        pass

    def send_event(self):
        self.fire_event("SOME_EVENT", my_keyword="hello")


@automation_fixture(MockAutomation)
def automation():
    pass


def test_it_does_not_crash_when_testing_automation_that_sends_events(given_that,
                                                                     automation: MockAutomation):
    # For now, there is not assertion feature on events, so we're just ensuring
    # appdaemontestframework is not crashing when testing an automation that
    # sends events.
    automation.send_event()
