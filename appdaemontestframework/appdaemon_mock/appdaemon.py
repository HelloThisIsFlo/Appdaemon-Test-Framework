import asyncio
import pytz

class AppDaemon:
    """Implementation of appdaemon's internal AppDaemon class suitable for testing"""
    def __init__(self, logging, loop, **kwargs):

        #
        # Import various AppDaemon bits and pieces now to avoid circular import
        #

        from appdaemontestframework.appdaemon_mock.sccheduler import Scheduler

        # Use UTC timezone just for testing.
        self.tz = pytz.timezone('UTC')

        self.sched = Scheduler(self)

