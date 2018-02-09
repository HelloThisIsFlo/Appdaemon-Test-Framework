from apps.smart_bathroom import SmartBathroom
from appdaemon.plugins.hass.hassapi import Hass
from mock import patch, MagicMock
import pytest
from datetime import time

@pytest.fixture
def smart_bathroom(hass_functions):
    smart_bathroom = SmartBathroom(None, None, None, None, None, None, None, None)
    # Set initial time to 3PM
    hass_functions['time'].return_value = time(hour=15)
    smart_bathroom.initialize()
    return smart_bathroom

@pytest.fixture
def trigger(smart_bathroom):
    class Trigger:
        def __init__(self, smart_bathroom):
            self.smart_bathroom = smart_bathroom
        def new_time(self, hour=None):
            self.smart_bathroom._time_triggered(hour=hour)
        def new_motion_bathroom(self):
            self.smart_bathroom._new_motion_bathroom(None, None, None)
        def new_motion_kitchen(self):
            self.smart_bathroom._new_motion_kitchen(None, None, None)
        def new_motion_living_room(self):
            self.smart_bathroom._new_motion_living_room(None, None, None)
    return Trigger(smart_bathroom)


# def test_the_fixtures(smart_bathroom, trigger):
#     print(trigger)
#     assert 0
