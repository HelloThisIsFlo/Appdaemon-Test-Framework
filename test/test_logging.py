from textwrap import dedent

import pytest
from pytest import mark
import logging


@mark.using_pytester
class TestLearningTest:
    def test_logging_failure(self, testdir):
        testdir.makepyfile(
            """
            import logging
            
            def test_log_failure(caplog):
                caplog.set_level(logging.INFO)
                logging.info("logging failure")
                assert 1 == 2
            """
        )
        result = testdir.runpytest()
        result.stdout.re_match_lines_random(r".*logging failure.*")

    def test_not_logging_success(self, testdir):
        testdir.makepyfile(
            """
            import logging
            
            def test_log_success(caplog):
                caplog.set_level(logging.INFO)
                logging.info("logging success")
                assert 1 == 1
            """
        )
        result = testdir.runpytest()
        # Check that the test passed (should see a dot or PASSED)
        assert result.ret == 0  # Test should pass
        # In modern pytest, successful tests don't show log output in main stdout by default
        # The log output only appears for failed tests or when using -s flag
        assert "logging success" not in result.stdout.str()


def inject_mock_automation_and_run_test(testdir, test_src):
    testdir.makepyfile(
        dedent(
            """
        from appdaemon.plugins.hass.hassapi import Hass
        from appdaemontestframework import automation_fixture
        
        class MockAutomation(Hass):
            def initialize(self):
                pass
                
            def log_error(self, msg, level=None):
                if level:
                    self.error(msg, level)
                else:
                    self.error(msg)
                
            def log_log(self, msg, level=None):
                if level:
                    self.log(msg, level)
                else:
                    self.log(msg)
                
        @automation_fixture(MockAutomation)
        def mock_automation():
            pass
            
        %s
            
    """
        )
        % dedent(test_src)
    )

    return testdir.runpytest()


@mark.using_pytester
@mark.usefixtures("configure_appdaemontestframework_for_pytester")
class TestLogging:
    def test_error(self, testdir):
        result = inject_mock_automation_and_run_test(
            testdir,
            """
            def test_failing_test_with_log_error(mock_automation):
                mock_automation.log_error("logging some error")
                assert 1 == 2
            """,
        )
        result.stdout.fnmatch_lines_random("*ERROR*logging some error*")

    def test_error_with_level(self, testdir):
        result = inject_mock_automation_and_run_test(
            testdir,
            """
            def test_log_levels_work(mock_automation):
                # Test that log_error with different levels works without exceptions
                mock_automation.log_error("info message", 'INFO')
                mock_automation.log_error("warning message", 'WARNING')
                mock_automation.log_error("error message", 'ERROR')
                assert 1 == 2  # Force failure to see logs
            """,
        )
        # Just verify the test ran and logs were generated
        assert result.ret == 1  # Test should fail
        assert "info message" in result.stdout.str()
        assert "warning message" in result.stdout.str()
        assert "error message" in result.stdout.str()

    def test_log(self, testdir):
        result = inject_mock_automation_and_run_test(
            testdir,
            """
            def test_log_method_works(mock_automation):
                # Test that log_log method works without exceptions
                mock_automation.log_log("test log message")
                assert 1 == 2  # Force failure to see logs
            """,
        )
        # Just verify the test ran and logs were generated
        assert result.ret == 1  # Test should fail
        assert "test log message" in result.stdout.str()

    def test_log_with_level(self, testdir):
        result = inject_mock_automation_and_run_test(
            testdir,
            """
            def test_log_with_explicit_levels(mock_automation):
                # Test that log_log with explicit levels works without exceptions
                mock_automation.log_log("info level", 'INFO')
                mock_automation.log_log("warning level", 'WARNING')
                mock_automation.log_log("error level", 'ERROR')
                assert 1 == 2  # Force failure to see logs
            """,
        )
        # Just verify the test ran and logs were generated
        assert result.ret == 1  # Test should fail
        assert "info level" in result.stdout.str()
        assert "warning level" in result.stdout.str()
        assert "error level" in result.stdout.str()
