"""Программа-клиент"""

import sys
import json
import socket
import time
import logging
import logs.config_client_log
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT, SENDER, MESSAGE, MESSAGE_TEXT, DESTINATION, EXIT
from common.utils import get_message, send_message
import argparse
import threading
from errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError
from decos import log

LOGGER = logging.getLogger('client')


@log
def create_exit_message(account_name):
    """Функция создаёт словарь с сообщением о выходе"""
    return {
        ACTION: EXIT,
        TIME: time.time(),
        ACCOUNT_NAME: account_name
    }


@log
def message_from_server(sock, my_username):
    """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
    while True:
        try:
            message = get_message(sock)
            if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                    and MESSAGE_TEXT in message and message[DESTINATION] == my_username:
                print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                      f'\n{message[MESSAGE_TEXT]}')
                LOGGER.info(f'Получено сообщение от пользователя '
                            f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
            else:
                LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
        except IncorrectDataRecivedError:
            LOGGER.error(f'Не удалось декодировать полученное сообщение.')
        except (OSError, ConnectionError, ConnectionAbortedError,
                ConnectionResetError, json.JSONDecodeError):
            LOGGER.critical(f'Потеряно соединение с сервером.')
            break


@log
def create_message(sock, account_name='Guest'):
    """Функция запрашивает текст сообщения и возвращает его.
    Так же завершает работу при вводе команды
    """
    to_user = input('Введите имя получателя сообщения: ')
    message = input('Введите сообщение: ')
    message_dict = {
        ACTION: MESSAGE,
        SENDER: account_name,
        DESTINATION: to_user,
        TIME: time.time(),
        MESSAGE_TEXT: message
    }
    LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
    try:
        send_message(sock, message_dict)
        LOGGER.info(f'Отправлено сообщение пользователю {to_user}')
    except:
        LOGGER.critical('Потеряно соединение с сервером.')
        sys.exit(1)


def print_help():
    """Функция выводит справку по использованию"""
    print('Поддерживаемые команды:')
    print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
    print('help - вывести подсказки по командам')
    print('exit - выход из программы')


@log
def user_interactive(sock, username):
    """Функция запрашивает команды, отправляет сообщения"""
    print_help()
    while True:
        command = input('Введите команду: ')
        if command == 'message':
            create_message(sock, username)
        elif command == 'help':
            print_help()
        elif command == 'exit':
            send_message(sock, create_exit_message(username))
            print('Завершение соединения.')
            LOGGER.info('Завершение работы по команде пользователя.')
            # Задержка необходима, чтобы успело уйти сообщение о выходе
            time.sleep(0.5)
            break
        else:
            print('Команда не распознана. help - вывести поддерживаемые команды.')


@log
def create_presence(account_name):
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
    LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
    return out


@log
def process_ans(message) -> object:
    """
    Функция разбирает ответ сервера
    :param message:
    :return:
    """
    LOGGER.debug(f'Разбор сообщения от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


@log
def create_arg_parser():
    """Парсер аргументов командной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    # проверим подходящий номер порта
    if not 1023 < server_port < 65536:
        LOGGER.critical(f'Запуск клиента с не правильным номером порта: {server_port}. '
                        f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    LOGGER.info(f'Запущен клиент с парамерами: адрес сервера: '
                f'{server_address}, порт: {server_port}')

    return server_address, server_port, client_name


def main():
    """Загружаем параметры командной строки"""
    # client.py 192.168.0.100 8079
    server_address, server_port, client_name = create_arg_parser()

    # Если имя пользователя не было задано, необходимо запросить пользователя.
    if not client_name:
        client_name = input('Введите имя пользователя: ')

    LOGGER.info(
        f'Запущен клиент: адрес сервера: {server_address}, '
        f'порт: {server_port}, имя клиента: {client_name}')

    # Инициализация сокета и обмен
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_ans(get_message(transport))
        LOGGER.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        #print(f'Установлено соединение с сервером {client_name}.')
        # print(answer)
    except (ConnectionRefusedError, ConnectionError):  # Если сервер не запущен, выдать предупреждение,а не вылетит с ошибкой
        # print('Сервер не отвечает')
        LOGGER.critical(f'Не удалось подключиться к серверу {server_address}:{server_port}, '
                        f'сервер отверг запрос на подключение.')
        sys.exit(1)
    except json.JSONDecodeError:
        # print('Не удалось декодировать сообщение сервера.')
        LOGGER.error('Не удалось декодировать полученную Json строку.')
        sys.exit(1)
    except ReqFieldMissingError as missing_error:
        LOGGER.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        sys.exit(1)
    except ServerError as error:
        LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        sys.exit(1)
    else:
        # Если соединение с сервером установлено корректно, начинаем обмен с ним, согласно требуемому режиму.
        receiver = threading.Thread(target=message_from_server, args=(transport, client_name))
        receiver.daemon = True
        receiver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        user_interface = threading.Thread(target=user_interactive, args=(transport, client_name))
        user_interface.daemon = True
        user_interface.start()
        LOGGER.debug('Запущены процессы')

        # Watchdog основной цикл, если один из потоков завершён,
        # то значит или потеряно соединение или пользователь ввёл exit.
        # Поскольку все события обрабатываются в потоках, достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
