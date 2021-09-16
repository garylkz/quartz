from logging import getLogger, ERROR
from time import sleep
from threading import Thread
from urllib.request import urlopen

from flask import Flask

__all__ = ['up']
app = Flask('')


@app.route('/')
def home():
    return 'Q bot up!'


def run():
    app.run(host='0.0.0.0', port=8080)


def ping(target, debug):
    while True:
        r = urlopen(target)
        if debug: print(f'Status Code: {r.getcode()}')
        sleep(30 * 60)


def up(url, debug=False):
    log = getLogger('werkzeug')
    log.setLevel(ERROR)
    Thread(target=run).start()
    Thread(target=ping, args=(url, debug,)).start()