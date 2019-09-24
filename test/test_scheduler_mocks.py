from appdaemontestframework.scheduler_mocks import SchedulerMocks
import pytest
import datetime


@pytest.fixture
def scheduler_mocks():
    return SchedulerMocks()


class Test_get_now_mocks:
    """tests for SchedulerMocks.get_now_*() calls"""
    def test_get_now_returns_proper_time(self, scheduler_mocks):
        # the time should default to Jan 1st, 2000 12:00AM
        assert scheduler_mocks.get_now_mock() == datetime.datetime(2000, 1, 1, 0, 0)

    def test_get_now_ts_returns_proper_time_stamp(self,  scheduler_mocks):
        # the time should default to Jan 1st, 2000 12:00AM
        assert scheduler_mocks.get_now_ts_mock() == datetime.datetime(2000, 1, 1, 0, 0).timestamp()


class Test_time_movement:
    def test_set_start_time_to_known_time(self, scheduler_mocks):
        new_time = datetime.datetime(2010, 6, 1, 0, 0)
        scheduler_mocks.set_start_time(new_time)
        assert scheduler_mocks.get_now_mock() == new_time

    def test_cant_set_start_time_with_pending_callbacks(self, scheduler_mocks):
        scheduled_utc = scheduler_mocks.get_now_ts_mock() + 10
        scheduler_mocks.insert_schedule_mock('', scheduled_utc, lambda: None, False, None)
        with pytest.raises(RuntimeError) as cm:
            scheduler_mocks.set_start_time(datetime.datetime(2010, 6, 1, 0, 0))
        assert str(cm.value) == 'You can not set start time while callbacks are scheduled'

    def test_fast_forward_to_past_raises_exception(self, scheduler_mocks):
        with pytest.raises(ValueError) as cm:
            scheduler_mocks.fast_forward(datetime.timedelta(-1))
        assert str(cm.value) == "You can not fast forward to a time in the past."

    def test_fast_forward_to_time_in_future_goes_to_correct_time(self, scheduler_mocks):
        scheduler_mocks.set_start_time(datetime.datetime(2015, 1, 1, 12, 0))
        scheduler_mocks.fast_forward(datetime.time(14, 0))
        assert scheduler_mocks.get_now_mock() == datetime.datetime(2015, 1, 1, 14, 0)

    def test_fast_forward_to_time_in_past_wraps_to_correct_time(self, scheduler_mocks):
        scheduler_mocks.set_start_time(datetime.datetime(2015, 1, 1, 12, 0))
        scheduler_mocks.fast_forward(datetime.time(7, 0))
        assert scheduler_mocks.get_now_mock() == datetime.datetime(2015, 1, 2, 7, 0)

    def test_fast_forward_to_datetime_goes_to_correct_time(self, scheduler_mocks):
        to_datetime = datetime.datetime(2020, 5, 4, 10, 10)
        scheduler_mocks.fast_forward(to_datetime)
        assert scheduler_mocks.get_now_mock() == to_datetime

    def test_fast_forward_by_timedelta_goes_to_correct_time(self, scheduler_mocks):
        scheduler_mocks.set_start_time(datetime.datetime(2015, 1, 1, 12, 0))
        scheduler_mocks.fast_forward(datetime.timedelta(days=1))
        assert scheduler_mocks.get_now_mock() == datetime.datetime(2015, 1, 2, 12, 0)

    #def test_scheduled_

class Test_scheduling_and_dispatch:
    pass