import logging
from posm.speaker import Speaker

# create and configure main logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create console handler with a higher log level
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

# create formatter and add it to the handler
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# add the handler to the logger
logger.addHandler(handler)
