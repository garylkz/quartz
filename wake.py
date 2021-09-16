from logging import getLogger, ERROR
from time import sleep
from threading import Thread
from urllib.request import urlopen

from flask import Flask
from replit import info

__all__ = ['up']

app = Flask('')
home = app.route('/')(lambda: 'Bot is up!')
run = lambda: app.run(host='0.0.0.0', port=8080),
ping = lambda: (urlopen(info.co_url), sleep(5 * 60), ping())


def up(debug: bool = False) -> None:
    getLogger('werkzeug').setLevel(ERROR)
    for f in [run, ping]: Thread(target=f).start()
