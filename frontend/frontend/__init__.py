from . import core
from . import api
from . import bulk
from . import server
__all__ = ['core', 'api', 'bulk', 'server']
import logging

log = logging.getLogger('frontend')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.INFO)

log.info("Initialized")
