import asyncio
import datetime
from unittest import mock

import pytest
import pytz

from appdaemontestframework.appdaemon_mock.appdaemon import MockAppDaemon
from appdaemontestframework.appdaemon_mock.scheduler import MockScheduler


@pytest.fixture
def scheduler() -> MockScheduler:
    return MockScheduler(MockAppDaemon())


def test_calling_a_scheduler_method_not_mocked_raises_a_helpful_error_message(
    scheduler,
):
    # For instance `parse_time` is a method that's not mocked because it is
    # not needed with the current time travel logic.
    with pytest.raises(RuntimeError) as error:
        scheduler.parse_time("2020/01/01T23:11")

    assert "'parse_time' has not been mocked" in str(error.value)


class Test_get_now:
    """tests for SchedulerMocks.get_now_*() calls"""

    @pytest.mark.asyncio
    async def test_get_now_returns_proper_time(self, scheduler):
        # the time should default to Jan 1st, 2000 12:00AM UTC
        assert await scheduler.get_now() == pytz.utc.localize(
            datetime.datetime(2000, 1, 1, 0, 0)
        )

    @pytest.mark.asyncio
    async def test_get_now_ts_returns_proper_time_stamp(self, scheduler):
        # the time should default to Jan 1st, 2000 12:00AM
        assert (
            await scheduler.get_now_ts()
            == pytz.utc.localize(
                datetime.datetime(2000, 1, 1, 0, 0)
            ).timestamp()
        )


class Test_time_movement:
    def test_set_start_time_to_known_time(self, scheduler):
        new_time = datetime.datetime(2010, 6, 1, 0, 0)
        scheduler.sim_set_start_time(new_time)
        assert scheduler.get_now_sync() == pytz.utc.localize(new_time)

    @pytest.mark.asyncio
    async def test_cant_set_start_time_with_pending_callbacks(self, scheduler):
        scheduled_time = scheduler.get_now_sync() + datetime.timedelta(
            seconds=10
        )
        await scheduler.insert_schedule(
            "", scheduled_time, lambda: None, False, None
        )
        with pytest.raises(RuntimeError) as cm:
            scheduler.sim_set_start_time(datetime.datetime(2010, 6, 1, 0, 0))
        assert (
            str(cm.value)
            == "You can not set start time while callbacks are scheduled"
        )

    def test_fast_forward_to_past_raises_exception(self, scheduler):
        with pytest.raises(ValueError) as cm:
            scheduler.sim_fast_forward(datetime.timedelta(-1))
        assert (
            str(cm.value) == "You can not fast forward to a time in the past."
        )

    @pytest.mark.asyncio
    async def test_fast_forward_to_time_in_future_goes_to_correct_time(
        self, scheduler
    ):
        scheduler.sim_set_start_time(datetime.datetime(2015, 1, 1, 12, 0))
        scheduler.sim_fast_forward(datetime.time(14, 0))
        assert await scheduler.get_now() == pytz.utc.localize(
            datetime.datetime(2015, 1, 1, 14, 0)
        )

    @pytest.mark.asyncio
    async def test_fast_forward_to_time_in_past_wraps_to_correct_time(
        self, scheduler
    ):
        scheduler.sim_set_start_time(datetime.datetime(2015, 1, 1, 12, 0))
        scheduler.sim_fast_forward(datetime.time(7, 0))
        assert await scheduler.get_now() == pytz.utc.localize(
            datetime.datetime(2015, 1, 2, 7, 0)
        )

    @pytest.mark.asyncio
    async def test_fast_forward_to_datetime_goes_to_correct_time(
        self, scheduler
    ):
        to_datetime = datetime.datetime(2020, 5, 4, 10, 10)
        scheduler.sim_fast_forward(to_datetime)
        assert await scheduler.get_now() == pytz.utc.localize(to_datetime)

    @pytest.mark.asyncio
    async def test_fast_forward_by_timedelta_goes_to_correct_time(
        self, scheduler
    ):
        scheduler.sim_set_start_time(datetime.datetime(2015, 1, 1, 12, 0))
        scheduler.sim_fast_forward(datetime.timedelta(days=1))
        assert await scheduler.get_now() == pytz.utc.localize(
            datetime.datetime(2015, 1, 2, 12, 0)
        )


class Test_scheduling_and_dispatch:
    @pytest.mark.asyncio
    async def test_schedule_in_the_future_succeeds(
        self, scheduler: MockScheduler
    ):
        scheduled_time = await scheduler.get_now() + datetime.timedelta(
            seconds=10
        )
        await scheduler.insert_schedule(
            "", scheduled_time, lambda: None, False, None
        )

    @pytest.mark.asyncio
    async def test_schedule_in_the_past_raises_exception(
        self, scheduler: MockScheduler
    ):
        scheduled_time = await scheduler.get_now() - datetime.timedelta(
            seconds=10
        )
        with pytest.raises(ValueError):
            await scheduler.insert_schedule(
                "", scheduled_time, lambda: None, False, None
            )

    @pytest.mark.asyncio
    async def test_callbacks_are_run_in_time_order(
        self, scheduler: MockScheduler
    ):
        first_mock = mock.Mock()
        second_mock = mock.Mock()
        third_mock = mock.Mock()
        manager = mock.Mock()
        manager.attach_mock(first_mock, "first_mock")
        manager.attach_mock(second_mock, "second_mock")
        manager.attach_mock(third_mock, "third_mock")

        now = await scheduler.get_now()
        # Note: insert them out of order to try and expose possible bugs
        await asyncio.gather(
            scheduler.insert_schedule(
                "",
                now + datetime.timedelta(seconds=10),
                first_mock,
                False,
                None,
            ),
            scheduler.insert_schedule(
                "",
                now + datetime.timedelta(seconds=30),
                third_mock,
                False,
                None,
            ),
            scheduler.insert_schedule(
                "",
                now + datetime.timedelta(seconds=20),
                second_mock,
                False,
                None,
            ),
        )

        scheduler.sim_fast_forward(datetime.timedelta(seconds=30))

        expected_call_order = [
            mock.call.first_mock({}),
            mock.call.second_mock({}),
            mock.call.third_mock({}),
        ]
        assert manager.mock_calls == expected_call_order

    @pytest.mark.asyncio
    async def test_callback_not_called_before_timeout(
        self, scheduler: MockScheduler
    ):
        callback_mock = mock.Mock()
        now = await scheduler.get_now()
        await scheduler.insert_schedule(
            "",
            now + datetime.timedelta(seconds=10),
            callback_mock,
            False,
            None,
        ),
        scheduler.sim_fast_forward(datetime.timedelta(seconds=5))

        callback_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_callback_called_after_timeout(
        self, scheduler: MockScheduler
    ):
        callback_mock = mock.Mock()
        now = await scheduler.get_now()
        await scheduler.insert_schedule(
            "",
            now + datetime.timedelta(seconds=10),
            callback_mock,
            False,
            None,
        ),
        scheduler.sim_fast_forward(datetime.timedelta(seconds=20))

        callback_mock.assert_called()

    @pytest.mark.asyncio
    async def test_canceled_timer_does_not_run_callback(
        self, scheduler: MockScheduler
    ):
        callback_mock = mock.Mock()
        now = await scheduler.get_now()
        handle = await scheduler.insert_schedule(
            "",
            now + datetime.timedelta(seconds=10),
            callback_mock,
            False,
            None,
        )
        scheduler.sim_fast_forward(datetime.timedelta(seconds=5))
        await scheduler.cancel_timer("", handle)
        scheduler.sim_fast_forward(datetime.timedelta(seconds=10))

        callback_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_time_is_correct_when_callback_it_run(
        self, scheduler: MockScheduler
    ):
        scheduler.sim_set_start_time(datetime.datetime(2020, 1, 1, 12, 0))

        time_when_called = []

        def callback(kwargs):
            nonlocal time_when_called
            time_when_called.append(scheduler.get_now_sync())

        now = await scheduler.get_now()
        await asyncio.gather(
            scheduler.insert_schedule(
                "", now + datetime.timedelta(seconds=1), callback, False, None
            ),
            scheduler.insert_schedule(
                "", now + datetime.timedelta(seconds=15), callback, False, None
            ),
            scheduler.insert_schedule(
                "", now + datetime.timedelta(seconds=65), callback, False, None
            ),
        )
        scheduler.sim_fast_forward(datetime.timedelta(seconds=90))

        expected_call_times = [
            pytz.utc.localize(datetime.datetime(2020, 1, 1, 12, 0, 1)),
            pytz.utc.localize(datetime.datetime(2020, 1, 1, 12, 0, 15)),
            pytz.utc.localize(datetime.datetime(2020, 1, 1, 12, 1, 5)),
        ]
        assert expected_call_times == time_when_called

    @pytest.mark.asyncio
    async def test_callback_called_with_correct_args(
        self, scheduler: MockScheduler
    ):
        callback_mock = mock.Mock()
        now = await scheduler.get_now()
        await scheduler.insert_schedule(
            "",
            now + datetime.timedelta(seconds=1),
            callback_mock,
            False,
            None,
            arg1="asdf",
            arg2="qwerty",
        )
        scheduler.sim_fast_forward(datetime.timedelta(seconds=10))

        callback_mock.assert_called_once_with(
            {"arg1": "asdf", "arg2": "qwerty"}
        )

    @pytest.mark.asyncio
    async def test_callback_with_interval_is_rescheduled_after_being_run(
        self, scheduler: MockScheduler
    ):
        callback_mock = mock.Mock()
        now = await scheduler.get_now()
        await scheduler.insert_schedule(
            "",
            now + datetime.timedelta(seconds=10),
            callback_mock,
            False,
            None,
            interval=10,
        )

        # Advance 3 time and make sure it's called each time
        scheduler.sim_fast_forward(datetime.timedelta(seconds=10))
        assert callback_mock.call_count == 1
        scheduler.sim_fast_forward(datetime.timedelta(seconds=10))
        assert callback_mock.call_count == 2
        scheduler.sim_fast_forward(datetime.timedelta(seconds=10))
        assert callback_mock.call_count == 3
