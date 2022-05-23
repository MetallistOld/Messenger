"""
Задание 5.

Выполнить пинг веб-ресурсов yandex.ru, youtube.com и
преобразовать результаты из байтовового в строковый тип на кириллице.

Подсказки:
--- используйте модуль chardet, иначе задание не засчитается!!!
"""
import subprocess
import chardet


def ping_site(name_site):
    site_ping = subprocess.Popen(name_site, stdout=subprocess.PIPE)
    for line in site_ping.stdout:
        result = chardet.detect(line)
        print(result)
        line = line.decode(result['encoding']).encode('utf-8')
        print(line.decode('utf-8'))


ARGS_1 = ['ping', 'yandex.ru']
ARGS_2 = ['ping', 'youtube.com']

ping_site(ARGS_1)
ping_site(ARGS_2)
