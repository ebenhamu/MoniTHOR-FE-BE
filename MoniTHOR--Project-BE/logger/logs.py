import logging
import sys
import json


with open('./config.json', 'r') as config_file:
    config = json.load(config_file)

log_level = config['LOG_LEVEL']
log_file =  config['LOG_FILE'] 
log_format= config['LOG_FORMAT'] 
def set_log_level(level):
    if level == 'DEBUG':
        logging.basicConfig(level=logging.INFO,format=log_format,handlers=[logging.FileHandler(log_file),logging.StreamHandler(sys.stdout)]
        )
    elif level == 'INFO':
        logging.basicConfig(level=logging.INFO,format=log_format,handlers=[logging.FileHandler(log_file),logging.StreamHandler(sys.stdout)]
        )
    else:        
        logging.basicConfig(level=logging.INFO,format=log_format,handlers=[logging.FileHandler(log_file),logging.StreamHandler(sys.stdout)]
        )

set_log_level(log_level)

logger = logging.getLogger(__name__)
logger.setLevel(log_level)
