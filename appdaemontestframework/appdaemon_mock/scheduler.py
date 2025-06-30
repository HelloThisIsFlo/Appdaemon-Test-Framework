import datetime
import uuid
import pytz
import asyncio
import threading
from typing import Any, Callable, Optional
from appdaemontestframework.appdaemon_mock.appdaemon import MockAppDaemon


class MockScheduler:
    """Implement the AppDaemon Scheduler appropriate for testing and provide extra interfaces for adjusting the simulation"""

    def __init__(self, AD: MockAppDaemon):
        self.AD = AD
        self._registered_callbacks = []
        self._loop = None
        self._loop_thread = None

        # Default to Jan 1st, 2000 12:00AM
        # internal time is stored as a naive datetime in UTC
        self.sim_set_start_time(datetime.datetime(2000, 1, 1, 0, 0))

        # Initialize event loop for async operations
        self._ensure_event_loop()

    def _ensure_event_loop(self):
        """Ensure we have an event loop available for async operations"""
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, create our own
            self._loop = asyncio.new_event_loop()
            # Don't set as the running loop here to avoid conflicts

    def _run_async(self, coro):
        """Run an async coroutine in our event loop"""
        if self._loop is None:
            self._ensure_event_loop()

        try:
            # If we're already in an event loop context
            running_loop = asyncio.get_running_loop()
            if running_loop == self._loop:
                # We're already in our loop
                return asyncio.create_task(coro)
            else:
                # Different loop is running, use run_coroutine_threadsafe
                future = asyncio.run_coroutine_threadsafe(coro, self._loop)
                return future.result()
        except RuntimeError:
            # No running loop, we can use run_until_complete
            return self._loop.run_until_complete(coro)

    ### Implement the AppDaemon APIs for Scheduler
    async def get_now(self):
        """Return current localized naive datetime"""
        return self.get_now_sync()

    def get_now_sync(self):
        """Same as `get_now` but synchronous"""
        return pytz.utc.localize(self._now)

    async def get_now_ts(self):
        """Return the current localized timestamp"""
        return (await self.get_now()).timestamp()

    def get_now_ts_sync(self):
        """Synchronous version of get_now_ts"""
        return self.get_now_sync().timestamp()

    async def get_now_naive(self):
        return self.make_naive(await self.get_now())

    def get_now_naive_sync(self):
        """Synchronous version of get_now_naive"""
        return self.make_naive(self.get_now_sync())

    async def insert_schedule(self, name, aware_dt, callback, repeat, type_, **kwargs):
        naive_dt = self.make_naive(aware_dt)
        return self._queue_callback(callback, kwargs, naive_dt)

    def insert_schedule_sync(self, name, aware_dt, callback, repeat, type_, **kwargs):
        """Synchronous version of insert_schedule"""
        naive_dt = self.make_naive(aware_dt)
        return self._queue_callback(callback, kwargs, naive_dt)

    async def cancel_timer(self, name, handle):
        return self.cancel_timer_sync(name, handle)

    def cancel_timer_sync(self, name, handle):
        """Synchronous version of cancel_timer"""
        for callback in self._registered_callbacks:
            if callback.handle == handle:
                self._registered_callbacks.remove(callback)
                return True
        return False

    def convert_naive(self, dt):
        # Is it naive?
        result = None
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            # Localize with the configured timezone
            result = self.AD.tz.localize(dt)
        else:
            result = dt

        return result

    def make_naive(self, dt):
        local = dt.astimezone(self.AD.tz)
        return datetime.datetime(
            local.year,
            local.month,
            local.day,
            local.hour,
            local.minute,
            local.second,
            local.microsecond,
        )

    ### Test framework simulation functions
    def sim_set_start_time(self, time):
        """Set the absolute start time and set current time to that as well.
        if time is a datetime, it goes right to that.
        if time is time, it will set to that time with the current date.
        All dates/datetimes should be localized naive

        To guarantee consistency, you can not set the start time while any callbacks are scheduled.
        """
        if len(self._registered_callbacks) > 0:
            raise RuntimeError(
                "You can not set start time while callbacks are scheduled"
            )

        if type(time) == datetime.time:
            time = datetime.datetime.combine(self._now.date(), time)
        self._start_time = self._now = time

    def sim_get_start_time(self):
        """returns localized naive datetime of the start of the simulation"""
        return pytz.utc.localize(self._start_time)

    def sim_elapsed_seconds(self):
        """Returns number of seconds elapsed since the start of the simulation"""
        return (self._now - self._start_time).total_seconds()

    def sim_fast_forward(self, time):
        """Fastforward time and invoke callbacks. time can be a timedelta, time, or datetime (all should be localized naive)"""
        if type(time) == datetime.timedelta:
            target_datetime = self._now + time
        elif type(time) == datetime.time:
            if time > self._now.time():
                target_datetime = datetime.datetime.combine(self._now.date(), time)
            else:
                # handle wrap around to next day if time is in the past already
                target_date = self._now.date() + datetime.timedelta(days=1)
                target_datetime = datetime.datetime.combine(target_date, time)
        elif type(time) == datetime.datetime:
            target_datetime = time
        else:
            raise ValueError(f"Unknown time type '{type(time)}' for fast_forward")

        self._run_callbacks_and_advance_time(target_datetime)

    ### Internal functions
    def _queue_callback(self, callback_function, kwargs, run_date_time):
        """queue a new callback and return its handle"""
        interval = kwargs.get("interval", 0)
        new_callback = CallbackInfo(callback_function, kwargs, run_date_time, interval)

        if new_callback.run_date_time < self._now:
            raise ValueError("Can not schedule events in the past")

        self._registered_callbacks.append(new_callback)
        return new_callback.handle

    def _run_callbacks_and_advance_time(self, target_datetime, run_callbacks=True):
        """run all callbacks scheduled between now and target_datetime"""
        if target_datetime < self._now:
            raise ValueError("You can not fast forward to a time in the past.")

        while True:
            callbacks_to_run = [
                x
                for x in self._registered_callbacks
                if x.run_date_time <= target_datetime
            ]
            if not callbacks_to_run:
                break
            # sort so we call them in the order from oldest to newest
            callbacks_to_run.sort(key=lambda cb: cb.run_date_time)
            # dispatch the oldest callback
            callback = callbacks_to_run[0]
            self._now = callback.run_date_time
            if run_callbacks:
                callback()
            if callback.interval > 0:
                callback.run_date_time += datetime.timedelta(seconds=callback.interval)
            else:
                self._registered_callbacks.remove(callback)

        self._now = target_datetime

    def __getattr__(self, name: str):
        raise RuntimeError(f"'{name}' has not been mocked in {self.__class__.__name__}")


class CallbackInfo:
    """Class to hold info about a scheduled callback"""

    def __init__(self, callback_function, kwargs, run_date_time, interval):
        self.handle = str(uuid.uuid4())
        self.run_date_time = run_date_time
        self.callback_function = callback_function
        self.kwargs = kwargs
        self.interval = interval

    def __call__(self):
        self.callback_function(self.kwargs)
