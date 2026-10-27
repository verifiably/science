"""Stop signals for the launchers: SIGTERM and SIGHUP become an exit that runs
cleanup, and a launcher can hold one off across the window where nothing yet
owns that cleanup."""
from __future__ import annotations

import signal
import sys
import threading
from contextlib import contextmanager

# The ordinary ways a long-running launcher is stopped: an MCP client or a
# service manager sends SIGTERM, a closed terminal sends SIGHUP.
_STOP_SIGNALS = (signal.SIGTERM, signal.SIGHUP)

# The main thread's hold: whether a stop signal is deferred, and the one that
# arrived while it was. Only the main thread runs a signal handler.
_hold = {"active": False, "pending": None}


@contextmanager
def stop_signals_exit():
    """Turn a stop signal into `SystemExit` in the main thread, so the
    launcher's `finally` blocks run: the socket it bound is unlinked and its
    session ledgers `session-close`. The default action kills the process
    without either, and the next launcher then refuses on the stale socket.

    Installed at the CLI entry, because `signal.signal` works only from the
    main thread and tests run `serve` functions from worker threads. The
    first stop signal restores the previous handlers, so a second one while
    cleanup runs, or while a hold defers the first, stops the process the old
    way.

    A signal already ignored (`SIG_IGN`) — as SIGHUP is when a launcher is
    started under `nohup` — is left ignored rather than overridden: a
    launcher that used to survive its terminal closing must keep surviving
    it."""
    def stop(signum, frame):
        for number, handler in previous.items():
            signal.signal(number, handler)
        if _hold["active"]:
            _hold["pending"] = signum
            return
        raise SystemExit(128 + signum)

    previous: dict[int, object] = {}
    for number in _STOP_SIGNALS:
        current = signal.getsignal(number)
        if current is signal.SIG_IGN:
            continue
        previous[number] = signal.signal(number, stop)
    try:
        yield
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


@contextmanager
def stop_signals_held():
    """Defer a stop signal until the caller's cleanup owns what it must clean:
    yields `release`, which the caller calls inside the `try` whose `finally`
    closes the session and socket, and which raises the deferred stop there.
    Leaving the block releases too; leaving it on an exception drops a
    deferred stop instead, so the exception that ends the launcher is the one
    reported. A launcher's cleanup holds as well, so a first stop signal
    cannot cut short the drain or the session close it is waiting on.

    A stop signal raises at whatever line the main thread is on, so without a
    hold one landing while the session opens, or after the socket binds but
    before the assignment the `finally` reads, leaves the session unclosed or
    the socket on disk. A hold taken off the main thread does nothing: no
    signal raises there."""
    if threading.current_thread() is not threading.main_thread():
        yield lambda: None
        return

    def release() -> None:
        _hold["active"] = False
        pending, _hold["pending"] = _hold["pending"], None
        if pending is not None:
            raise SystemExit(128 + pending)

    _hold["active"] = True
    try:
        yield release
    except BaseException:
        _hold["active"], _hold["pending"] = False, None
        raise
    if sys.exc_info()[1] is not None:
        # A hold inside a `finally` that an exception is unwinding through:
        # that exception, not the deferred stop, is what ends the launcher.
        _hold["active"], _hold["pending"] = False, None
        return
    release()
