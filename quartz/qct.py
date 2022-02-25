from datetime import datetime
import json
import logging
import os
import re
from typing import List, Union

from dumpster import fdict
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

from quartz import cue

# Constants
CREDS = json.loads(os.environ['CREDS'])
SCOPE = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets'
]
IMG = 'https://cdn-virttrade-assets-eucalyptus.cloud.virttrade.com/filekey'
ID = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo' 
CARDS = 'Card List!A:N'
COLS = 'Collection!A:D'
FUSE = 'Fusion'
LGCYS = 'Legacy Cards!A:AZ'


# Variables
fd = fdict(epoch=0)


# Authentication
creds = ServiceAccountCredentials.from_json_keyfile_dict(CREDS, SCOPE)
service = discovery.build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


# Functions
def get(range: str) -> List[List[str]]:
    return sheet.values().get(
        spreadsheetId=ID, range=range).execute().get('values', [])


def append(range: str, body: List[List[str]]) -> None:
    return sheet.values().append(
        spreadsheetId=ID, range=range, 
        body={'values': body}, 
        valueInputOption='USER_ENTERED').execute()


def update(range: str, body: List[List[str]]) -> None:
    return sheet.values().update(
        spreadsheetId=ID, range=range, 
        body={'values': body}, 
        valueInputOption='USER_ENTERED').execute()


def to_datetime(ms: Union[str, int]) -> str:
    if isinstance(ms, str):
        ms = int(ms)
    dt = datetime.utcfromtimestamp(ms/1000.0)
    return dt.strftime("%d/%m/%Y %H:%M:%S")


def extract_card(pl: dict) -> List[str]:
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
        ability = re.sub(':power:', '⚡', ability)
        ability = re.sub(':energy:', '🔋', ability)
        ability = re.sub(':lock:', '🔒 ', ability)
        ability = re.sub(':burn:', '🔥 ', ability)
        ability = re.sub(':return:', '↩️ ', ability)
        ability = re.sub(':play:', '▶️ ', ability)
        ability = re.sub(':draw:', '⬆️ ', ability)

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


def update_cards(cards: List[dict]) -> None:
    Q_CARDS = get(CARDS) 
    Q_COLS = get(COLS)
    q_cards = Q_CARDS.copy()
    new_legacies = []
    new_fusions = []
    new_collections = []

    for c in cards:
        epoch = int(c['modifiedDate'])
        if epoch > fd['epoch']:
            fd['epoch'] = epoch

        card = extract_card(c)
        logging.info(f'{card[0]}:{card[1]}')
        for i in range(len(q_cards)): # Update card
            if q_cards[i][0] == card[0]:
                # new_legacies.append(['Updated'] + q_cards[i] + card)
                q_cards[i] = card
                break
        else: # New card
            q_cards.append(card)
            # Fusion
            if card[3] == FUSE: 
                new_fusions.append([card[1]])
            # Collection
            if not any(card[3] == j[0] for j in Q_COLS): 
                _img = c['collectionImage']
                img = f'{IMG}/{_img[0:2]}/{_img[2:4]}/{_img[4:]}'
                col = [card[3], c['collectionCode'], card[11], img]
                new_collections.append(col)

    if Q_CARDS != q_cards: 
        update(CARDS, q_cards) 
    if new_legacies: 
        append(LGCYS, new_legacies)
    if new_fusions: 
        append(FUSE, new_fusions)
    if new_collections: 
        append(COLS, new_collections)
    
    fd.write()


def mass_update() -> None:
    update_cards(cue.get_card_updates(1574969089362))
