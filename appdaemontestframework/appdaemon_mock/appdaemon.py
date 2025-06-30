import asyncio
import pytz
import threading


class MockAppDaemon:
    """Implementation of appdaemon's internal AppDaemon class suitable for testing"""

    def __init__(self, **kwargs):

        #
        # Import various AppDaemon bits and pieces now to avoid circular import
        #

        from appdaemontestframework.appdaemon_mock.scheduler import MockScheduler

        # Use UTC timezone just for testing.
        self.tz = pytz.timezone("UTC")

        self.sched = MockScheduler(self)

        # Add main_thread_id for compatibility with newer Appdaemon versions
        self.main_thread_id = threading.current_thread().ident
