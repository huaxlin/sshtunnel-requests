import os

SSH_SERVER_HOST = '127.0.0.1'
SSH_SERVER_PORT = 2223
SSH_SERVER_USERNAME = 'linuxserver'
SSH_PKEY = os.path.join(os.path.dirname(__file__), 'ssh-server-config',
                        'ssh_host_rsa_key')
SSH_URL = f'ssh://{SSH_SERVER_USERNAME}@{SSH_SERVER_HOST}:{SSH_SERVER_PORT}'

SSH_SERVER_REMOTE_SIDE_HOST_HTTPBIN = '10.5.0.5'
