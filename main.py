import os
from pathlib import Path

import nexity


if __name__ == '__main__':
    os.environ['CREDS'] = Path('creds').read_text()
    nexity.load_env()
    nexity.load_local('exts.card')
    nexity.run()

