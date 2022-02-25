import logging
import requests
from typing import List, Union


API = 'https://eucalyptus-production-master-services-us.cloud.virttrade.com/rest/album/card'


def get(path: str) -> Union[dict, list]:
    return requests.get(f'{API}/{path}').json()


def get_card(code: str) -> dict:
    return get(f'detail/{code}')


def get_cards(codes: List[str], size: int = 500) -> List[dict]:
    session = requests.Session() # Initialize a request session
    g = lambda x : session.get(f'{API}/{x}').json()

    cards = []
    for i in range(len(codes)):
        if i > 0 and i % size == 0: 
            session.close() 
            session = requests.Session()
        logging.info(f'{i}:{codes[i]}')
        card = g(f'detail/{codes[i]}')
        cards.append(card)
    return cards


def get_updates(since: int) -> List[str]:
    return get(f'updateList/{since}')


def get_card_updates(since: int, size: int = 500) -> List[dict]:
    codes = get_updates(since)
    logging.info(f'{len(codes)} card(s)')
    return get_cards(codes, size)
