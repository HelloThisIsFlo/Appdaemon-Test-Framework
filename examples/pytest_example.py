import pytest
from myrooms import LivingRoom

# Important:
# For this example to work, do not forget to copy the `conftest.py` file.
# See README.md for more info

@pytest.fixture
def living_room(given_that):
    living_room = LivingRoom(None, None, None, None, None, None, None, None)
    living_room.initialize()
    given_that.mock_functions_are_cleared()
    return living_room


def test_during_night_light_turn_on(given_that, living_room, assert_that):
    given_that.state_of('sensor.living_room_illumination').is_set_to(200) # 200lm == night
    living_room._new_motion(None, None, None)
    assert_that('light.living_room').was.turned_on()

def test_during_day_light_DOES_NOT_turn_on(given_that, living_room, assert_that):
    given_that.state_of('sensor.living_room_illumination').is_set_to(1000) # 1000lm == sunlight
    living_room._new_motion(None, None, None)
    assert_that('light.living_room').was_not.turned_on()
