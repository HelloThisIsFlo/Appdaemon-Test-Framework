import textwrap
from abc import ABC, abstractmethod


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

    def __repr__(self):
        return "'ANY_DOMAIN" + self.service + "'"


class AnyString:
    def __eq__(self, other):
        return isinstance(other, str)


assert 'somedomain/my_service' == ServiceOnAnyDomain('my_service')
assert 'asdfasdf' == AnyString()


######################################################################


### Custom Exception #################################################
class EitherOrAssertionError(AssertionError):
    def __init__(self, first_assertion_error, second_assertion_error):
        message = '\n'.join([
            '',
            '',
            'At least ONE of the following exceptions should not have been raised',
            '',
            'The problem is EITHER:',
            str(first_assertion_error),
            '',
            'OR',
            str(second_assertion_error)])

        super(EitherOrAssertionError, self).__init__(message)


######################################################################


class Was(ABC):
    @abstractmethod
    def turned_on(self, **service_specific_parameters):
        pass

    @abstractmethod
    def turned_off(self):
        pass

    @abstractmethod
    def called_with(self, **kwargs):
        pass

    def called(self):
        self.called_with()


class WasWrapper(Was):
    def __init__(self, thing_to_check, hass_functions):
        self.thing_to_check = thing_to_check
        self.hass_functions = hass_functions

    def turned_on(self, **service_specific_parameters):
        """ Assert that a given entity_id has been turned on """
        entity_id = self.thing_to_check

        service_not_called = _capture_assert_failure_exception(
            lambda: self.hass_functions['call_service'].assert_any_call(
                ServiceOnAnyDomain('turn_on'),
                **{'entity_id': entity_id, **service_specific_parameters}))

        turn_on_helper_not_called = _capture_assert_failure_exception(
            lambda: self.hass_functions['turn_on'].assert_any_call(
                entity_id,
                **service_specific_parameters))

        if service_not_called and turn_on_helper_not_called:
            raise EitherOrAssertionError(
                service_not_called, turn_on_helper_not_called)

    def turned_off(self, **service_specific_parameters):
        """ Assert that a given entity_id has been turned off """
        entity_id = self.thing_to_check

        service_not_called = _capture_assert_failure_exception(
            lambda: self.hass_functions['call_service'].assert_any_call(
                ServiceOnAnyDomain('turn_off'),
                **{'entity_id': entity_id, **service_specific_parameters}))

        turn_off_helper_not_called = _capture_assert_failure_exception(
            lambda: self.hass_functions['turn_off'].assert_any_call(
                entity_id,
                **service_specific_parameters))

        if service_not_called and turn_off_helper_not_called:
            raise EitherOrAssertionError(
                service_not_called, turn_off_helper_not_called)

    def called_with(self, **kwargs):
        """ Assert that a given service has been called with the given arguments"""
        service_full_name = self.thing_to_check

        self.hass_functions['call_service'].assert_any_call(
            service_full_name, **kwargs)


class WasNotWrapper(Was):
    def __init__(self, was_wrapper):
        self.was_wrapper = was_wrapper

    def turned_on(self, **service_specific_parameters):
        """ Assert that a given entity_id has NOT been turned ON w/ the given parameters"""
        thing_not_turned_on_with_given_params = _capture_assert_failure_exception(
            lambda: self.was_wrapper.turned_on(**service_specific_parameters))

        if not thing_not_turned_on_with_given_params:
            raise AssertionError(
                "Should NOT have been turned ON w/ the given params: "
                + str(self.was_wrapper.thing_to_check))

    def turned_off(self, **service_specific_parameters):
        """ Assert that a given entity_id has NOT been turned OFF """
        thing_not_turned_off = _capture_assert_failure_exception(
            lambda: self.was_wrapper.turned_off(**service_specific_parameters))

        if not thing_not_turned_off:
            raise AssertionError(
                "Should NOT have been turned OFF: "
                + str(self.was_wrapper.thing_to_check))

    def called_with(self, **kwargs):
        """ Assert that a given service has NOT been called with the given arguments"""
        service_not_called = _capture_assert_failure_exception(
            lambda: self.was_wrapper.called_with(**kwargs))

        if not service_not_called:
            raise AssertionError(
                "Service shoud NOT have been called with the given args: " + str(kwargs))


class ListensToWrapper:
    def __init__(self, automation_thing_to_check, hass_functions):
        self.automation_thing_to_check = automation_thing_to_check
        self.listen_event = hass_functions['listen_event']
        self.listen_state = hass_functions['listen_state']

    def event(self, event, **event_data):
        listens_to_wrapper = self

        class WithCallbackWrapper:
            def with_callback(self, callback):
                listens_to_wrapper.automation_thing_to_check.initialize()
                listens_to_wrapper.listen_event.assert_any_call(
                    callback,
                    event,
                    **event_data)

        return WithCallbackWrapper()

    def state(self, entity_id, **listen_state_opts):
        listens_to_wrapper = self

        class WithCallbackWrapper:
            def with_callback(self, callback):
                listens_to_wrapper.automation_thing_to_check.initialize()
                listens_to_wrapper.listen_state.assert_any_call(
                    callback,
                    entity_id,
                    **listen_state_opts)

        return WithCallbackWrapper()


class RegisteredWrapper:
    def __init__(self, automation_thing_to_check, hass_functions):
        self.automation_thing_to_check = automation_thing_to_check
        self._run_daily = hass_functions['run_daily']
        self._run_mintely = hass_functions['run_minutely']
        self._run_at = hass_functions['run_at']


    def run_daily(self, time_, **kwargs):
        registered_wrapper = self

        class WithCallbackWrapper:
            def with_callback(self, callback):
                registered_wrapper.automation_thing_to_check.initialize()
                registered_wrapper._run_daily.assert_any_call(
                    callback,
                    time_,
                    **kwargs)

        return WithCallbackWrapper()

    def run_minutely(self, time_, **kwargs):
        registered_wrapper = self

        class WithCallbackWrapper:
            def with_callback(self, callback):
                registered_wrapper.automation_thing_to_check.initialize()
                registered_wrapper._run_mintely.assert_any_call(
                    callback,
                    time_,
                    **kwargs)

        return WithCallbackWrapper()

    def run_at(self, time_, **kwargs):
        registered_wrapper = self

        class WithCallbackWrapper:
            def with_callback(self, callback):
                registered_wrapper.automation_thing_to_check.initialize()
                registered_wrapper._run_at.assert_any_call(
                    callback,
                    time_,
                    **kwargs)

        return WithCallbackWrapper()


NOT_INIT_ERROR = textwrap.dedent("""\
        AssertThat has not been initialized!

        Call `assert_that(THING_TO_CHECK).was.ASSERTION`
        And NOT `assert_that.was.ASSERTION`
        """)


def _ensure_init(property):
    if property is None:
        raise Exception(NOT_INIT_ERROR)
    return property


class AssertThatWrapper:
    def __init__(self, hass_mocks):
        # Access the `_hass_functions` through private member for now to avoid genearting deprecation
        # warnings while keeping compatibility.
        self.hass_functions = hass_mocks._hass_functions
        self._was = None
        self._was_not = None
        self._listens_to = None
        self._registered = None

    def __call__(self, thing_to_check):
        self._was = WasWrapper(thing_to_check, self.hass_functions)
        self._was_not = WasNotWrapper(self.was)
        self._listens_to = ListensToWrapper(thing_to_check, self.hass_functions)
        self._registered = RegisteredWrapper(thing_to_check, self.hass_functions)
        return self

    @property
    def was(self):
        return _ensure_init(self._was)

    @property
    def was_not(self):
        return _ensure_init(self._was_not)

    @property
    def listens_to(self):
        return _ensure_init(self._listens_to)

    @property
    def registered(self):
        return _ensure_init(self._registered)


def _capture_assert_failure_exception(function_with_assertion):
    """ Returns wether the assertion was successful or not. But does not throw """
    try:
        function_with_assertion()
        return None
    except AssertionError as failed_assert:
        return failed_assert
