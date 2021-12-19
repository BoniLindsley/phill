#!/usr/bin/env python3

# Standard library.
import concurrent.futures
import datetime
import functools
import pathlib
import subprocess
import sys
import threading
import typing
import unittest
import unittest.mock

# External dependencies.
import PySide6.QtCore
import mypy.api
import pytest

# Internal packages.
import phill.PySide6.QtCore


def test_process_deferred_delete_events_triggers_deletion(
    q_core_application: PySide6.QtCore.QCoreApplication,
) -> None:
    del q_core_application
    list_to_pop = [None]
    q_object = PySide6.QtCore.QObject()
    q_object.destroyed.connect(list_to_pop.pop)
    q_object.deleteLater()
    phill.PySide6.QtCore.process_deferred_delete_events()
    assert not list_to_pop


def test_process_events_can_trigger_timer_events(
    q_core_application: PySide6.QtCore.QCoreApplication,
) -> None:
    del q_core_application

    class TimedObject(PySide6.QtCore.QObject):
        def __init__(
            self, *args: typing.Any, **kwargs: typing.Any
        ) -> None:
            super().__init__(*args, **kwargs)
            self.timer_triggered = False
            self.timer_id = self.startTimer(0)

        def timerEvent(self, _event: PySide6.QtCore.QTimerEvent) -> None:
            self.timer_triggered = True
            self.killTimer(self.timer_id)

    try:
        timed_object = TimedObject()
        phill.PySide6.QtCore.process_events()
        assert timed_object.timer_triggered
    finally:
        timed_object.deleteLater()


def test_call_request_attributes() -> None:
    assert isinstance(
        phill.PySide6.QtCore.CallRequest.event_type,
        PySide6.QtCore.QEvent.Type,
    )
    phill.PySide6.QtCore.CallRequest(lambda: None)


class TestCaller:
    def test_calls_callback_in_call_requests(
        self,
        q_core_application: PySide6.QtCore.QCoreApplication,
    ) -> None:
        del q_core_application
        list_to_pop = [None]
        caller = phill.PySide6.QtCore.Caller()
        try:
            caller.event(
                phill.PySide6.QtCore.CallRequest(
                    callback=list_to_pop.pop
                )
            )
        finally:
            caller.deleteLater()
        assert not list_to_pop

    def test_deletes_self_after_calling_callback(
        self,
        q_core_application: PySide6.QtCore.QCoreApplication,
    ) -> None:
        del q_core_application
        list_to_pop = [None]
        caller = phill.PySide6.QtCore.Caller()
        try:
            caller.destroyed.connect(list_to_pop.pop)
            caller.event(
                phill.PySide6.QtCore.CallRequest(callback=lambda: None)
            )
            phill.PySide6.QtCore.process_deferred_delete_events()
        except:
            caller.deleteLater()
            raise
        assert not list_to_pop

    def test_ignores_events_that_are_not_call_requests(
        self,
        q_core_application: PySide6.QtCore.QCoreApplication,
    ) -> None:
        del q_core_application
        try:
            list_to_not_pop = [None]
            caller = phill.PySide6.QtCore.Caller()
            caller.destroyed.connect(list_to_not_pop.pop)
            caller.event(
                PySide6.QtCore.QEvent(PySide6.QtCore.QEvent.User)
            )
            phill.PySide6.QtCore.process_deferred_delete_events()
        finally:
            caller.deleteLater()
        assert list_to_not_pop

    def test_processing_posted_events_sends_requests(
        self,
        q_core_application: PySide6.QtCore.QCoreApplication,
    ) -> None:
        del q_core_application
        list_to_pop = [None]
        caller = phill.PySide6.QtCore.Caller()
        PySide6.QtCore.QCoreApplication.postEvent(
            caller,
            phill.PySide6.QtCore.CallRequest(callback=list_to_pop.pop),
        )
        phill.PySide6.QtCore.process_events()
        phill.PySide6.QtCore.process_deferred_delete_events()
        assert not list_to_pop


class TestCallSoonThreadsafe:
    def test_calls_callback_eventually(
        self, q_core_application: PySide6.QtCore.QCoreApplication
    ) -> None:
        del q_core_application
        list_to_pop = [None]
        phill.PySide6.QtCore.call_soon_threadsafe(list_to_pop.pop)
        phill.PySide6.QtCore.process_events()
        phill.PySide6.QtCore.process_deferred_delete_events()
        assert not list_to_pop

    def test_passes_positional_arguments_to_callback(
        self, q_core_application: PySide6.QtCore.QCoreApplication
    ) -> None:
        del q_core_application
        list_to_append: list[int] = []
        phill.PySide6.QtCore.call_soon_threadsafe(
            list_to_append.append, 0
        )
        phill.PySide6.QtCore.process_events()
        phill.PySide6.QtCore.process_deferred_delete_events()
        assert list_to_append == [0]

    def test_calls_from_different_thread_defaults_to_main(
        self, q_core_application: PySide6.QtCore.QCoreApplication
    ) -> None:
        del q_core_application
        list_to_pop = [None]
        worker = threading.Thread(
            target=functools.partial(
                phill.PySide6.QtCore.call_soon_threadsafe,
                list_to_pop.pop,
            )
        )
        worker.start()
        worker.join()
        assert list_to_pop
        phill.PySide6.QtCore.process_events()
        phill.PySide6.QtCore.process_deferred_delete_events()
        assert not list_to_pop

    def test_call_into_specified_thread(
        self, q_core_application: PySide6.QtCore.QCoreApplication
    ) -> None:
        list_to_pop = [None]
        worker = threading.Thread(
            target=functools.partial(
                phill.PySide6.QtCore.call_soon_threadsafe,
                list_to_pop.pop,
                thread=q_core_application.thread(),
            )
        )
        worker.start()
        worker.join()
        phill.PySide6.QtCore.process_events()
        phill.PySide6.QtCore.process_deferred_delete_events()
        assert not list_to_pop


future_script = """
import collections.abc
import concurrent.futures
import typing
_T = typing.TypeVar("_T")
class Future(concurrent.futures.Future[_T]):
    __Self = typing.TypeVar("__Self", bound="Future[_T]")
    def add_done_callback(
        self: __Self,
        fn: collections.abc.Callable[[__Self], typing.Any],
    ) -> None:
        super().add_done_callback(fn)
"""


class TestFuture:
    def test_static_check_add_done_callback(self) -> None:
        list_to_pop = [None]
        future = phill.PySide6.QtCore.Future[int]()

        def done_callback(
            future: phill.PySide6.QtCore.Future[int],
        ) -> None:
            del future
            list_to_pop.pop()

        future.add_done_callback(done_callback)
        future.set_result(0)
        assert not list_to_pop

    def test_fix_is_necessary(self, tmp_path: pathlib.Path) -> None:
        result = mypy.api.run(["-c", future_script])
        assert len(result) == 3
        assert (
            result[2] != 0
        ), "Subclassing Future directly might be possible."
        assert result[0].splitlines() == [
            '<string>:12: error: Argument 1 to "add_done_callback"'
            ' of "Future" has incompatible type'
            ' "Callable[[__Self], Any]";'
            ' expected "Callable[[Future[_T]], Any]"  [arg-type]',
            "Found 1 error in 1 file (checked 1 source file)",
        ], "mypy error expected, but not the right one."
        assert result[1] == ""


class UserBaseException(Exception):
    pass


class TestTask:
    def test_run_sets_result(self) -> None:
        def zero() -> int:
            return 0

        task = phill.PySide6.QtCore.Task[int](callback=zero)
        task.run()
        assert task.result() == 0

    def test_run_propagates_base_exception(self) -> None:
        def bad() -> int:
            raise UserBaseException()

        task = phill.PySide6.QtCore.Task[int](callback=bad)
        task.run()
        with pytest.raises(UserBaseException):
            task.result()
        assert isinstance(task.exception(), UserBaseException)

    def test_run_respects_cancellation_before_run_call(self) -> None:
        def zero() -> int:
            return 0

        task = phill.PySide6.QtCore.Task[int](callback=zero)
        task.cancel()
        task.run()
        with pytest.raises(concurrent.futures.CancelledError):
            task.result()


class TestExecutor:
    def test_calls_submitted_callable(
        self, q_core_application: PySide6.QtCore.QCoreApplication
    ) -> None:
        del q_core_application
        list_to_pop = [None]
        with phill.PySide6.QtCore.Executor() as executor:
            executor.submit(list_to_pop.pop)
            assert list_to_pop
            phill.PySide6.QtCore.process_events()
        assert not list_to_pop

    def test_calls_submitted_callable_with_given_arguments(
        self, q_core_application: PySide6.QtCore.QCoreApplication
    ) -> None:
        del q_core_application
        list_to_pop = [None]
        with phill.PySide6.QtCore.Executor() as executor:
            executor.submit(list_to_pop.pop, 0)
            phill.PySide6.QtCore.process_events()
        assert not list_to_pop

    def test_shutdown_twice_is_okay(
        self, q_core_application: PySide6.QtCore.QCoreApplication
    ) -> None:
        del q_core_application
        with phill.PySide6.QtCore.Executor() as executor:
            executor.shutdown()

    def test_shutdown_waits_for_task_to_finish(
        self, q_core_application: PySide6.QtCore.QCoreApplication
    ) -> None:
        del q_core_application
        list_to_pop = [None]
        process_gui_events = threading.Event()

        def run() -> None:
            with phill.PySide6.QtCore.Executor() as executor:
                executor.submit(list_to_pop.pop)
                process_gui_events.set()
                executor.shutdown()

        worker_thread = threading.Thread(target=run, daemon=True)
        worker_thread.start()
        timeout = datetime.timedelta(seconds=2).total_seconds()
        process_gui_events.wait(timeout=timeout)
        phill.PySide6.QtCore.process_events()
        worker_thread.join(timeout=timeout)
        assert not list_to_pop

    def test_shutdown_can_cancel_futures(
        self, q_core_application: PySide6.QtCore.QCoreApplication
    ) -> None:
        del q_core_application
        list_to_pop = [None]
        process_gui_events = threading.Event()

        def run() -> None:
            with phill.PySide6.QtCore.Executor() as executor:
                executor.submit(list_to_pop.pop)
                executor.shutdown(cancel_futures=True)
                process_gui_events.set()

        worker_thread = threading.Thread(target=run, daemon=True)
        worker_thread.start()
        timeout = datetime.timedelta(seconds=2).total_seconds()
        process_gui_events.wait(timeout=timeout)
        phill.PySide6.QtCore.process_events()
        worker_thread.join(timeout=timeout)
        assert list_to_pop

    def test_shutdown_does_not_have_to_wait(
        self, q_core_application: PySide6.QtCore.QCoreApplication
    ) -> None:
        del q_core_application
        list_to_pop = [None]
        process_gui_events = threading.Event()

        def run() -> None:
            with phill.PySide6.QtCore.Executor() as executor:
                executor.submit(list_to_pop.pop)
                executor.shutdown(wait=False)
                process_gui_events.set()

        worker_thread = threading.Thread(target=run, daemon=True)
        worker_thread.start()
        timeout = datetime.timedelta(seconds=2).total_seconds()
        process_gui_events.wait(timeout=timeout)
        phill.PySide6.QtCore.process_events()
        worker_thread.join(timeout=timeout)
        assert not list_to_pop

    def test_submission_fails_after_shutdown(
        self, q_core_application: PySide6.QtCore.QCoreApplication
    ) -> None:
        del q_core_application
        with phill.PySide6.QtCore.Executor() as executor:
            pass
        with pytest.raises(RuntimeError):
            executor.submit(lambda: None)
