import appdaemon.plugins.hass.hassapi as hass

from appdaemontestframework import automation_fixture

COVER = 'cover.some_cover'

class WithMiscellaneousHelperFunctions(hass.Hass):
    def initialize(self):
        pass

    def get_entity_exists(self, entity):
        return self.entity_exists(entity)

@automation_fixture(WithMiscellaneousHelperFunctions)
def with_miscellaneous_helper_functions():
    pass


def test_entity_exists_true(given_that, with_miscellaneous_helper_functions, hass_functions):
    given_that.state_of(COVER).is_set_to("closed", {'friendly_name': f"{COVER}", 'current_position': 0})
    assert with_miscellaneous_helper_functions.get_entity_exists(COVER)==True

def test_entity_exists_false(given_that, with_miscellaneous_helper_functions, hass_functions):
    assert with_miscellaneous_helper_functions.get_entity_exists("not_existent_entity")==False
