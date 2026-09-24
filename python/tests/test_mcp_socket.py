"""Decision 6: both launchers serve the whole service protocol on the socket."""
import io
import json
import os
import socket
import threading
import time

import pytest

from helpers.world import write_cli_config


class _BlockingStdin(io.RawIOBase):
    """Stdin that stays open until released, so the MCP server keeps running."""
    def __init__(self):
        self._read, self._write = os.pipe()

    def readable(self):
        return True

    def readinto(self, buffer):
        data = os.read(self._read, len(buffer))
        buffer[:len(data)] = data
        return len(data)

    def release(self):
        os.close(self._write)


def _wait_for(path, timeout=30):
    deadline = time.monotonic() + timeout
    while not path.exists():
        if time.monotonic() > deadline:
            raise AssertionError(f"{path} never appeared")
        time.sleep(0.05)


def _request(path, payload):
    with socket.socket(socket.AF_UNIX) as client:
        client.connect(str(path))
        client.sendall(json.dumps(payload).encode() + b"\n")
        return json.loads(client.makefile().readline())


def test_mcp_serve_accepts_cli_writes_on_the_socket_and_blocks_a_second_launcher(certified_work, short_tmp):
    from science.config import load_config
    from science.mcp import serve as mcp_serve
    from science.refusal import Refused
    from science.serve import serve as service_serve

    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)
    stdin = _BlockingStdin()
    thread = threading.Thread(target=mcp_serve, args=(config_path,),
                              kwargs={"stdin": io.BufferedReader(stdin), "stdout": io.StringIO(),
                                      "stderr": io.StringIO()}, daemon=True)
    thread.start()
    try:
        _wait_for(sock)
        reply = _request(sock, {"command": "project",
                                "inputs": {"name": "via-socket",
                                           "query": "version: science.view-query.v1\nclauses: []\n"}})
        assert reply["ok"] and "[project]" in reply["text"]
        with pytest.raises(Refused) as caught:
            service_serve(load_config(config_path), sock)
        assert "socket already exists" in caught.value.refusal.message
    finally:
        stdin.release()
        thread.join(timeout=30)
    assert not thread.is_alive()
    assert not sock.exists()  # clean shutdown removed it


def test_mcp_socket_teardown_failure_still_closes_the_session(certified_work, short_tmp, monkeypatch):
    import socketserver

    from science.config import load_config
    from science.mcp import serve as mcp_serve

    config_path = write_cli_config(certified_work, service_socket=short_tmp / "service.sock")

    def boom(self):
        raise OSError("teardown failed")

    monkeypatch.setattr(socketserver.ThreadingUnixStreamServer, "server_close", boom)
    with pytest.raises(OSError):
        mcp_serve(config_path, stdin=io.BytesIO(), stdout=io.StringIO(), stderr=io.StringIO())
    ledgers = list((load_config(config_path).operations_root / "sessions").glob("*/ledger.v1"))
    assert len(ledgers) == 1
    assert json.loads(ledgers[0].read_text().splitlines()[-1])["line"] == "session-close"
