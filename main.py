import logging
import os
from pathlib import Path

import nexity


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    os.environ['CREDS'] = Path('creds').read_text()
    nexity.load_env()
    nexity.load_local('quartz.card')
    nexity.run()

