==================
sshtunnel-requests
==================


.. image:: https://github.com/featureoverload/sshtunnel-requests/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/featureoverload/sshtunnel-requests/actions?query=workflow%3Aci

.. image:: https://img.shields.io/pypi/v/sshtunnel-requests.svg
   :target: https://pypi.org/project/sshtunnel-requests

.. image:: https://img.shields.io/github/license/featureoverload/sshtunnel-requests.svg
   :target: https://github.com/featureoverload/sshtunnel-requests/blob/main/LICENSE

.. image:: https://readthedocs.org/projects/sshtunnel-requests/badge/?version=latest
        :target: https://sshtunnel-requests.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


Install
-------

.. code:: shell

  $ pip install sshtunnel-requests


Usage
-----

.. code:: python

  import sshtunnel_requests

  requests = sshtunnel_requests.from_url(
      'ssh://username@host:port', '<path>/<to>/private_key')

  resp = requests.get('http://httpbin.org/ip')
  print(resp.status_code)
  # 200
  print(resp.json())
  # public IP of ssh-server machine


reused created tunnel to request more then once:

.. code:: python

  import sshtunnel_requests

  requests = sshtunnel_requests.from_url(
      'ssh://username@host:port', '<path>/<to>/private_key')

  urls = [
      'http://httpbin.org/headers',
      'http://httpbin.org/ip',
      'http://httpbin.org/user-agent',
      'http://httpbin.org/uuid',
  ]
  for url in urls:
      resp = requests.get(url)
      print(resp.json())


thread example:

.. code:: python

  import sshtunnel_requests

  requests = sshtunnel_requests.from_url(
      "ssh://<username>@<ssh server host>[:<port>]",
      "<path>/<to>/<private key>"
  )

  urls = [
      'http://httpbin.org/headers',
      'http://httpbin.org/ip',
      'http://httpbin.org/user-agent',
      'http://httpbin.org/uuid',
  ]

  from concurrent.futures import ThreadPoolExecutor
  from concurrent.futures import as_completed

  results = []
  with ThreadPoolExecutor(max_workers=3) as pool:
      futures = []
      for url in urls:
          f = pool.submit(
              lambda _req, _url: _req.get(_url),
              requests, url
          )
          futures.append(f)
      done_iter = as_completed(futures)
      for future in done_iter:
          response = future.result()
          results.append(response.json())

  from pprint import pp
  for result in results:
      pp(result)

use session:

.. code:: python

  import sshtunnel_requests

  session = sshtunnel_requests.Session.from_url(
      "ssh://<username>@<ssh server host>[:<port>]",
      "<path>/<to>/<private key>"
  )

  assert session.cookies.values() == list()
  resp = session.get(
      'http://httpbin.org/cookies/set/sessioncookie/123456789'
  )
  assert resp.json() == {'cookies': {'sessioncookie': '123456789'}}
  assert session.cookies.values() == ['123456789']
  resp = session.get('http://httpbin.org/ip')
  assert 'Cookie' in resp.request.headers
  assert resp.request.headers['Cookie'] == 'sessioncookie=123456789'
  print(resp.json())
  # public IP of ssh-server machine


Features
--------

- simply use `sshtunnel` and `requests` to request HTTP server in internal networking.
- caching ssh tunnel connection to reused next requests of the same server.
- automatic release connection if the ssh tunnel connection has not been used some time
  (without any consideration of memory leak and fd leak)
- (thread) concurrent support of the same connection.

Test
----

.. code:: shell

  $ cd e2e_tests && docker-compose up -d; cd ..
  $
  $ `which python` -m pip install -U pip
  $ pip install .
  $ pip install -r requirements_test.txt
  $
  $ # cd e2e_tests && docker-compose logs ssh; cd ..
  $ # cd e2e_tests && docker-compose exec ssh cat /config/logs/openssh/current; cd ..
  $ chmod 600 ./e2e_tests/ssh-server-config/ssh_host_rsa_key
  $ # ssh -o "StrictHostKeyChecking=no" linuxserver@127.0.0.1 -p 2223 -i ./e2e_tests/ssh-server-config/ssh_host_rsa_key -v "uname -a"
  $ pytest e2e_tests
