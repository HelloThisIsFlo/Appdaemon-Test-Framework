import pytest
import mock
from appdaemon.plugins.hass.hassapi import Hass

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

    patched_log = patch_log.__enter__()
    patched_time = patch_time.__enter__() 
    patched_run_daily = patch_run_daily.__enter__() 
    patched_listen_event = patch_listen_event.__enter__() 
    patched_listen_state = patch_listen_state.__enter__() 

    def unpatch():
        patch___init__.__exit__()
        patch_log.__exit__()
        patch_time.__exit__() 
        patch_run_daily.__exit__() 
        patch_listen_event.__exit__() 
        patch_listen_state.__exit__() 
    
    request.addfinalizer(unpatch)

    return {
        'log': patched_log,
        'time': patched_time,
        'run_daily': patched_run_daily,
        'listen_event': patched_listen_event,
        'listen_state': patched_listen_state
    }