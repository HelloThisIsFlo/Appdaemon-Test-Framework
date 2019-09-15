import re
from textwrap import dedent

import pytest
from appdaemon.plugins.hass.hassapi import Hass
from pytest import mark, fixture


class MockAutomation(Hass):
    def __init__(self, ad, name, logger, error, args, config, app_config, global_vars):
        super().__init__(ad, name, logger, error, args, config, app_config, global_vars)
        self.was_created = True
        self.was_initialized = False

    def initialize(self):
        self.was_initialized = True


def expected_error_regex_was_found_in_stdout_lines(result, expected_error_regex):
    for line in result.outlines:
        if re.search(expected_error_regex, line):
            return True
    return False


@mark.using_pytester
@mark.usefixtures('configure_appdaemontestframework_for_pytester')
class TestAutomationFixture:
    def test_fixture_is_available_for_injection(self, testdir):
        testdir.makepyfile(
            """
            from appdaemon.plugins.hass.hassapi import Hass
            from appdaemontestframework import automation_fixture

            class MockAutomation(Hass):
                def initialize(self):
                    pass

            @automation_fixture(MockAutomation)
            def mock_automation():
                pass

            def test_is_injected_as_fixture(mock_automation):
                assert mock_automation is not None
        """)

        result = testdir.runpytest()
        result.assert_outcomes(passed=1)

    def test_automation_was_initialized(self, testdir):
        testdir.makepyfile(
            """
            from appdaemon.plugins.hass.hassapi import Hass
            from appdaemontestframework import automation_fixture

            class MockAutomation(Hass):
                was_initialized: False

                def initialize(self):
                    self.was_initialized = True


            @automation_fixture(MockAutomation)
            def mock_automation():
                pass

            def test_was_initialized(mock_automation):
                assert mock_automation.was_initialized
        """)

        result = testdir.runpytest()
        result.assert_outcomes(passed=1)

    def test_calls_to_appdaemon_during_initialize_are_cleared_before_entering_test(self, testdir):
        testdir.makepyfile(
            """
            from appdaemon.plugins.hass.hassapi import Hass
            from appdaemontestframework import automation_fixture

            class MockAutomation(Hass):
                def initialize(self):
                    self.turn_on('light.living_room')


            @automation_fixture(MockAutomation)
            def mock_automation():
                pass

            def test_some_test(mock_automation):
                assert mock_automation is not None

        """)

        result = testdir.runpytest()
        result.assert_outcomes(passed=1)

    def test_multiple_automations(self, testdir):
        testdir.makepyfile(
            """
            from appdaemon.plugins.hass.hassapi import Hass
            from appdaemontestframework import automation_fixture

            class MockAutomation(Hass):
                def initialize(self):
                    pass

            class OtherMockAutomation(Hass):
                def initialize(self):
                    pass


            @automation_fixture(MockAutomation, OtherMockAutomation)
            def mock_automation():
                pass

            def test_some_test(mock_automation):
                assert mock_automation is not None
        """)

        result = testdir.runpytest()
        result.assert_outcomes(passed=2)

    def test_given_that_fixture_is_injectable_in_automation_fixture(self, testdir):
        testdir.makepyfile(
            """
            from appdaemon.plugins.hass.hassapi import Hass
            from appdaemontestframework import automation_fixture

            class MockAutomation(Hass):
                def initialize(self):
                    pass

                def assert_light_on(self):
                    assert self.get_state('light.bed') == 'on'


            @automation_fixture(MockAutomation)
            def mock_automation(given_that):
                given_that.state_of('light.bed').is_set_to('on')

            def test_some_test(mock_automation):
                mock_automation.assert_light_on()
        """)

        result = testdir.runpytest()
        result.assert_outcomes(passed=1)

    def test_decorator_called_without_automation__raise_error(self, testdir):
        testdir.makepyfile(
            """
            from appdaemon.plugins.hass.hassapi import Hass
            from appdaemontestframework import automation_fixture

            class MockAutomation(Hass):
                def initialize(self):
                    pass

            @automation_fixture
            def mock_automation():
                pass

            def test_some_test(mock_automation):
                assert mock_automation is not None
        """)

        result = testdir.runpytest()
        result.assert_outcomes(error=1)
        assert expected_error_regex_was_found_in_stdout_lines(result, r"AutomationFixtureError.*argument")

    def test_name_attribute_of_hass_object_set_to_automation_class_name(self, testdir):
            testdir.makepyfile(
                """
                from appdaemon.plugins.hass.hassapi import Hass
                from appdaemontestframework import automation_fixture

                class MockAutomation(Hass):
                    def initialize(self):
                        pass

                @automation_fixture(MockAutomation)
                def mock_automation():
                    pass

                def test_name_attribute_of_hass_object_set_to_automation_class_name(mock_automation):
                    assert mock_automation.name == 'MockAutomation'
            """)

            result = testdir.runpytest()
            result.assert_outcomes(passed=1)

    class TestInvalidAutomation:
        @fixture
        def assert_automation_class_fails(self, testdir):
            def wrapper(automation_class_src, expected_error_regex):
                # Given: Test file with given automation class
                testdir.makepyfile(dedent(
                    """
                    from appdaemon.plugins.hass.hassapi import Hass
                    from appdaemontestframework import automation_fixture

                    %s

                    @automation_fixture(MockAutomation)
                    def mock_automation():
                        pass

                    def test_some_test(mock_automation):
                        assert mock_automation is not None
                """) % dedent(automation_class_src))

                # When: Running 'pytest'
                result = testdir.runpytest()

                # Then: Found 1 error & stdout has a line with expected error
                result.assert_outcomes(error=1)

                if not expected_error_regex_was_found_in_stdout_lines(result, expected_error_regex):
                    pytest.fail(f"Couldn't fine line matching error: '{expected_error_regex}'")

            return wrapper

        def test_automation_has_no_initialize_function(self, assert_automation_class_fails):
            assert_automation_class_fails(
                automation_class_src="""
                                     class MockAutomation(Hass):
                                         def some_other_function(self):
                                             self.turn_on('light.living_room')
                                     """,
                expected_error_regex=r"AutomationFixtureError: 'MockAutomation' .* no 'initialize' function")

        def test_initialize_function_has_arguments_other_than_self(self, assert_automation_class_fails):
            assert_automation_class_fails(
                automation_class_src="""
                                     class MockAutomation(Hass):
                                         def initialize(self, some_arg):
                                             self.turn_on('light.living_room')
                                     """,
                expected_error_regex=r"AutomationFixtureError: 'MockAutomation'.*"
                                     r"'initialize' should have no arguments other than 'self'")

        def test___init___was_overridden(self, assert_automation_class_fails):
            assert_automation_class_fails(
                automation_class_src="""
                                     class MockAutomation(Hass):
                                         def __init__(self, ad, name, logger, error, args, config, app_config, global_vars):
                                             super().__init__(ad, name, logger, error, args, config, app_config, global_vars)
                                             self.log("do some things in '__init__'")

                                         def initialize(self):
                                             self.turn_on('light.living_room')
                                     """,
                expected_error_regex=r"AutomationFixtureError: 'MockAutomation'.*should not override '__init__'")

        # noinspection PyPep8Naming,SpellCheckingInspection
        def test_not_a_subclass_of_Hass(self, assert_automation_class_fails):
            assert_automation_class_fails(
                automation_class_src="""
                                     class MockAutomation:
                                         def initialize(self):
                                            pass
                                     """,
                expected_error_regex=r"AutomationFixtureError: 'MockAutomation'.*should be a subclass of 'Hass'")

    class TestWithArgs:
        def test_automation_is_injected_with_args(self, testdir):
            testdir.makepyfile(
                """
                from appdaemon.plugins.hass.hassapi import Hass
                from appdaemontestframework import automation_fixture

                class MockAutomation(Hass):
                    def initialize(self):
                        pass


                @automation_fixture((MockAutomation, "some_arg"))
                def mock_automation_with_args():
                    pass

                def test_automation_was_injected_with_args(mock_automation_with_args):
                    automation = mock_automation_with_args[0]
                    arg = mock_automation_with_args[1]

                    assert isinstance(automation, MockAutomation)
                    assert arg == "some_arg"
            """)

            result = testdir.runpytest()
            result.assert_outcomes(passed=1)

        def test_multiple_automation_are_injected_with_args(self, testdir):
            testdir.makepyfile(
                """
                from appdaemon.plugins.hass.hassapi import Hass
                from appdaemontestframework import automation_fixture

                class MockAutomation(Hass):
                    def initialize(self):
                        pass

                class OtherAutomation(Hass):
                    def initialize(self):
                        pass


                @automation_fixture(
                    (MockAutomation, "some_arg"),
                    (OtherAutomation, "other_arg")
                )
                def mock_automation_with_args():
                    pass

                def test_automation_was_injected_with_args(mock_automation_with_args):
                    automation = mock_automation_with_args[0]
                    arg = mock_automation_with_args[1]

                    assert isinstance(automation, MockAutomation) or isinstance(automation, OtherAutomation)
                    assert arg == "some_arg" or arg == "other_arg"
            """)

            result = testdir.runpytest()
            result.assert_outcomes(passed=2)
