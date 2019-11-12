# chatsystem

# Installation:
- install tornado
```sh
$ pip install tornado
```

- install yaml
```sh
$ pip install pyyaml
```

- install PyCrypto
```
$ pip install pycrypto
```

# Running the Chat
- prepare a config (in yml format) which supplies at least the paths to your ssl_cert and ssl_key. Those are mandatory. An example config is on github. The other config parameters are optional and should be left as in the example or omitted. If you change them, you might need to change the client code .
    - if you dont have a certificate and key, you can create a self signed one with the following command:
    ```sh
    openssl req -x509 -newkey rsa:4096 -keyout key.key -out cert.crt -days 365
    ```
- run the chat with:
```sh
$ python3 main.py -c /path/to/config.yml
```
- if your key is secured with a passphrase, you might be prompted to type it
