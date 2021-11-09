import logging

LOGGER = logging.getLogger()

def setup_logging(filename=None, level=logging.INFO):
    log_format = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    if filename:
        file_handler = logging.FileHandler(filename, 'a')
        file_handler.setFormatter(log_format)
        LOGGER.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    LOGGER.addHandler(console_handler)
    LOGGER.setLevel(level)

def test_logger():
    setup_logging("test-logfile.log")
    logger = logging.getLogger(__name__) #ensure module name
    LOGGER.info("This should print out")
    LOGGER.warning("This should print out")
    LOGGER.error("This should print out")
    LOGGER.debug("This should not be seen")


if __name__ == "__main__":
    test_logger()
