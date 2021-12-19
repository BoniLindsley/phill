#!/usr/bin/env python3

# Standard library.
from __future__ import annotations  # For delayed type expansion < 3.10.
import collections.abc
import concurrent.futures
import contextvars
import datetime
import functools
import threading
import typing

# External dependencies.
import PySide6.QtCore

_T = typing.TypeVar("_T")
NullaryCallable = collections.abc.Callable[[], typing.Any]

wait_for_timeout: contextvars.ContextVar[
    datetime.timedelta
] = contextvars.ContextVar(
    "wait_for_timeout", default=datetime.timedelta(seconds=2)
)
"""Default timeout value when processing PySide6 events."""


def process_deferred_delete_events() -> None:
    # Calling `processEvents` does not process `DeferredDelete` events.
    # Asking `sendPostedEvents` to process all events
    # (which is done by`processEvents`, I think)
    # also does not process it.
    # So this needs to be explicitly called.
    PySide6.QtCore.QCoreApplication.sendPostedEvents(
        None,
        PySide6.QtCore.QEvent.DeferredDelete,  # type: ignore[arg-type]
    )


def process_events() -> None:
    PySide6.QtCore.QCoreApplication.processEvents(
        PySide6.QtCore.QEventLoop.AllEvents,
        int(wait_for_timeout.get() / datetime.timedelta(milliseconds=1)),
    )


class CallRequest(PySide6.QtCore.QEvent):

    event_type = PySide6.QtCore.QEvent.Type(
        PySide6.QtCore.QEvent.registerEventType()
    )

    def __init__(self, callback: NullaryCallable) -> None:
        super().__init__(self.event_type)
        self.callback = callback


class Caller(PySide6.QtCore.QObject):
    def customEvent(
        self, event_to_handle: PySide6.QtCore.QEvent
    ) -> None:
        """Internal."""
        if event_to_handle.type() == CallRequest.event_type:
            try:
                event_to_handle.callback()
            finally:
                self.deleteLater()
        else:
            super().customEvent(event_to_handle)


def call_soon_threadsafe(
    callback: typing.Callable[..., typing.Any],
    *args: typing.Any,
    thread: PySide6.QtCore.QThread | None = None,
) -> None:
    """Schedule ``callback`` to be called in the Qt event loop."""
    if args:
        callback = functools.partial(callback, *args)
    if thread is None:
        q_core_application = PySide6.QtCore.QCoreApplication.instance()
        assert q_core_application is not None
        thread = q_core_application.thread()
    event_to_post = CallRequest(callback=callback)
    caller = Caller()  # Might leak if any of the below fails.
    caller.moveToThread(thread)
    caller.setParent(thread)
    PySide6.QtCore.QCoreApplication.postEvent(caller, event_to_post)


class Future(concurrent.futures.Future[_T]):
    """Fixes typing of add_done_callback."""

    __Self = typing.TypeVar("__Self", bound="Future[_T]")

    # The name `fn` is used by superclass. Keeping it for consistency.
    def add_done_callback(  # pylint: disable=invalid-name
        self: __Self,
        fn: collections.abc.Callable[[__Self], typing.Any],
    ) -> None:
        super().add_done_callback(
            typing.cast(
                collections.abc.Callable[
                    [concurrent.futures.Future[_T]], typing.Any
                ],
                fn,
            )
        )


class Task(Future[_T]):
    def __init__(
        self,
        *args: typing.Any,
        callback: collections.abc.Callable[[], _T],
        **kwargs: typing.Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._callback = callback

    def run(self) -> None:
        if not self.set_running_or_notify_cancel():
            return
        try:
            result = self._callback()
        # Intentionally catching all exception to propagate.
        # pylint: disable=broad-except
        except BaseException as exception:
            self.set_exception(exception)
        else:
            self.set_result(result)


class Executor(concurrent.futures.Executor):
    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)
        self.futures = set[Task[typing.Any]]()
        self.future_done_event = threading.Event()
        self.is_shutdown = False
        self.shutdown_lock = threading.Lock()

    def submit(
        self,
        fn: collections.abc.Callable[..., _T],
        /,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> concurrent.futures.Future[_T]:
        callback: collections.abc.Callable[[], _T]
        if args or kwargs:
            callback = functools.partial(
                fn,
                *args,
                **kwargs,
            )
        else:
            callback = fn
        task = Task[_T](callback=callback)
        task.add_done_callback(self.futures.discard)
        task.add_done_callback(
            lambda _future: self.future_done_event.set()
        )
        with self.shutdown_lock:
            if self.is_shutdown:
                raise RuntimeError("Executor is shut down.")
            call_soon_threadsafe(callback=task.run)
            self.futures.add(task)
        return task

    def shutdown(
        self, wait: bool = True, *, cancel_futures: bool = False
    ) -> None:
        with self.shutdown_lock:
            self.is_shutdown = True
        if cancel_futures:
            for future in self.futures.copy():
                future.cancel()
        if wait:
            while self.futures:
                self.future_done_event.wait()
                self.future_done_event.clear()
        super().shutdown(wait=wait, cancel_futures=cancel_futures)
