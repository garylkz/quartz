if __name__ == '__main__':
    import logging
    import os
    from pathlib import Path

    from quartz import qct


    logging.basicConfig(level=logging.INFO)
    os.environ['CREDS'] = Path('creds.json').read_text()

    qct.mass_update()
