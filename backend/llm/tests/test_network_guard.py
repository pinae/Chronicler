import socket

import pytest
from pytest_socket import SocketBlockedError


@pytest.mark.filterwarnings("ignore:A test tried to use socket")
def test_default_test_run_cannot_open_network_connections():
    with pytest.raises(SocketBlockedError):
        socket.create_connection(("192.0.2.1", 11434), timeout=1)
