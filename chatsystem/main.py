# -*- coding: utf-8 -*-
import tornado.ioloop
import tornado.web
import tornado.websocket
import json
import uuid
import sys
sys.path.append(__file__)
import ssl
import argparse
import params
from logic import get_lobbypool, User
from Crypto.PublicKey import RSA
from crypter import get_rsa_crypter
from base64 import b64encode


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class WebSocket(tornado.websocket.WebSocketHandler):
    id = -1
    name = ""
    connections = set()
    public_key = None
    storage = {}

    def open(self):
        self.connections.add(self)

    def on_message(self, message):
        message = json.loads(message)
        print(message)
        if 'type' in message:
            if message['type'] == 'login':
                self.name = message['name']
                self.id = uuid.uuid4()
                self.public_key = RSA.importKey(message['public_key'])

                rsa_crypter = get_rsa_crypter()
                self.write_message({'type': 'public_key_response',
                                    'public_key': rsa_crypter.rsa_public_key_to_string()})

                lobbypool = get_lobbypool()
                active_lobbies = lobbypool.get_active_lobbies()
                self.broadcast({'type': 'active_lobbies',
                                'lobby_info': active_lobbies})
            elif message['type'] == 'open_lobby':
                lobbypool = get_lobbypool()
                lobby_id = lobbypool.open_lobby(User(self.id, self.name), self)
                aes_key = lobbypool.get_lobby(lobby_id).get_aes_key()
                aes_iv = lobbypool.get_lobby(lobby_id).get_aes_iv()

                rsa_crypter = get_rsa_crypter()

                self.write_message({'type': 'open_lobby_response',
                                    'lobby_id': lobby_id,
                                    'aes_info': {
                                        'key': b64encode(rsa_crypter.encrypt_client_pubkey(self.public_key, b64encode(aes_key).decode())).decode(),
                                        'iv': b64encode(rsa_crypter.encrypt_client_pubkey(self.public_key, b64encode(aes_iv).decode())).decode()}
                                    })
                lobbypool.get_lobby(lobby_id).send_user_list()
            elif message['type'] == 'join_lobby':
                lobbypool = get_lobbypool()
                lobby_id = message['lobby_id']
                lobby_id = lobbypool.join_lobby(User(self.id, self.name), int(lobby_id))

                aes_key = lobbypool.get_lobby(lobby_id).get_aes_key()
                aes_iv = lobbypool.get_lobby(lobby_id).get_aes_iv()

                rsa_crypter = get_rsa_crypter()

                self.write_message({'type': 'join_lobby_response',
                                    'lobby_id': lobby_id,
                                    'aes_info': {
                                        'key': b64encode(rsa_crypter.encrypt_client_pubkey(self.public_key, b64encode(aes_key).decode())).decode(),
                                        'iv': b64encode(rsa_crypter.encrypt_client_pubkey(self.public_key, b64encode(aes_iv).decode())).decode()}
                                    })
                lobbypool.get_lobby(lobby_id).send_user_list()
            elif message['type'] == 'chat_message':
                lobbypool = get_lobbypool()
                lobby_id = message['lobby_id']
                lobbypool.get_lobby(lobby_id).broadcast_message(message)
            elif message['type'] == 'get_active_lobbies': # explicit request from client to get Lobbies, only send it to him
                lobbypool = get_lobbypool()
                active_lobbies = lobbypool.get_active_lobbies()
                self.write_message({'type': 'active_lobbies',
                                    'lobby_info': active_lobbies})

    def on_close(self):
        self.connections.remove(self)

    def broadcast(self, message):
        for client in self.connections:
            client.write_message(message)

    def broadcast_lobby(self, message, lobby_id):
        for client in self.connections:
            if client.name in self.storage[lobby_id]:
                client.write_message(message)


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/websocket", WebSocket),
        (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": "./css/"},),
        (r"/img/(.*)", tornado.web.StaticFileHandler, {"path": "./img/"},),
    ])


def set_params(config):
    if config:
        if 'aes_blocksize' in config:
            params.AES_BLOCKSIZE = config['aes_blocksize']
        if 'aes_keylength' in config:
            params.AES_KEYLENGTH = config['aes_keylength']
        if 'rsa_keylength' in config:
            params.RSA_KEYLENGTH = config['rsa_keylength']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, help="path to config file")
    args = parser.parse_args()

    ssl_ctx = None

    if args.config:
        config = json.load(open(args.config))
        set_params(config)
        if ('ssl_cert' in config) and ('ssl_key' in config):
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(config['ssl_cert'], config['ssl_key'])
        else:
            print('missing ssl_cert or ssl_key in the config or an error occured when reading the file')
            sys.exit(-1)
    else:
        print('config not supplied or an error occured when reading the file')
        sys.exit(-1)

    app = make_app()
    server = tornado.httpserver.HTTPServer(app, ssl_options=ssl_ctx,)
    server.listen(8888)
    tornado.ioloop.IOLoop.current().start()
