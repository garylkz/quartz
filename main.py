if __name__ == '__main__':
    import logging
    import os
    from pathlib import Path

    logging.basicConfig(level=logging.INFO)
    os.environ['CREDS'] = Path('creds.json').read_text()


    from quartz import qct

    qct.mass_update()

