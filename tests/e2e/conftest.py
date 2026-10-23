import pytest
from helpers import serve


@pytest.fixture
def image_server():
    servers = []

    def _start(routes):
        srv = serve(routes)
        servers.append(srv)
        return f"http://127.0.0.1:{srv.server_port}"

    yield _start
    for s in servers:
        s.shutdown()
        s.server_close()
