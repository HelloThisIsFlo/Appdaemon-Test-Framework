
import datetime
import uuid


class SchedulerMocks:
    """Class to provide functional mocks for the AppDaemon HASS scheduling functions"""
    def __init__(self):
        self._registered_callbacks = []
        # Default to Jan 1st, 2000 12:00AM
        self.set_start_time(datetime.datetime(2000, 1, 1, 0, 0))

    ### Hass mock functions
    def get_now_mock(self):
        return self._now

    def get_now_ts_mock(self):
        return self._now.timestamp()

    def insert_schedule_mock(self, name, utc, callback, repeat, type_, **kwargs):
        aware_dt = datetime.datetime.fromtimestamp(utc)
        return self._queue_calllback(callback, kwargs, aware_dt)

    def cancel_timer_mock(self, handle):
        for callback in self._registered_callbacks:
            if callback.handle == handle:
                self._registered_callbacks.remove(callback)

    ### Test framework functions
    def set_start_time(self, time):
        """Set the absolute start time and set current time to that as well.
        if time is a datetime, it goes right to that.
        if time is time, it will set to that time with the current date.

        To guarantee consistency, you can not set the start time while any callbacks are scheduled.
        """
        if len(self._registered_callbacks) > 0:
            raise RuntimeError("You can not set start time while callbacks are scheduled")

        if type(time) == datetime.time:
            time = datetime.datetime.combine(self._now.date(), time)
        self._start_time = self._now = time

    def elapsed_seconds(self):
        return (self._now - self._start_time).total_seconds()

    def fast_forward(self, time):
        """Fastforward time and invoke callbacks. time can be a timedelta, time, or datetime"""
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

        self._run_callbacks_and_advance_time(target_datetime)

    ### Internal functions
    def _queue_calllback(self, callback_function, kwargs, run_date_time):
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
            callbacks_to_run = [x for x in self._registered_callbacks if x.run_date_time <= target_datetime]
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