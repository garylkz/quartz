if __name__ == '__main__':
    import logging

    from quartz import update


    logging.basicConfig(level=logging.INFO)

    update.schedule()
