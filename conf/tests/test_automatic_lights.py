from apps.automatic_lights import KitchenLight
import pytest
from mock import patch, MagicMock
from apps.entity_ids import ID


@pytest.fixture
def kitchen_light(given_that):
    kitchen_light = KitchenLight(
        None, None, None, None, None, None, None, None)
    kitchen_light.initialize()

    given_that.mock_functions_are_cleared()
    return kitchen_light

@pytest.fixture
def when_new(kitchen_light):
    class WhenNewWrapper:
        def motion(self):
            kitchen_light._new_motion(None, None, None)

        def no_more_motion(self):
            kitchen_light._no_more_motion(
                None,  None, None, None, None)

    return WhenNewWrapper()

def test_turn_on(when_new, assert_that):
    when_new.motion()
    assert_that(ID['kitchen']['light']).was.turned_on()

def test_turn_off(when_new, assert_that):
    when_new.no_more_motion()
    assert_that(ID['kitchen']['light']).was.turned_off()
