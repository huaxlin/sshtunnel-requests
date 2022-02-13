import sshtunnel_requests

from const import *


class TestSSHTunnelRequests():

    def test_one_request(self):
        requests = sshtunnel_requests.Requests(host=SSH_SERVER_HOST,
                                               username=SSH_SERVER_USERNAME,
                                               port=SSH_SERVER_PORT,
                                               private_key=SSH_PKEY)
        resp = requests.get(f'http://{SSH_SERVER_REMOTE_SIDE_HOST_HTTPBIN}/ip')
        assert resp.json() == {'origin': '10.5.0.2'}

    def test_http_method(self, mocker):
        call_count = 0
        release_call_count = 0

        def mock__init__(self, tunnel_partial, remote_bind_address) -> None:
            nonlocal call_count
            call_count += 1
            import threading
            self.remote_bind_address = remote_bind_address
            self.tunnel_partial = tunnel_partial
            self._tunnel = None
            self.create_tunnel_connection_lock = threading.Lock()

        def mock__del__(self):
            nonlocal release_call_count
            release_call_count += 1
            if self._tunnel is not None:
                self._tunnel.close()

        mocker.patch('sshtunnel_requests.cache.Connection.__init__',
                     mock__init__)
        mocker.patch('sshtunnel_requests.cache.Connection.__del__', mock__del__)
        requests = sshtunnel_requests.Requests(host=SSH_SERVER_HOST,
                                               username=SSH_SERVER_USERNAME,
                                               port=SSH_SERVER_PORT,
                                               private_key=SSH_PKEY)
        url = f'http://{SSH_SERVER_REMOTE_SIDE_HOST_HTTPBIN}'

        for method in ['delete', 'get', 'patch', 'post', 'put']:
            _url = url + f'/{method}'
            fn = getattr(requests, method)
            response = fn(_url)

            assert response.status_code == 200
            expected_partial = {'origin': '10.5.0.2'}
            assert expected_partial.items() <= response.json().items()
        assert release_call_count >= call_count - 1, f'{release_call_count = }'
        assert call_count == 1, f'{release_call_count = }; {call_count = }'

    def test_many_requests_sequential(self, mocker):
        call_count = 0

        def mock__init__(self, tunnel_partial, remote_bind_address) -> None:
            nonlocal call_count
            call_count += 1
            import threading
            self.remote_bind_address = remote_bind_address
            self.tunnel_partial = tunnel_partial
            self._tunnel = None
            self.create_tunnel_connection_lock = threading.Lock()

        mocker.patch('sshtunnel_requests.cache.Connection.__init__',
                     mock__init__)
        requests = sshtunnel_requests.Requests(host=SSH_SERVER_HOST,
                                               username=SSH_SERVER_USERNAME,
                                               port=SSH_SERVER_PORT,
                                               private_key=SSH_PKEY)
        urls = [
            f'http://{SSH_SERVER_REMOTE_SIDE_HOST_HTTPBIN}{api}'
            for api in ('/headers', '/ip', '/user-agent', '/uuid')
        ]
        for url in urls:
            resp = requests.get(url)
            assert resp.status_code == 200
        assert call_count == 1

    def test_many_requests_concurrent(self, mocker):
        call_count = 0

        def mock__init__(self, tunnel_partial, remote_bind_address) -> None:
            nonlocal call_count
            call_count += 1
            import threading
            self.remote_bind_address = remote_bind_address
            self.tunnel_partial = tunnel_partial
            self._tunnel = None
            self.create_tunnel_connection_lock = threading.Lock()

        mocker.patch('sshtunnel_requests.cache.Connection.__init__',
                     mock__init__)
        requests = sshtunnel_requests.Requests(host=SSH_SERVER_HOST,
                                               username=SSH_SERVER_USERNAME,
                                               port=SSH_SERVER_PORT,
                                               private_key=SSH_PKEY)
        urls = [
            f'http://{SSH_SERVER_REMOTE_SIDE_HOST_HTTPBIN}{api}'
            for api in ('/headers', '/ip', '/user-agent', '/uuid')
        ]
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(requests.get, url) for url in urls]
            done_iter = as_completed(futures)
            for future in done_iter:
                response = future.result()
                assert response.status_code == 200
        assert call_count == 1


class TestFromURL():

    def test_one_requests(self):
        requests = sshtunnel_requests.from_url(SSH_URL, SSH_PKEY)
        resp = requests.get(f'http://{SSH_SERVER_REMOTE_SIDE_HOST_HTTPBIN}/ip')
        assert resp.json() == {'origin': '10.5.0.2'}
