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


class AssertThatWrapper:
    def __init__(self, thing_to_check, hass_functions):
        self.thing_to_check = thing_to_check
        self.hass_functions = hass_functions

    def was_turned_on(self, **service_specific_parameters):
        """ Assert that a given entity_id has been turned on """
        entity_id = self.thing_to_check

        service_not_called = self._capture_assert_result(
            lambda: self.hass_functions['call_service'].assert_any_call(
                ServiceOnAnyDomain('turn_on'),
                {'entity_id': entity_id, **service_specific_parameters}))

        turn_on_helper_not_called = self._capture_assert_result(
            lambda: self.hass_functions['turn_on'].assert_any_call(
                entity_id,
                **service_specific_parameters))

        if service_not_called and turn_on_helper_not_called:
            raise EitherOrAssertionError(
                service_not_called, turn_on_helper_not_called)

    def was_turned_off(self):
        """ Assert that a given entity_id has been turned off """
        entity_id = self.thing_to_check

        service_not_called = self._capture_assert_result(
            lambda: self.hass_functions['call_service'].assert_any_call(
                ServiceOnAnyDomain('turn_off'),
                entity_id=entity_id))

        turn_off_helper_not_called = self._capture_assert_result(
            lambda: self.hass_functions['turn_off'].assert_any_call(
                entity_id))

        if service_not_called and turn_off_helper_not_called:
            raise EitherOrAssertionError(
                service_not_called, turn_off_helper_not_called)

    def _capture_assert_result(self, function_with_assertion):
        """ Returns wether the assertion was successful or not. But does not throw """
        try:
            function_with_assertion()
            return None
        except AssertionError as failed_assert:
            return failed_assert

    def was_called_with(self, **kwargs):
        """ Assert that a given service has been called with the given arguments"""
        service_full_name = self.thing_to_check

        self.hass_functions['call_service'].assert_called_once_with(
            service_full_name, **kwargs)
