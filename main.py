import os
from pathlib import Path
os.environ['CREDS'] = Path('.creds').read_text()


import blurpo


if __name__ == '__main__':
    blurpo.load_env()
    blurpo.load_local('ext.extension')
    blurpo.run()

