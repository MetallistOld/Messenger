"""Программа-клиент"""

import sys
import json
import socket
import time
import logging
import logs.config_client_log
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT
from common.utils import get_message, send_message

CLIENT_LOGGER = logging.getLogger('client')

def create_presence(account_name='Guest'):
    """
    Функция генерирует запрос о присутствии клиента
    :param account_name:
    :return:
    """
    # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
    return out


def process_ans(message):
    """
    Функция разбирает ответ сервера
    :param message:
    :return:
    """
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {message[ERROR]}'
    raise ValueError


def main():
    """Загружаем параметры командной строки"""
    # client.py 192.168.0.100 8079
    try:
        server_address = sys.argv[1]
        # print("address", server_address)
        server_port = int(sys.argv[2])
        # print(server_port)
        if server_port < 1024 or server_port > 65535:
            CLIENT_LOGGER.critical(
                f'Запуск клиента с неподходящим номером порта: {server_port}.'
                f' Допустимы адреса с 1024 до 65535.')
            sys.exit(1)
    except IndexError:
        server_address = DEFAULT_IP_ADDRESS
        server_port = DEFAULT_PORT
    # except ValueError:
    #     print('В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
    #     sys.exit(1)
    CLIENT_LOGGER.info(f'Запущен клиент с парамертами: адрес сервера: {server_address}, порт: {server_port}')

    # Инициализация сокета и обмен
    try:
        # print("address", server_address)
        # print(server_port)
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        message_to_server = create_presence()
        send_message(transport, message_to_server)
        answer = process_ans(get_message(transport))
        CLIENT_LOGGER.info(f'Принят ответ от сервера {answer}')
        # print(answer)
    except ConnectionRefusedError:  # Если сервер не запущен, выдать предупреждение,а не вылетит с ошибкой
        # print('Сервер не отвечает')
        CLIENT_LOGGER.critical(f'Не удалось подключиться к серверу {server_address}:{server_port}, '
                               f'сервер отверг запрос на подключение.')
        sys.exit(1)
    except (ValueError, json.JSONDecodeError):
        # print('Не удалось декодировать сообщение сервера.')
        CLIENT_LOGGER.error('Не удалось декодировать полученную Json строку.')


if __name__ == '__main__':
    main()
