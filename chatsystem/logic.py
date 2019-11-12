import json
import params
from Crypto import Random
from Crypto.Cipher import AES
from crypter import AES_Crypter
from base64 import b64encode, b64decode


class Lobby:
    def __init__(self, id, first_user, socket):
        self.id = id
        self.users = []
        self.socket = socket
        self.socket.storage[self.id] = list()
        self.add_user(first_user)
        self.aes_key = Random.new().read(params.AES_KEYLENGTH)
        self.aes_iv = Random.new().read(AES.block_size)

    def get_aes_key(self):
        return self.aes_key

    def get_aes_iv(self):
        return self.aes_iv

    def decipher_chat_message(self, ciphertext):
        crypter = AES_Crypter()
        decrypted = crypter.decrypt(b64decode(ciphertext))
        return decrypted.decode()

    def broadcast_message(self, message):
        """
        broadcasts a message to every other member of this chatroom
        :param message: the message to broadcast. if it is a dictionary, it will
                        be automatically converted to JSON, else suppy a json
                        dumped string yourself using json.dumps()
        :type message: Varies
        .. note:: messages do not neccessarily have to be in JSON format, as
                  long as your clients can handle it. but as a matter of
                  convention it is suggested
        """

        self.socket.broadcast_lobby(message, self.id)

    def add_user(self, user):
        """
        adds a user to this lobby. Also adds the user to socket handlers internal
        storage to identify which client belongs to which chatroom.
        :param user: the user to be added
        :type user: User
        .. seealso:: :class: `User`
        .. todo:: check type of user
        """
        self.users.append(user)
        self.socket.storage[self.id].append(user.name)

    def remove_user(self, user):
        """
        removes a user from this lobby
        :param user: the user to be removed
        :type user: User
        .. seealso:: :class: `User`
        :raises: :class: `ValueError` of the underlying list, if the user is not present
        """
        self.users.remove(user)

    def send_user_list(self):
        """
        Broadcasts the list of users to all users of this chatroom. Purpose of
        this method is to update the display of active users on the clients.
        based on this information.
        In detail, the message looks like the following:
        .. code-block:: json
            {
              'type': 'lobby_user_list',
              'lobby_id': <id of this lobby>,
              'users': <[list of users in this lobby]>
            }
        """
        payload = {
            'type': 'lobby_user_list',
            'lobby_id': self.id,
            'users': [user.name for user in self.users]}
        self.broadcast_message(payload)


the_lobbypool = None
def get_lobbypool():
    global the_lobbypool
    if the_lobbypool is None:
        the_lobbypool = LobbyPool()
    return the_lobbypool


class LobbyPool:
    """
    Singleton that represents the Pool of active chatrooms.
    Never create an instance of this class, always use it statically with
    LobbyPool.<function()>
    Also avoid to create instances of Lobby yourself, because they won't show
    up in this pool and cannot be addressed unless per direct reference. If you
    need access to the lobby object, use the function get_lobby() of this
    LobbyPool.
    """

    def __init__(self):
        self.lobbies = {}

    def open_lobby(self, user, socket):
        """
        Opens a new chatroom and adds the user to it
        :param user: the user that wants to open a new lobby
        :type user: User
        :param socket: tornados Sockethandler
        :type socket: tornado.websocket.WebSocketHandler
        ..note:: currently there is a limit of 100 lobbies
        :returns: the lobby ID of the newly created lobby
        :rtype: int
        """
        for i in range(0, 100):
            if i not in self.lobbies:
                lobby = Lobby(i, user, socket)
                self.lobbies[i] = lobby
                return i

    def join_lobby(self, user, lobby_id):
        """
        Join a already opened chatroom via its ID
        :param user: the user to join the chatroom
        :type user: User
        :param lobby_id: the ID of the chatroom to join
        :type lobby_id: int
        :returns: the lobby ID
        :rtype: int
        """
        if lobby_id in self.lobbies:
            self.lobbies[lobby_id].add_user(user)
            return lobby_id

    def get_active_lobbies(self):
        """
        Returns a dictionary of all active chatrooms and their users.
        The format of the dict is:
        .. code-block:: javascript
            {
              <lobby_id> : <[list of usernames of this lobby]>
            }
        :returns: the dictionary containing the information
        :rtype: dict
        """
        data = {}
        for lobby in self.lobbies:
            data[lobby] = [user.name for user in self.lobbies[lobby].users]
        return data

    def get_lobby(self, lobby_id):
        """
        Returns the lobby object of the Chatroom associated with the given ID
        :param lobby_id: the ID of the desired object
        :type lobby_id: int
        :returns: The Lobby object associated with the given ID or None, if no
                  such lobby is present
        :rtype: Lobby, None
        """
        if lobby_id in self.lobbies:
            return self.lobbies[lobby_id]
        else:
            return None


class User:
    def __init__(self, id, name):
        self.id = id
        self.name = name
