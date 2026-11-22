"""Host-side control and lifetime of a supervised run session."""
from __future__ import annotations

from contextlib import ExitStack, contextmanager
import os
import selectors
import select
import signal
import socket
import stat
import threading
import time
from pathlib import Path
import tempfile

from beliefs.errors import SealTimeout, ScienceError

from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.refusal import Refusal, Refused
from science.serve import refused_reply
from science.run_endpoint import drain
from science.run_endpoint.basis import seal_basis
from science.run_endpoint.control import Control, seal_evidence, wire
from science.run_endpoint.handle import answer, receive_actor
from science.run_endpoint.launch import open_run
from science.run_endpoint.paths import Scratch


def persist_seal(run_dir: Path, document: dict) -> None:
    """Publish the witness only after syncing the complete private file."""
    parent = os.open(run_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        with tempfile.NamedTemporaryFile(dir=run_dir, prefix=".seal-", delete=False) as stream:
            temp = Path(stream.name)
            try:
                stream.write(wire(document))
                stream.flush()
                os.fsync(stream.fileno())
            except BaseException:
                temp.unlink()
                raise
        try:
            os.replace(temp.name, "seal.json", src_dir_fd=parent, dst_dir_fd=parent)
            os.fsync(parent)
        finally:
            temp.unlink(missing_ok=True)
    finally:
        os.close(parent)


@contextmanager
def _term_wakeup():
    reader, writer = socket.socketpair()
    with reader, writer:
        reader.setblocking(False)
        writer.setblocking(False)
        pending = False

        def term(signum, frame):
            nonlocal pending
            pending = True

        prior = signal.signal(signal.SIGTERM, term)
        try:
            previous_fd = signal.set_wakeup_fd(writer.fileno(), warn_on_full_buffer=False)
            try:
                mask = signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTERM})
                try:
                    yield reader, lambda: pending
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, mask)
            finally:
                signal.set_wakeup_fd(previous_fd)
        finally:
            signal.signal(signal.SIGTERM, prior)


@contextmanager
def _listener(path):
    with socket.socket(socket.AF_UNIX) as server:
        server.bind(str(path))
        identity = path.lstat()
        try:
            path.chmod(0o600)
            server.listen()
            server.setblocking(False)
            yield server
        finally:
            if path.exists() and os.path.samestat(identity, path.lstat()):
                path.unlink()


class _Actors:
    """Only authenticated requests that can start work own a drain obligation."""

    def __init__(self, token, scratch, can_execute, writes):
        self.token = token
        self.scratch = scratch
        self.can_execute = can_execute
        self.writes = writes
        self.condition = threading.Condition()
        self.pending = set()
        self.failed = threading.Event()
        self.slots = threading.BoundedSemaphore(32)

    def accept(self, server, namespace, dispatcher):
        try:
            stream, _ = server.accept()
        except BlockingIOError:
            return
        if not self.slots.acquire(blocking=False):
            stream.close()
            return
        peer_ns = None
        try:
            if namespace is not None:
                peer_ns = os.dup(namespace)
            threading.Thread(target=self._serve, args=(stream, peer_ns, dispatcher), daemon=True).start()
        except BaseException:
            stream.close()
            self.slots.release()
            if peer_ns is not None:
                os.close(peer_ns)
            raise

    def _serve(self, stream, namespace, dispatcher):
        try:
            with stream:
                stream.settimeout(5.0)
                try:
                    request = receive_actor(stream, namespace, self.token)
                    reply = self._dispatch(dispatcher, request)
                except Refused as error:
                    reply = refused_reply(error)
                stream.sendall(wire(reply))
        except (OSError, EOFError):
            pass
        finally:
            if namespace is not None:
                os.close(namespace)
            self.slots.release()

    def _dispatch(self, dispatcher, request):
        command = request.get("command") if isinstance(request, dict) else None
        writes = isinstance(command, str) and command in self.writes
        with self.condition:
            self.scratch.check()
            if writes:
                self.pending.add(threading.get_ident())
        try:
            return answer(dispatcher, request, can_execute=self.can_execute)
        except Exception:
            with self.condition:
                if threading.get_ident() in self.pending:
                    self.failed.set()
            raise
        finally:
            self.complete()

    def complete(self):
        with self.condition:
            self.pending.discard(threading.get_ident())
            self.condition.notify_all()

    def stop(self):
        with self.condition:
            self.scratch.cancelled.set()

    def finished(self):
        with self.condition:
            return not self.pending

    def wait(self, seconds):
        with self.condition:
            if self.pending:
                self.condition.wait(seconds)


def _message(kind, **fields):
    return {"type": kind, "version": "control.v1", **fields}


def _report(control, message):
    try:
        control.queue(message)
    except (OSError, EOFError, Refused):
        pass


def _control_loop(control, server, wake, term, actors, dispatcher, lease, expires, clock):
    with selectors.DefaultSelector() as selector:
        selector.register(server, selectors.EVENT_READ)
        selector.register(control.stream, selectors.EVENT_READ)
        selector.register(wake, selectors.EVENT_READ)
        while True:
            if term():
                return "term"
            if actors.failed.is_set():
                return "failure"
            if clock() >= expires:
                return "lease"
            mask = selectors.EVENT_READ | (selectors.EVENT_WRITE if control.writable else 0)
            selector.modify(control.stream, mask)
            for key, events in selector.select(min(0.5, max(0, expires - clock()))):
                if term():
                    return "term"
                if key.fileobj is wake:
                    wake.recv(4096)
                elif key.fileobj is server:
                    if clock() < expires:
                        actors.accept(server, control.namespace, dispatcher)
                else:
                    try:
                        if events & selectors.EVENT_WRITE:
                            control.flush()
                        if events & selectors.EVENT_READ:
                            kind = control.receive()
                            if clock() >= expires:
                                if kind == "renew":
                                    _report(control, _message("refused", code="run-sealed"))
                                return "lease"
                            if kind == "seal":
                                return "stop"
                            if kind == "renew":
                                expires = clock() + lease
                                control.queue(_message("renewed"))
                            if kind == "bind-actor":
                                control.queue(_message("bound"))
                    except (OSError, EOFError, Refused):
                        return "eof"


def _shutdown(launch, opened, actors, control, cause, clock):
    session = opened.session
    deadline = clock() + launch.seal_timeout_seconds
    actors.stop()

    def observe_control():
        try:
            kind = control.receive()
            if kind == "renew":
                _report(control, _message("refused", code="run-sealed"))
            control.flush()
        except (OSError, EOFError, Refused):
            pass

    def done():
        observe_control()
        return actors.finished()

    sweep = drain.sweep_children if actors.can_execute else lambda: None
    try:
        tips = session.seal(max(0, deadline - clock()))
        if not drain.drain_workers(done, sweep, deadline, clock=clock, wait=actors.wait):
            raise SealTimeout("Invocation drain timed out")
        if actors.failed.is_set() or session.current_invocation is not None:
            raise RuntimeError("An invocation failed to close")
        basis = seal_basis(opened.basis, launch.config)
        document, report = seal_evidence(cause, tips, basis)
        persist_seal(launch.run_dir, document)
        session.close()
        _report(control, report)
        while control.writable:
            remaining = deadline - clock()
            if remaining <= 0:
                break
            try:
                if not select.select([], [control.stream], [], remaining)[1]:
                    break
                control.flush()
            except (OSError, EOFError):
                break
        return 0
    except (OSError, RuntimeError, ScienceError) as error:
        try:
            sweep()
        except OSError:
            pass
        scratch = actors.scratch
        # The process owns any still-live workers and their descriptors up to exit.
        # A failed shutdown never waits beyond the original deadline for cleanup.
        scratch.quiescent = False
        captures = [str(scratch.capture_root / iid) for iid in tuple(scratch.owned)]
        if actors.finished() and clock() < deadline:
            def reclaim():
                try:
                    scratch.cleanup()
                except OSError:
                    pass  # the private diagnostic below identifies remaining paths
            cleanup = threading.Thread(target=reclaim, daemon=True)
            cleanup.start()
            cleanup.join(max(0, deadline - clock()))
        _report(control, _message("seal-timeout" if isinstance(error, SealTimeout) else "seal-failed"))
        stage = launch.config.operations_root / "scratch" / session.session_id
        details = {"session": session.session_id, "error": type(error).__name__, "staging": str(stage),
                   "invocation": session.current_invocation,
                   "captures": captures}
        # The launcher supplies a private log. Never block stderr backpressure on forced exit.
        try:
            if stat.S_ISREG(os.fstat(2).st_mode) or select.select([], [2], [], 0)[1]:
                os.write(2, wire(details))
        except OSError:
            pass
        return 1


def serve_run(launch, *, open_context, clock=time.monotonic):
    """Run in the endpoint process's main thread; return its exit status."""
    if os.path.lexists(launch.run_dir / "seal.json"):
        raise Refused(Refusal("invalid-input", "This run directory already contains a seal"))
    with ExitStack() as resources:
        wake, term = resources.enter_context(_term_wakeup())
        scratch = resources.enter_context(Scratch(launch.scratch_dir, launch.config.operations_root, threading.Event()))
        stream = resources.enter_context(socket.socket(socket.AF_UNIX))
        stream.settimeout(5.0)
        stream.connect(str(launch.control_socket))
        control = resources.enter_context(Control(stream))
        server = resources.enter_context(_listener(launch.socket))
        declarations = production_tree()
        handlers = resolve_handlers(declarations)
        ctx = open_context(launch.config)
        can_execute = drain.can_control_jobs()
        opened = open_run(launch)
        expires = clock() + launch.lease_seconds
        try:
            actors = _Actors(launch.token, scratch, can_execute,
                             {d.name for d in declarations if d.write_class.kind != "read-only"})
            dispatcher = Dispatcher(declarations, handlers, ctx, session=opened.session,
                                    selection=launch.config.default_project, run_inputs=scratch,
                                    on_invocation_close=actors.complete)
            control.queue(opened.open_report())
        except (OSError, EOFError):
            cause = "eof"
        except BaseException:
            opened.session.close()
            raise
        else:
            try:
                cause = _control_loop(control, server, wake, term, actors, dispatcher, launch.lease_seconds, expires, clock)
            except OSError:
                cause = "eof"
        return _shutdown(launch, opened, actors, control, cause, clock)
