import unittest
from appdaemontestframework import patch_hass, GivenThatWrapper, AssertThatWrapper, TimeTravelWrapper
from myrooms import LivingRoom

# Important:
# This class is equivalent to the setup done in the `conftest.py` on the pytest version.
# Do not forget to inherint from it in all your XXXTestCase classes.
# See below in `LivingRoomTestCase`
class AppdaemonTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        patched_hass_functions, unpatch_callback = patch_hass()

        cls.given_that = GivenThatWrapper(patched_hass_functions)
        cls.assert_that = AssertThatWrapper(patched_hass_functions)
        cls.time_travel = TimeTravelWrapper(patched_hass_functions)

        cls.unpatch_callback = unpatch_callback

    @classmethod
    def tearDownClass(cls):
        cls.unpatch_callback()


class LivingRoomTestCase(AppdaemonTestCase):
    def setUp(self):
        self.living_room = LivingRoom(None, None, None, None, None, None, None, None)
        self.living_room.initialize()
        self.given_that.mock_functions_are_cleared()

    def test_during_night_light_turn_on(self):
        self.given_that.state_of('sensor.living_room_illumination').is_set_to(200) # 200lm == night
        self.living_room._new_motion(None, None, None)
        self.assert_that('light.living_room').was.turned_on()

    def test_during_day_light_DOES_NOT_turn_on(self):
        self.given_that.state_of('sensor.living_room_illumination').is_set_to(1000) # 1000lm == sun light
        self.living_room._new_motion(None, None, None)
        self.assert_that('light.living_room').was_not.turned_on()
