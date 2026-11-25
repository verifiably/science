import json
import socket
import threading

import pytest

from science.refusal import Refused


@pytest.mark.parametrize("reply,code", [
    ({"result": "admitted"}, None),
    ({"result": "already-recorded", "state": "reserved"}, "allowance-scope"),
    ({"result": "refused", "code": "allowance-closed"}, "allowance-closed"),
    ({"result": "admitted", "extra": True}, "allowance-unavailable"),
    ({"version": "bad", "result": "admitted"}, "allowance-unavailable"),
    ({"result": "settled"}, "allowance-unavailable"),
])
def test_reserve_round_trip_requires_a_matching_first_admission(reply, code):
    from science.run_endpoint.allowance import JobAdmission
    host, delegate = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    seen = []
    def respond():
        with host:
            request = json.loads(host.recv(16384))
            seen.append(request)
            host.send(json.dumps({"version": "allowance.v1", "id": request["id"], **reply}).encode())
    with delegate:
        worker = threading.Thread(target=respond)
        worker.start()
        try:
            client = JobAdmission(delegate)
            if code is None:
                client.reserve("A", "original")
            else:
                with pytest.raises(Refused) as error:
                    client.reserve("A", "original")
                assert error.value.refusal.code == code
        finally:
            delegate.shutdown(socket.SHUT_RDWR)
            worker.join(2)
    assert seen == [{"version": "allowance.v1", "id": 1, "op": "reserve-job",
                     "args": {"invocation_id": "A", "phase": "original"}}]
