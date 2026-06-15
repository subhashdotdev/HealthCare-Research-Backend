import logging
import json
import uuid
import time
from pythonjsonlogger import jsonlogger   



LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(user_id)s %(project)s %(query)s"



def get_logger(name: str = __name__) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:                     
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(user_id)s %(project)s %(query)s %(duration)s",
        rename_fields={"levelname": "severity", "asctime": "timestamp"},
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger