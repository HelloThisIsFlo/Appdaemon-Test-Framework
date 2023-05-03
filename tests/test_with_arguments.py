import appdaemon.plugins.hass.hassapi as hass
import pytest

from appdaemontestframework import automation_fixture


class WithArguments(hass.Hass):
    """
    Simulate a Class initialized with arguments in `apps.yml`

    WithArguments:
      module: somemodule
      class: WithArguments
      # Below are the arguments
      name: "Frank"
      color: "blue"

    See: http://appdaemon.readthedocs.io/
    en/latest/APPGUIDE.html#passing-arguments-to-apps
    """

    def initialize(self):
        pass

    def get_arg_passed_via_config(self, key):
        return self.args[key]

    def get_all_args(self):
        return self.args


@automation_fixture(WithArguments)
def with_arguments(given_that):
    pass


def test_argument_not_mocked(given_that, with_arguments):
    with pytest.raises(KeyError):
        with_arguments.get_arg_passed_via_config("name")


def test_argument_mocked(given_that, with_arguments):
    given_that.passed_arg("name").is_set_to("Frank")
    assert with_arguments.get_arg_passed_via_config("name") == "Frank"


def test_multiple_arguments_mocked(given_that, with_arguments):
    given_that.passed_arg("name").is_set_to("Frank")
    given_that.passed_arg("color").is_set_to("blue")
    assert with_arguments.get_arg_passed_via_config("name") == "Frank"
    assert with_arguments.get_arg_passed_via_config("color") == "blue"
    assert with_arguments.get_all_args() == {"name": "Frank", "color": "blue"}


def test_clear_mocked_arguments(given_that, with_arguments):
    given_that.passed_arg("name").is_set_to("Frank")
    assert with_arguments.get_arg_passed_via_config("name") == "Frank"

    given_that.mock_functions_are_cleared(clear_mock_passed_args=False)
    assert with_arguments.get_arg_passed_via_config("name") == "Frank"

    given_that.mock_functions_are_cleared(clear_mock_passed_args=True)
    with pytest.raises(KeyError):
        with_arguments.get_arg_passed_via_config("name")


@pytest.fixture
def with_args(given_that):
    return WithArguments(
        None,
        "With Args",
        None,
        {"entity": "state"},
        None,
        None,
        None,
    )


def test_with_args(given_that, with_args):
    assert with_args.get_arg_passed_via_config("entity") == "state"


@pytest.fixture
def with_kwargs(given_that):
    return WithArguments(
        ad=None,
        name="With Keyword Args",
        logging=None,
        args={"entity": "state"},
        config=None,
        app_config=None,
        global_vars=None,
    )


def test_with_kwargs(with_kwargs):
    assert with_kwargs.get_arg_passed_via_config("entity") == "state"
