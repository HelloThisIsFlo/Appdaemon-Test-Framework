from textwrap import dedent

import pytest
from pytest import mark


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
            """)
        result = testdir.runpytest()
        result.stdout.re_match_lines_random(r'.*logging failure.*')

    def test_not_logging_success(self, testdir):
        testdir.makepyfile(
            """
            import logging
            
            def test_log_success(caplog):
                caplog.set_level(logging.INFO)
                logging.info("logging success")
                assert 1 == 1
            """)
        result = testdir.runpytest()
        with pytest.raises(ValueError):
            result.stdout.re_match_lines_random(r'.*logging success.*')


def inject_mock_automation_and_run_test(testdir, test_src):
    testdir.makepyfile(dedent(
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
            
    """) % dedent(test_src))

    return testdir.runpytest()


@mark.using_pytester
@mark.usefixtures('configure_appdaemontestframework_for_pytester')
class TestLogging:
    def test_error(self, testdir):
        result = inject_mock_automation_and_run_test(
            testdir,
            """
            def test_failing_test_with_log_error(mock_automation):
                mock_automation.log_error("logging some error")
                assert 1 == 2
            """)
        result.stdout.fnmatch_lines_random('*ERROR*logging some error*')

    def test_error_with_level(self, testdir):
        result = inject_mock_automation_and_run_test(
            testdir,
            """
            def test_log_level_not_set__info(mock_automation):
                mock_automation.log_error("should not show", 'INFO')
                assert 1 == 2
                
            def test_log_level_not_set__warning(mock_automation):
                mock_automation.log_error("should show", 'WARNING')
                assert 1 == 2
                
            def test_log_level_set_to_info(mock_automation, caplog):
                import logging
                caplog.set_level(logging.INFO)
                mock_automation.log_error("should show", 'INFO')
                assert 1 == 2
            """)
        with pytest.raises(ValueError):
            result.stdout.fnmatch_lines_random('*INFO*should not show*')
        result.stdout.fnmatch_lines_random('*INFO*should show*')

    def test_log(self, testdir):
        result = inject_mock_automation_and_run_test(
            testdir,
            """
            def test_log_level_not_set(mock_automation):
                mock_automation.log_log("should not show")
                assert 1 == 2
                
            def test_log_level_set_to_info(mock_automation, caplog):
                import logging
                caplog.set_level(logging.INFO)
                mock_automation.log_log("should show")
                assert 1 == 2
            """)

        with pytest.raises(ValueError):
            result.stdout.fnmatch_lines_random('*INFO*should not show*')
        result.stdout.fnmatch_lines_random('*INFO*should show*')

    def test_log_with_level(self, testdir):
        result = inject_mock_automation_and_run_test(
            testdir,
            """
            def test_log_level_not_set__info(mock_automation):
                mock_automation.log_log("should not show", 'INFO')
                assert 1 == 2
                
            def test_log_level_not_set__warning(mock_automation):
                mock_automation.log_log("should show", 'WARNING')
                assert 1 == 2
                
            def test_log_level_set_to_info(mock_automation, caplog):
                import logging
                caplog.set_level(logging.INFO)
                mock_automation.log_log("should show", 'INFO')
                assert 1 == 2
            """)
        with pytest.raises(ValueError):
            result.stdout.fnmatch_lines_random('*INFO*should not show*')
        result.stdout.fnmatch_lines_random('*INFO*should show*')
        result.stdout.fnmatch_lines_random('*WARNING*should show*')
