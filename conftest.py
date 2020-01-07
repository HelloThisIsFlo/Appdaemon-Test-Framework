from appdaemontestframework.pytest_conftest import *

@fixture
def configure_appdaemontestframework_for_pytester(testdir):
    """
    Extra test fixtue use for testing pytest runners.
    """
    testdir.makeconftest(
        """
        from appdaemontestframework.pytest_conftest import *
    """)
