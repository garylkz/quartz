import json
from threading import Thread
import time

from quartz import api, card


def all(legacy: bool = False) -> None:
    cards = api.get_update_cards(1574969089362)
    card.update(cards, legacy=legacy)


def epoch() -> None:
    data = json.load(open('data.json', encoding='utf-8'))
    cards = api.get_update_cards(data['epoch'])
    card.update(cards)


def schedule(*, interval: int = 60*60*24, thread: bool = False) -> None:
    def f():
        while True:
            epoch()
            time.sleep(interval)

    if thread: 
        Thread(target=f).start()
    else: 
        f()