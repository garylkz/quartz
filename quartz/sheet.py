import json
import os
from typing import List

from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials


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
ID = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo'


# Authentication
creds = ServiceAccountCredentials.from_json_keyfile_dict(CREDS, SCOPE)
service = discovery.build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


# Functions
def get(ranges: List[str]) -> List[List[str]]:
    ranges = sheet.values().batchGet(
        spreadsheetId=ID, ranges=ranges).execute()['valueRanges']
    return [r['values'] for r in ranges]


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
