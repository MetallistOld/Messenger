"""Программа-сервер"""
import socket
import sys
import json
import logging
import logs.config_server_log
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, DEFAULT_IP_ADDRESS
from common.utils import get_message, send_message

SERVER_LOGGER = logging.getLogger('server')

def process_client_message(message):
    """
    Обработчик сообщений от клиентов, принимает словарь -
    сообщение от клинта, проверяет корректность,
    возвращает словарь-ответ для клиента

    :param message:
    :return:
    """
    SERVER_LOGGER.debug(f'Разбор сообщения от клиента : {message}')
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
            and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
        return {RESPONSE: 200}
    return {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }

def main():
    """
    Загрузка параметров командной строки, если нет параметров, то задаём значения по умолчанию.
    Сначала обрабатываем порт:
    server.py -p 8079 -a 192.168.0.100
    :return:
    """
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = DEFAULT_PORT
        # print(listen_port)
        if listen_port < 1024 or listen_port > 65535:
            SERVER_LOGGER.critical(f'Попытка запуска сервера с указанием неподходящего порта '
                                   f'{listen_port}. Допустимы адреса с 1024 до 65535.')
            sys.exit(1)
            # raise ValueError
    except IndexError:
        SERVER_LOGGER.critical('После параметра -\'p\' необходимо указать номер порта')
        # print('После параметра -\'p\' необходимо указать номер порта')
        sys.exit(1)
    # except ValueError:
    #     print('В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
    #     sys.exit(1)

    # Затем загружаем какой адрес слушать

    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = DEFAULT_IP_ADDRESS
        # print(listen_address)
    except IndexError:
        SERVER_LOGGER.critical('После параметра \'a\'- необходимо указать адрес, который будет слушать сервер.')
        # print(
        #     'После параметра \'a\'- необходимо указать адрес, который будет слушать сервер.')
        sys.exit(1)

    SERVER_LOGGER.info(f'Запущен сервер, порт для подключений: {listen_port}, '
                           f'адрес подключения: {listen_address}. ')
    # Готовим сокет

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_address, listen_port))

    # Слушаем порт

    transport.listen(MAX_CONNECTIONS)

    while True:
        client, client_address = transport.accept()
        SERVER_LOGGER.info(f'Установлено соедение с ПК {client_address}')
        try:
            message_from_cient = get_message(client)
            SERVER_LOGGER.debug(f'Получено сообщение {message_from_cient}')
            response = process_client_message(message_from_cient)
            SERVER_LOGGER.info(f'Cформирован ответ клиенту {response}')
            send_message(client, response)
            SERVER_LOGGER.debug(f'Соединение с клиентом {client_address} закрывается.')
            client.close()
            # message_from_client = get_message(client)
            # print(message_from_client)
            # response = process_client_message(message_from_client)
            # send_message(client, response)
            # client.close()
        except (ValueError, json.JSONDecodeError):
            SERVER_LOGGER.error(f'От клиента {client_address} приняты некорректные данные. '
                                f'Соединение закрывается.')
            client.close()
            # print('Принято некорректное сообщение от клиента.')
            # client.close()


if __name__ == '__main__':
    main()
