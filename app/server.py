"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports
from collections import deque


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").strip()

                if login not in self.server.clients:
                    self.server.clients[login] = self
                    self.login = login
                    self.send_history()
                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
                else:
                    self.transport.write(
                        f"Логин {login} занят, попробуйте другой".encode()
                    )
                    self.transport.close()
            else:
                self.transport.write(
                    "Залогиньтесь, чтобы писать сообщения".encode()
                )
        else:
            message = self.format_message(decoded)
            self.update_history(message)
            self.send_message(message)

    def format_message(self, message):
        return f"<{self.login}> {message}"

    def update_history(self, message):
        self.server.history.append(message)

    def send_history(self):
        for message in self.server.history:
            self.transport.write(message.encode())

    def send_message(self, message):
        encoded = message.encode()

        for login, client in self.server.clients.items():
            if login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        print("Соединение установлено")

    def connection_lost(self, exception):
        if self.login:
            self.server.clients.pop(self.login)
        print("Соединение разорвано")


class Server:
    clients: dict
    history: deque

    def __init__(self):
        self.clients = {}
        self.history = deque(maxlen=10)

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_event_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        return coroutine


loop = asyncio.get_event_loop()
server = loop.run_until_complete(Server().start())

print("Сервер запущен ...")

try:
    loop.run_forever()
except KeyboardInterrupt:
    print("Сервер остановлен вручную")

server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
