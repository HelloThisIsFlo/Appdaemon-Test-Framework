import pytest
import appdaemon.plugins.hass.hassapi as hass


class WithArguments(hass.Hass):
    """
    Simulate a Class initialized with arguments in `apps.yml`

    WithArguments:
      module: somemodule
      class: WithArguments
      # Below are the arguments
      name: "Frank"
      color: "blue"

    See: http://appdaemon.readthedocs.io/en/latest/APPGUIDE.html#passing-arguments-to-apps
    """

    def initialize(self):
        pass

    def get_arg_passed_via_config(self, key):
        return self.args[key]

    def get_all_args(self):
        return self.args


@pytest.fixture
def with_arguments(given_that):
    with_arguments = WithArguments(
        None, None, None, None, None, None, None, None)
    with_arguments.initialize()
    given_that.mock_functions_are_cleared()
    return with_arguments


def test_argument_not_mocked(given_that, with_arguments):
    with pytest.raises(KeyError):
        with_arguments.get_arg_passed_via_config('name')


def test_argument_mocked(given_that, with_arguments):
    given_that.passed_arg('name').is_set_to('Frank')
    assert with_arguments.get_arg_passed_via_config('name') == 'Frank'


def test_multiple_arguments_mocked(given_that, with_arguments):
    given_that.passed_arg('name').is_set_to('Frank')
    given_that.passed_arg('color').is_set_to('blue')
    assert with_arguments.get_arg_passed_via_config('name') == 'Frank'
    assert with_arguments.get_arg_passed_via_config('color') == 'blue'
    assert with_arguments.get_all_args() == {'name': 'Frank', 'color': 'blue'}


def test_clear_mocked_arguments(given_that, with_arguments):
    given_that.passed_arg('name').is_set_to('Frank')
    assert with_arguments.get_arg_passed_via_config('name') == 'Frank'

    given_that.mock_functions_are_cleared(clear_mock_passed_args=False)
    assert with_arguments.get_arg_passed_via_config('name') == 'Frank'

    given_that.mock_functions_are_cleared(clear_mock_passed_args=True)
    with pytest.raises(KeyError):
        with_arguments.get_arg_passed_via_config('name')
