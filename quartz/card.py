from datetime import datetime
import json
import logging
import re
from typing import List, Union

from quartz import sheet


# Constants
IMG = 'https://cdn-virttrade-assets-eucalyptus.cloud.virttrade.com/filekey' 
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
    data = json.load(open('data.json', encoding='utf-8'))
except FileNotFoundError:
    data = {'epoch': 1574969089362, 'subs': DEF_SUBS}
    json.dump(data, open('data.json', 'w', encoding='utf-8'), ensure_ascii=False)


def to_datetime(ms: Union[str, int]) -> str:
    print()
    dt = datetime.utcfromtimestamp(ms/1000.0)
    return dt.strftime("%d/%m/%Y %H:%M:%S")


def extract(pl: dict) -> List[str]:
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

    try:
        pull = to_datetime(pl['firstPull'])
        modified = to_datetime(pl['modifiedDate'])
    except TypeError:
        raise Exception(f"{code}: date parsing error, firstPull: {pl['firstPull']}, modifiedDate: {pl['modifiedDate']}")

    _img = pl['img'] 
    img = f'{IMG}/{_img[0:2]}/{_img[2:4]}/{_img[4:]}'

    return [code, name,
            album, collection,
            type_, rarity,
            energy, power, ppe,
            title, ability,
            pull, modified,
            img]


def update(cards: List[dict], legacy: bool = True) -> None:
    Q_CARDS, Q_COLS, Q_DYKS = sheet.get([CARDS, COLS, DYKS]) 
    q_cards = Q_CARDS.copy()
    cols, dyks = Q_COLS.copy(), Q_DYKS.copy()
    logs, legacies, fusions = ([] for _ in range(3))

    for c in cards:
        epoch = int(c['modifiedDate']) 
        if epoch > data['epoch']:
            data['epoch'] = epoch

        card = extract(c)
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
        sheet.update(CARDS, q_cards) 
        logging.info(f'UPDATED {len(cards)} CARD(S)')
    if Q_COLS != cols: 
        sheet.update(COLS, cols) 
        logging.info(f'UPDATED {len(cols)} COLLECTION(S)')
    if Q_DYKS != dyks: 
        sheet.update(DYKS, dyks) 
        logging.info(f'UPDATED {len(dyks)} DYK(S)')
    if logs: 
        sheet.append('Changelog', logs)
        logging.info(f'ADDED {len(logs)} LOG(S)')
    if legacies: 
        sheet.append('Legacy Cards', legacies)
        logging.info(f'ADDED {len(legacies)} LEGACY(S)')
    if fusions: 
        sheet.append(FUSE, fusions)
        logging.info(f'ADDED {len(fusions)} FUSION(S)')
    
    json.dump(data, open('data.json', 'w', encoding='utf-8'), ensure_ascii=False)
