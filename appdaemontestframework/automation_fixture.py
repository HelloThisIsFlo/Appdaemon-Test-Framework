import warnings
from inspect import isfunction, signature
import pkg_resources

import pytest
from appdaemon.plugins.hass.hassapi import Hass

from appdaemontestframework.common import AppdaemonTestFrameworkError
from appdaemontestframework.hass_mocks import is_appdaemon_version_at_least


class AutomationFixtureError(AppdaemonTestFrameworkError):
    pass


def _instantiate_and_initialize_automation(function, automation_class, given_that, hass_functions, hass_mocks):
    _inject_helpers_and_call_function(function, given_that, hass_functions, hass_mocks)

    if is_appdaemon_version_at_least('4.0.0'):
        automation = automation_class(
                None,
                automation_class.__name__,
                None,
                None,
                None,
                None,
                None
        )
    else:
        automation = automation_class(
                None,
                automation_class.__name__,
                None,
                None,
                None,
                None,
                None,
                None
        )
    automation.initialize()
    given_that.mock_functions_are_cleared()
    return automation


def _inject_helpers_and_call_function(function, given_that, hass_functions, hass_mocks):
    injectable_fixtures = {
        'given_that': given_that,
        'hass_functions': hass_functions,
        'hass_mocks': hass_mocks,
    }

    def _check_valid(param):
        if param not in injectable_fixtures:
            raise AutomationFixtureError(
                f"'{param}' is not a valid fixture! | The only fixtures injectable in '@automation_fixture' are: {list(injectable_fixtures.keys())}")

        if param == 'hass_functions':
            warnings.warn(
                """
                Injecting `hass_functions` into automation fixtures is deprecated.
                Replace `hass_functions` with `hass_mocks` injections and access hass_functions with `hass_mocks.hass_functions`
                """,
                DeprecationWarning)


    args = []
    for param in signature(function).parameters:
        _check_valid(param)
        args.append(injectable_fixtures.get(param))

    function(*tuple(args))


def ensure_automation_is_valid(automation_class):
    def function_exist_in_automation_class(func_name):
        return func_name in dir(automation_class)

    def function_has_arguments_other_than_self(func_name):
        func_parameters = signature(getattr(automation_class, func_name)).parameters
        return list(func_parameters.keys()) != ["self"]

    def __init___was_overridden():
        return '__init__' in automation_class.__dict__

    # noinspection PyPep8Naming,SpellCheckingInspection
    def not_subclass_of_Hass():
        return not issubclass(automation_class, Hass)

    if not function_exist_in_automation_class('initialize'):
        raise AutomationFixtureError(
            f"'{automation_class.__name__}' has no 'initialize' function! Make sure you implemented it!")
    if function_has_arguments_other_than_self('initialize'):
        raise AutomationFixtureError(
            f"'{automation_class.__name__}' 'initialize' should have no arguments other than 'self'!")
    if __init___was_overridden():
        raise AutomationFixtureError(f"'{automation_class.__name__}' should not override '__init__'")
    if not_subclass_of_Hass():
        raise AutomationFixtureError(f"'{automation_class.__name__}' should be a subclass of 'Hass'")


class _AutomationFixtureDecoratorWithoutArgs:
    def __init__(self, automation_classes):
        self.automation_classes = automation_classes
        for automation in self.automation_classes:
            ensure_automation_is_valid(automation)

    def __call__(self, function):
        @pytest.fixture(params=self.automation_classes, ids=self._generate_id)
        def automation_fixture_with_initialisation(request, given_that, hass_functions, hass_mocks):
            automation_class = request.param
            return _instantiate_and_initialize_automation(function, automation_class, given_that, hass_functions, hass_mocks)

        return automation_fixture_with_initialisation

    def _generate_id(self, automation_classes):
        return automation_classes.__name__


class _AutomationFixtureDecoratorWithArgs:
    def __init__(self, automation_classes_with_args):
        self.automation_classes_with_args = automation_classes_with_args
        for automation, _args in self.automation_classes_with_args:
            ensure_automation_is_valid(automation)

    def __call__(self, function):
        @pytest.fixture(params=self.automation_classes_with_args, ids=self._generate_id)
        def automation_fixture_with_initialisation(request, given_that, hass_functions, hass_mocks):
            automation_class = request.param[0]
            automation_args = request.param[1]
            automation = _instantiate_and_initialize_automation(
                function, automation_class, given_that, hass_functions, hass_mocks)
            return (automation, automation_args)

        return automation_fixture_with_initialisation

    def _generate_id(self, automation_classes_with_args):
        return automation_classes_with_args[0].__name__


def automation_fixture(*args):
    """
    Decorator to seamlessly initialize and inject an automation fixture

    4 Versions:
     - Single Class:               @automation_fixture(MyAutomation)
     - Multiple Classes:           @automation_fixture(MyAutomation, MyOtherAutomation)
     - Single Class w/ params:     @automation_fixture((upstairs.Bedroom, {'motion': 'binary_sensor.bedroom_motion'}))
     - Multiple Classes w/ params: @automation_fixture(
                                       (upstairs.Bedroom, {'motion': 'binary_sensor.bedroom_motion'}),
                                       (upstairs.Bathroom, {'motion': 'binary_sensor.bathroom_motion'}),
                                   )

    When multiple classes are passed, tests will be generated for each automation.
    When using parameters, the injected object will be a tuple: `(Initialized_Automation, params)`

    # Pre-initialization setup
    All code in the `@automation_fixture` function will be executed before initializing the `automation_class`

    3 fixtures are injectable in `@automation_fixture`: 'given_that', 'hass_mocks' and 'hass_functions'
    'hass_functions' is deprecated in favor of 'hass_mocks'

    Examples:
    ```python
    @automation_fixture(Bathroom)
    def bathroom():
        pass
    # -> `Bathroom` automation will be initialized and available in tests as `bathroom`

    ---

    @automation_fixture(Bathroom)
    def bathroom(given_that):
        given_that.time_is(time(hour=13))

    # -> 1. `given_that.time_is(time(hour=13))` will be called
    # -> 2. `Bathroom` automation will be initialized and available in tests as `bathroom`

    ```

    Do not return anything, any returned object will be ignored

    """
    if not args or isfunction(args[0]):
        raise AutomationFixtureError(
            'Do not forget to pass the automation class(es) as argument')

    if type(args[0]) is not tuple:
        automation_classes = args
        return _AutomationFixtureDecoratorWithoutArgs(automation_classes)
    else:
        automation_classes_with_args = args
        return _AutomationFixtureDecoratorWithArgs(automation_classes_with_args)
