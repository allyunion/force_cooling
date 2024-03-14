import configparser
import json
import logging
import os
import requests
import uuid

from datetime import datetime

import sensibo_client

# Configure the logger
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%d/%b/%Y:%H:%M:%S', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.ini')

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read(config_path)

# Govee settings
govee_api_key = config.get('Govee', 'api_key')
govee_mac_address = config.get('Govee', 'mac_address')
govee_sku_model_number = config.get('Govee', 'sku_model_number')

# Sensibo settings
sensibo_api_key = config.get('Sensibo', 'api_key')
sensibo_device_name = config.get('Sensibo', 'device_name')

# Threshold setting
temperature_threshold = float(config.get('Threshold', 'temperature_threshold'))

url = f'https://openapi.api.govee.com/router/api/v1/device/state'

headers = {
    'Govee-API-Key': govee_api_key,
    'Content-Type': 'application/json'
}

payload = {
    "requestId": str(uuid.uuid4()),
    "payload": {
        "device": govee_mac_address,
        "sku": govee_sku_model_number
    }
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
response_data = response.json()
temperature_raw = response_data['payload']['capabilities'][1]['state']['value']

temperature_celsius = temperature_raw / 100  # Convert to degrees Celsius
temperature_fahrenheit = (temperature_celsius * 9/5) + 32  # Convert to Fahrenheit

client = sensibo_client.SensiboClientAPI(sensibo_api_key)
devices = client.devices()

if sensibo_device_name not in devices:
    logger.error(f"Device '{sensibo_device_name}' not found.")
    exit(1)

sensibo_device_id = devices[sensibo_device_name]
ac_state = client.pod_ac_state(sensibo_device_id)

if temperature_fahrenheit > temperature_threshold and not ac_state['on']:
    # Turn on the Sensibo AC
    client.pod_change_ac_state(sensibo_device_id, ac_state, "on", True)
    logger.info("Sensibo AC turned on.")
else:
    logger.info(f"Temperature in Fahrenheit: {temperature_fahrenheit} °F")
    logger.info(f"Sensibo AC Status: {ac_state['on']}")
