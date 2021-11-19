==================
sshtunnel-requests
==================


Install
-------

.. code:: shell

  $ pip install sshtunnel-requests


Usage
-----

.. code:: python

  import sshtunnel_requests

  stlrequests = sshtunnel_requests.from_url(
      'ssh://username@host:port', '<path>/<to>/private_key')

  resp = stlrequests.get('http://httpbin.org/ip')
  print(resp.status_code)
  # 200
  print(resp.json())
  # public IP of ssh-server machine


reused created tunnel to request more then once:

.. code:: python

  import sshtunnel_requests

  stlrequests = sshtunnel_requests.from_url(
      'ssh://username@host:port', '<path>/<to>/private_key')

  urls = [f'http://example.com/items-list?page={i}' for i in range(1, 5)]
  for url in urls:
      resp = stlrequests.get(url)
      print(resp.json())


thread example:

.. code:: python

  # TODO


use session:

.. code:: python

  # TODO



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
