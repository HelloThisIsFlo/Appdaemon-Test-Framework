import pytest
import mock
from appdaemon.plugins.hass.hassapi import Hass


### Custom Matchers ##################################################
class ServiceOnAnyDomain:
    def __init__(self, service):
        self.service = ''.join(['/', service])
    # Turn on service look like: 'DOMAIN/SERVICE'
    # We just check that the SERVICE part is equal

    def __eq__(self, other):
        """ 
        Turn on service look like: 'DOMAIN/SERVICE'
        We just check that the SERVICE part is equal
        """
        return self.service in other


class AnyString:
    def __eq__(self, other):
        return isinstance(other, str)


assert 'somedomain/my_service' == ServiceOnAnyDomain('my_service')
assert 'asdfasdf' == AnyString()
######################################################################


@pytest.fixture
def hass_functions(request):
    # Patch the __init__ method to skip Hass initialisation
    patch___init__ = mock.patch.object(Hass, '__init__')
    patched___init__ = patch___init__.__enter__()
    patched___init__.return_value = None

    # Patching the Hass functions
    # And returning a dict of their mocks
    patch_log = mock.patch.object(Hass, 'log')
    patch_time = mock.patch.object(Hass, 'time')
    patch_run_daily = mock.patch.object(Hass, 'run_daily')
    patch_listen_event = mock.patch.object(Hass, 'listen_event')
    patch_listen_state = mock.patch.object(Hass, 'listen_state')
    patch_call_service = mock.patch.object(Hass, 'call_service')
    patch_turn_on = mock.patch.object(Hass, 'turn_on')
    patch_turn_off = mock.patch.object(Hass, 'turn_off')

    patched_log = patch_log.__enter__()
    patched_time = patch_time.__enter__()
    patched_run_daily = patch_run_daily.__enter__()
    patched_listen_event = patch_listen_event.__enter__()
    patched_listen_state = patch_listen_state.__enter__()
    patched_call_service = patch_call_service.__enter__()
    patched_turn_on = patch_turn_on.__enter__()
    patched_turn_off = patch_turn_off.__enter__()

    def unpatch():
        patch___init__.__exit__()
        patch_log.__exit__()
        patch_time.__exit__()
        patch_run_daily.__exit__()
        patch_listen_event.__exit__()
        patch_listen_state.__exit__()
        patch_call_service.__exit__()
        patch_turn_off.__exit__()
        patch_turn_on.__exit__()

    request.addfinalizer(unpatch)

    return {
        'log': patched_log,
        'time': patched_time,
        'run_daily': patched_run_daily,
        'listen_event': patched_listen_event,
        'listen_state': patched_listen_state,
        'call_service': patched_call_service,
        'turn_on': patched_turn_on,
        'turn_off': patched_turn_off
    }


class HassAssertionWrapper:
    def __init__(self, thing_to_check, hass_functions):
        self.thing_to_check = thing_to_check
        self.hass_functions = hass_functions

    def was_turned_on(self, color_name=AnyString()):
        """ Assert that a given entity_id has been turned on """
        entity_id = self.thing_to_check

        service_called = True
        turn_on_helper_called = True
        try:
            self.hass_functions['call_service'].assert_called_once_with(
                ServiceOnAnyDomain('turn_on'),
                entity_id=entity_id,
                color_name=color_name)
        except AssertionError:
            service_called = False
        try:
            self.hass_functions['turn_on'].assert_called_once_with(
                entity_id,
                color_name=color_name)
        except AssertionError:
            turn_on_helper_called = False
        if not service_called and not turn_on_helper_called:
            raise AssertionError(
                ''.join([entity_id, ' was NOT turned on!']))

    def was_turned_off(self):
        """ Assert that a given entity_id has been turned off """
        entity_id = self.thing_to_check
        service_called = True
        turn_off_helper_called = True
        try:
            self.hass_functions['call_service'].assert_called_once_with(
                ServiceOnAnyDomain('turn_off'),
                entity_id=entity_id)
        except AssertionError:
            service_called = False
        try:
            self.hass_functions['turn_off'].assert_called_once_with(
                entity_id)
        except AssertionError:
            turn_off_helper_called = False
        if not service_called and not turn_off_helper_called:
            raise AssertionError(
                ''.join([entity_id, ' was NOT turned off!']))
    
    def was_called_with(self, **kwargs):
        """ Assert that a given service has been called with the given arguments"""
        service_full_name = self.thing_to_check

        self.hass_functions['call_service'].assert_called_once_with(service_full_name, **kwargs)



@pytest.fixture
def assert_that(hass_functions):
    def assert_that(thing_to_check):
        return HassAssertionWrapper(thing_to_check, hass_functions)
    return assert_that
