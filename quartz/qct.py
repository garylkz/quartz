from datetime import datetime
import json
import logging
import os
import re
from threading import Thread
import time
from typing import List, Union

from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

from quartz import cue


__all__ = ['mass_update', 'scheduled_update']


# Constants
try:
    CREDS = json.load(open('creds.json'))
except FileNotFoundError:
    CREDS = json.loads(os.environ['CREDS'])
except OSError:
    raise Exception('Based, creds.json not found, CREDS not in os.environ')
SCOPE = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets'
]
IMG = 'https://cdn-virttrade-assets-eucalyptus.cloud.virttrade.com/filekey'
ID = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo' 
CARDS = 'Card List!A:N'
COLS = 'Collection!B:E'
DYKS = 'Do You Know'
FUSE = 'Fusion'
DEF_SUBS = {
    ':power:': '⚡',
    ':power/turn:': '⚡/turn',
    ':energy:': '🔋',
    ':energy/turn:': '🔋/turn',
    ':lock:': '🔒 ',
    ':burn:': '🔥 ',
    ':return:': '↩️ ',
    ':play:': '▶️ ',
    ':draw:': '⬆️ '
}


# Variables
try:
    data = json.load(open('data.json'), ensure_ascii=False)
except FileNotFoundError:
    data = {'epoch': 1574969089362, 'subs': DEF_SUBS}
    json.dump(data, open('data.json', 'w'), ensure_ascii=False)


# Authentication
creds = ServiceAccountCredentials.from_json_keyfile_dict(CREDS, SCOPE)
service = discovery.build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


# Functions
def sheet_get(ranges: List[str]) -> List[List[str]]:
    ranges = sheet.values().batchGet(
        spreadsheetId=ID, ranges=ranges).execute()['valueRanges']
    return [r['values'] for r in ranges]


def sheet_append(range: str, body: List[List[str]]) -> None:
    return sheet.values().append(
        spreadsheetId=ID, range=range, 
        body={'values': body}, 
        valueInputOption='USER_ENTERED').execute()


def sheet_update(range: str, body: List[List[str]]) -> None:
    return sheet.values().update(
        spreadsheetId=ID, range=range, 
        body={'values': body}, 
        valueInputOption='USER_ENTERED').execute()


def to_datetime(ms: Union[str, int]) -> str:
    if isinstance(ms, str):
        ms = int(ms)
    dt = datetime.utcfromtimestamp(ms/1000.0)
    return dt.strftime("%d/%m/%Y %H:%M:%S")


def card_extract(pl: dict) -> List[str]:
    code = pl['code']
    name = pl['name']

    album = pl['albumCode']
    collection = pl['collection']

    type_ = ''
    rarity = pl['type']
    if len(k := rarity.split()) > 1:
        type_, rarity = k

    e = str(pl['energy'])
    energy = e if e.isnumeric() else '0'
    p = str(pl['power'])
    power = p if p.isnumeric() else '0'
    ppe = '∞'
    if energy != '0': 
        ppe = str(eval(power + "//" + energy))

    title = ability = ''
    if pl['abilityTitle'] is not None: 
        title = pl['abilityTitle']
        ability = pl['abilityPlaintextV2']
        for p in data['subs']:
            ability = re.sub(p, data['subs'][p], ability)

    pull = to_datetime(pl['firstPull'])
    modified = to_datetime(pl['modifiedDate'])

    _img = pl['img'] 
    img = f'{IMG}/{_img[0:2]}/{_img[2:4]}/{_img[4:]}'

    return [code, name,
            album, collection,
            type_, rarity,
            energy, power, ppe,
            title, ability,
            pull, modified,
            img]


def cards_update(cards: List[dict], legacy: bool = True) -> None:
    Q_CARDS, Q_COLS, Q_DYKS = sheet_get([CARDS, COLS, DYKS]) 
    q_cards = Q_CARDS.copy()
    cols, dyks = Q_COLS.copy(), Q_DYKS.copy()
    logs, legacies, fusions = ([] for _ in range(3))

    for c in cards:
        epoch = int(c['modifiedDate']) 
        if epoch > data['epoch']:
            data['epoch'] = epoch

        card = card_extract(c)
        dyk = [c['name'], c['dyk']]
        for i in range(len(q_cards)): # Update card
            if card[0] == q_cards[i][0]:
                q_cards[i] = card
                try:
                    if dyk != dyks[i]:
                        dyks[i] = dyk
                except IndexError: 
                    dyks.append(dyk)
                if legacy:
                    legacies.append(['Updated'] + q_cards[i] + card)
                break
        else: # New card
            q_cards.append(card)
            dyks.append(dyk)
            # Fusion
            if card[3] == FUSE: 
                fusions.append([card[1]])
            # Collection TODO: bugfix
            if not any(card[3] == j[0] for j in cols):
                logging.info(f'New collection: {card[3]}')
                # _img = c['collectionImage']
                # img = f'{IMG}/{_img[0:2]}/{_img[2:4]}/{_img[4:]}'
                # cols.append([c['collectionCode'], card[3], card[11], img])
        logs.append([c['name'], c['modifiedDate']])

    if Q_CARDS != q_cards: 
        sheet_update(CARDS, q_cards) 
        logging.info(f'UPDATED {len(cards)} CARD(S)')
    if Q_COLS != cols: 
        sheet_update(COLS, cols) 
        logging.info(f'UPDATED {len(cols)} COLLECTION(S)')
    if Q_DYKS != dyks: 
        sheet_update(DYKS, dyks) 
        logging.info(f'UPDATED {len(dyks)} DYK(S)')
    if logs: 
        sheet_append('Changelog', logs)
        logging.info(f'ADDED {len(logs)} LOG(S)')
    if legacies: 
        sheet_append('Legacy Cards', legacies)
        logging.info(f'ADDED {len(legacies)} LEGACY(S)')
    if fusions: 
        sheet_append(FUSE, fusions)
        logging.info(f'ADDED {len(fusions)} FUSION(S)')
    
    json.dump(data, open('data.json'), ensure_ascii=False)


def update_all(legacy: bool = False) -> None:
    cards = cue.get_card_updates(1574969089362)
    cards_update(cards, legacy=legacy)


def update_epoch() -> None:
    cards = cue.get_card_updates(data['epoch'])
    cards_update(cards)


def update_schedule(*, interval: int = 60*60*24, thread: bool = False) -> None:
    def f():
        while True:
            update_epoch()
            time.sleep(interval)

    if thread: 
        Thread(target=f).start()
    else: 
        f()
