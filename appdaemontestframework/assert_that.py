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
                {'entity_id': entity_id, **service_specific_parameters}))

        turn_on_helper_not_called = _capture_assert_failure_exception(
            lambda: self.hass_functions['turn_on'].assert_any_call(
                entity_id,
                **service_specific_parameters))

        if service_not_called and turn_on_helper_not_called:
            raise EitherOrAssertionError(
                service_not_called, turn_on_helper_not_called)

    def turned_off(self):
        """ Assert that a given entity_id has been turned off """
        entity_id = self.thing_to_check

        service_not_called = _capture_assert_failure_exception(
            lambda: self.hass_functions['call_service'].assert_any_call(
                ServiceOnAnyDomain('turn_off'),
                entity_id=entity_id))

        turn_off_helper_not_called = _capture_assert_failure_exception(
            lambda: self.hass_functions['turn_off'].assert_any_call(
                entity_id))

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

    def turned_off(self):
        """ Assert that a given entity_id has NOT been turned OFF """
        thing_not_turned_off = _capture_assert_failure_exception(
            lambda: self.was_wrapper.turned_off())

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

NOT_INIT_ERROR = textwrap.dedent("""\
        AssertThat has not been initialized!

        Call `assert_that(THING_TO_CHECK).was.ASSERTION`
        And NOT `assert_that.was.ASSERTION`
        """)
class AssertThatWrapper:
    def __init__(self, hass_functions):
        self.hass_functions = hass_functions
        self._was = None
        self._was_not = None

    def __call__(self, thing_to_check):
        self._was = WasWrapper(thing_to_check, self.hass_functions)
        self._was_not = WasNotWrapper(self.was)
        return self

    @property
    def was(self):
        if self._was is None:
            raise NOT_INIT_ERROR
        return self._was

    @property
    def was_not(self):
        if self._was_not is None:
            raise Exception(NOT_INIT_ERROR)
        return self._was_not


def _capture_assert_failure_exception(function_with_assertion):
    """ Returns wether the assertion was successful or not. But does not throw """
    try:
        function_with_assertion()
        return None
    except AssertionError as failed_assert:
        return failed_assert
