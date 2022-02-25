import logging
import requests
from typing import List, Union


API = 'https://eucalyptus-production-master-services-us.cloud.virttrade.com/rest/album/card'


def get(path: str) -> Union[dict, list]:
    return requests.get(f'{API}/{path}').json()

def get_card(code: str) -> dict:
    return get(f'detail/{code}')

def get_updates(since: int) -> List[str]:
    return get(f'updateList/{since}')

def get_card_updates(since: int, size: int = 500) -> List[dict]:
    session = requests.Session()
    g = lambda x : session.get(f'{API}/{x}').json()
    codes = g(f'updateList/{since}')
    logging.info(f'{len(codes)} card(s)')
    cards = []
    for i in range(len(codes)):
        if i > 0 and i % size == 0:
            session.close()
            session = requests.Session()
        logging.info(f'{codes[i]}:{i}')
        card = g(f'detail/{codes[i]}')
        cards.append(card)
    return cards
