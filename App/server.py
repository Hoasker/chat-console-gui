#  Сервер для обработки сообщений от клиентов
#
from twisted.internet import reactor
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.protocol import ServerFactory, connectionDone


class History:
    # Было ли прочитано сообщение
    viewer: list
    # Текст сообщения
    content: str

    def __init__(self, viewer: list, content: str):
        self.viewer = viewer
        self.content = content


class Client(LineOnlyReceiver):
    """Класс для обработки соединения с клиентом сервера"""

    delimiter = "\n".encode()  # \n для терминала, \r\n для GUI

    # указание фабрики для обработки подключений
    factory: 'Server'

    # информация о клиенте
    ip: str
    login: str = None
    logins = []


    def connectionMade(self):
        """
        Обработчик нового клиента

        - записать IP
        - внести в список клиентов
        - отправить сообщение приветствия
        """

        self.ip = self.transport.getPeer().host  # записываем IP адрес клиента
        self.factory.clients.append(self)  # добавляем в список клиентов фабрики
        self.sendLine("[ ! ] Welcome to the chat!".encode())  # отправляем сообщение клиенту
        print(f"[ + ] Client {self.ip} connected.")  # отображаем сообщение в консоли сервера

    def connectionLost(self, reason=connectionDone):
        """
        Обработчик закрытия соединения

        - удалить из списка клиентов
        - вывести сообщение в чат об отключении
        """

        self.factory.clients.remove(self)  # удаляем клиента из списка в фабрике
        print(f"[ - ] Client {self.ip} disconnected.")  # выводим уведомление в консоли сервера


    def send_history(self):
        '''
        Определение непрочитанных сообщений
        и отправка их текущему пользователю.
        '''
        history_messages = []
        
        for msg in self.factory.messages:
            users = []
            for user in msg.viewer:
                users.append(user.login)
 
            if self.login not in users:
                history_messages.append(msg)

        msg_count = len(history_messages)
        if msg_count > 0:
            self.transport.write(f'[ ! ] You have {msg_count} new messages:\n'.encode())
            for msg in history_messages:
                self.transport.write((f'[ * ] ' + msg.content + '\n').encode())
                msg.viewer.append(self)
        else:
            self.transport.write('[ ! ] There is no new messages.\n'.encode())


    def lineReceived(self, line: bytes):
        """
        Обработчик нового сообщения от клиента
        - зарегистрировать, если это первый вход, уведомить чат
        - переслать сообщение в чат, если уже зарегистрирован
        """

        message = line.decode()  # раскодируем полученное сообщение в строку

        # если логин еще не зарегистрирован
        if self.login is None:
            if message.startswith("[ + ] login:"):  # проверяем, чтобы в начале шел login:
                self.login = message.replace("[ + ] login:", "")  # вырезаем часть после :
                if self.logins.count(self.login)!=0:
                    self.transport.write(f"[ - ] Login {self.logins} is busy, try another...\n".encode())
                    reactor.callLater(0.5, self.transport.loseConnection)
                else:
                    self.logins.append(self.login)
                    notification = f"[ + ] New user: {self.login}"  # формируем уведомление о новом клиенте
                    self.factory.notify_all_users(notification)  # отсылаем всем в чат
                    self.send_history() #  Отправка последних сообщений 
            else:
                self.sendLine("[ ! ] Invalid login!".encode())  # шлем уведомление, если в сообщении ошибка
                reactor.callLater(0.5, self.transport.loseConnection)
        # если логин уже есть и это следующее сообщение
        else:
            format_message = f"{self.login}: {message}"  # форматируем сообщение от имени клиента

            # отсылаем всем в чат и в консоль сервера
            self.factory.notify_all_users(format_message)
            print(format_message)
            clients = self.factory.clients.copy()
            msg = History(clients, format_message)
            # Добавляем объект сообщения в список фабрики.
            self.factory.messages.append(msg)





class Server(ServerFactory):
    """Класс для управления сервером"""

    clients: list  # список клиентов
    protocol = Client  # протокол обработки клиента
    messages: list


    def __init__(self):
        """
        Старт сервера

        - инициализация списка клиентов
        - вывод уведомления в консоль
        """

        self.clients = []  # создаем пустой список клиентов
        self.messages = []
        print("*" * 10, "Server started - [OK]", "*" * 10)  # уведомление в консоль сервера


    def startFactory(self):
        """Запуск прослушивания клиентов (уведомление в консоль)"""

        print("[ * ] Start listening ...")  # уведомление в консоль сервера


    def notify_all_users(self, message: str):
        """
        Отправка сообщения всем клиентам чата
        :param message: Текст сообщения
        """

        data = message.encode()  # закодируем текст в двоичное представление
        # отправим всем подключенным клиентам
        for user in self.clients:
            user.sendLine(data)


if __name__ == '__main__':
    # параметры прослушивания
    reactor.listenTCP(
        7410,
        Server()
    )

    # запускаем реактор
    reactor.run()
