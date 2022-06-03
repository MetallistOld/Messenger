"""Программа-сервер"""
import socket
import sys
import json
import logging
import logs.config_server_log
from errors import IncorrectDataRecivedError
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, DEFAULT_IP_ADDRESS
from common.utils import get_message, send_message
import argparse
from decos import log

LOGGER = logging.getLogger('server')


@log
def process_client_message(message):
    """
    Обработчик сообщений от клиентов, принимает словарь -
    сообщение от клинта, проверяет корректность,
    возвращает словарь-ответ для клиента

    :param message:
    :return:
    """
    LOGGER.debug(f'Разбор сообщения от клиента : {message}')
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
            and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
        return {RESPONSE: 200}
    return {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }


@log
def create_arg_parser():
    """Парсер аргументов командной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    return parser


def main(listen_address=None):
    """
    Загрузка параметров командной строки, если нет параметров, то задаём значения по умолчанию.
    Сначала обрабатываем порт:
    server.py -p 8079 -a 192.168.0.100
    :return:
    """

    """Загрузка параметров командной строки, если нет параметров, то задаём значения по умолчанию"""
    parser = create_arg_parser()
    namespace = parser.parse_args(sys.argv[1:])
    if namespace.a == '':
        listen_address = DEFAULT_IP_ADDRESS
    else:
        listen_address = namespace.a
    listen_port = namespace.p

    # проверка получения корректного номера порта для работы сервера.
    if not 1023 < listen_port < 65536:
        LOGGER.critical(f'Попытка запуска сервера с указанием неподходящего порта {listen_port}. '
                        f'Допустимы адреса с 1024 до 65535.')
        sys.exit(1)
    LOGGER.info(f'Сервер запущен по адресу: {listen_address}, порт для подключений: {listen_port}')

    # Готовим сокет

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_address, listen_port))

    # Слушаем порт

    transport.listen(MAX_CONNECTIONS)

    while True:
        client, client_address = transport.accept()
        LOGGER.info(f'Установлено соединение с ПК {client_address}')
        try:
            message_from_client = get_message(client)
            LOGGER.debug(f'Получено сообщение {message_from_client}')
            response = process_client_message(message_from_client)
            LOGGER.info(f'Сформирован ответ клиенту {response}')
            send_message(client, response)
            LOGGER.debug(f'Соединение с клиентом {client_address} закрывается.')
            client.close()
        except (ValueError, json.JSONDecodeError):
            LOGGER.error(f'От клиента {client_address} получена не корректная Json строка . '
                         f'Соединение закрывается.')
            client.close()
        except IncorrectDataRecivedError:
            LOGGER.error(f'От клиента {client_address} приняты некорректные данные. '
                         f'Соединение закрывается.')
            client.close()


if __name__ == '__main__':
    main()
