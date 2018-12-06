import mock
from appdaemon.plugins.hass.hassapi import Hass


def patch_hass():
    """
    Patch the Hass API and returns a tuple of:
    - The patched functions (as Dict)
    - A callback to un-patch all functions
    """
    #### Non-actionable functions ####
    # Patch the __init__ method to skip Hass initialisation
    patch___init__ = mock.patch.object(Hass, '__init__')
    patched___init__ = patch___init__.start()
    patched___init__.return_value = None
    # Path the log method
    patch_log = mock.patch.object(Hass, 'log')
    _patched_log = patch_log.start()

    #### Actionable functions ####
    # Callback registrations functions
    patch_run_daily = mock.patch.object(Hass, 'run_daily')
    patch_run_in = mock.patch.object(Hass, 'run_in')
    patch_listen_event = mock.patch.object(Hass, 'listen_event')
    patch_listen_state = mock.patch.object(Hass, 'listen_state')
    # State functions / attr
    patch_set_state = mock.patch.object(Hass, 'set_state')
    patch_get_state = mock.patch.object(Hass, 'get_state')
    patch_time = mock.patch.object(Hass, 'time')
    patch_passed_args = mock.patch.object(Hass, 'args', create=True)
    # Interactions functions
    patch_call_service = mock.patch.object(Hass, 'call_service')
    patch_turn_on = mock.patch.object(Hass, 'turn_on')
    patch_turn_off = mock.patch.object(Hass, 'turn_off')
    # Custom callback functions
    patch_register_constraint = mock.patch.object(Hass, 'register_constraint')

    ## Initialize patches
    patched_run_daily = patch_run_daily.start()
    patched_run_in = patch_run_in.start()
    patched_listen_event = patch_listen_event.start()
    patched_listen_state = patch_listen_state.start()
    patched_set_state = patch_set_state.start()
    patched_get_state = patch_get_state.start()
    patched_time = patch_time.start()
    patched_passed_args = patch_passed_args.start()
    patched_call_service = patch_call_service.start()
    patched_turn_on = patch_turn_on.start()
    patched_turn_off = patch_turn_off.start()
    patched_register_constraint = patch_register_constraint.start()

    ## Setup un-patch callback
    def unpatch_callback():
        patch___init__.stop()
        patch_log.stop()

        patch_run_daily.stop()
        patch_run_in.stop()
        patch_listen_event.stop()
        patch_listen_state.stop()
        patch_get_state.stop()
        patch_time.stop()
        patch_passed_args.stop()
        patch_call_service.stop()
        patch_turn_off.stop()
        patch_turn_on.stop()
        patch_register_constraint.stop()

    return ({
        'run_daily': patched_run_daily,
        'run_in': patched_run_in,
        'listen_event': patched_listen_event,
        'listen_state': patched_listen_state,
        'set_state': patched_set_state,
        'get_state': patched_get_state,
        'time': patched_time,
        'passed_args': patched_passed_args,
        'call_service': patched_call_service,
        'turn_on': patched_turn_on,
        'turn_off': patched_turn_off,
        'register_constraint': patched_register_constraint
    }, unpatch_callback)
