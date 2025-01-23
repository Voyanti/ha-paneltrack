from time import sleep
from datetime import datetime, timedelta
import atexit
import logging

from loader import load_options, Options
from client import Client
from implemented_servers import ServerTypes
from modbus_mqtt import MqttClient
from paho.mqtt.enums import MQTTErrorCode


logging.basicConfig(
    level=logging.INFO,  # Set logging level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format with timestamp
    datefmt="%Y-%m-%d %H:%M:%S"  # Date format
)
logger = logging.getLogger(__name__)

mqtt_client = None
pause_interval = 10
read_interval = 0.001

def exit_handler(servers, modbus_clients, mqtt_client):          
    logger.info("Exiting")
    # publish offline availability for each server
    for server in servers:
        mqtt_client.publish_availability(False, server)
    logger.info("Closing client connections on exit")
    for client in modbus_clients:
        client.close()

    mqtt_client.loop_stop()


def sleep_if_midnight():
    """
    Sleeps if the current time is within 3 minutes before or 5 minutes after midnight.
    Uses efficient sleep intervals instead of busy waiting.
    """
    while True:
        current_time = datetime.now()
        is_before_midnight = (current_time.hour == 23 and current_time.minute >= 57)
        is_after_midnight = (current_time.hour == 0 and current_time.minute < 5)
        
        if not (is_before_midnight or is_after_midnight):
            break
            
        # Calculate appropriate sleep duration
        if is_before_midnight:
            # Calculate time until midnight
            next_check = (current_time + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:
            # Calculate time until 5 minutes after midnight
            next_check = current_time.replace(
                hour=0, minute=5, second=0, microsecond=0
            )
            
        # Sleep until next check, but no longer than 30 seconds at a time
        sleep_duration = min(30, (next_check - current_time).total_seconds())
        sleep(sleep_duration)

atexit.register(exit_handler, mqtt_client)

try:
    # Read configuration
    OPTIONS: Options = load_options()

    logger.info("Instantiate clients")
    clients = [Client(cl_options) for cl_options in OPTIONS.clients]
    logger.info(f"{len(clients)} clients set up")
    
    logger.info("Instantiate servers")
    servers = [ServerTypes[sr.server_type].value(sr, clients) for sr in OPTIONS.servers]
    logger.info(f"{len(servers)} servers set up")
    # if len(servers) == 0: raise RuntimeError(f"No supported servers configured")

    sleep_if_midnight()

    # Connect to clients
    for client in clients:
        client.connect()


    # Connect to Servers
    for server in servers:
        if not server.is_available():
            logger.error(f"Server {server.nickname} not available")
            raise ConnectionError()                             
        server.read_model()
        server.setup_valid_registers_for_model()

    # Setup MQTT Client
    mqtt_client = MqttClient(OPTIONS)
    succeed: MQTTErrorCode = mqtt_client.connect(host=OPTIONS.mqtt_host, port=OPTIONS.mqtt_port)
    if succeed.value != 0: logger.info(f"MQTT Connection error: {succeed.name}, code {succeed.value}")
    
    sleep(read_interval)
    mqtt_client.loop_start()
    
    # Publish Discovery Topics
    for server in servers:
        mqtt_client.publish_discovery_topics(server)

    # every read_interval seconds, read the registers and publish to mqtt
    while True:
        for server in servers:
            for register_name, details in server.registers.items():
                client = server.connected_client
                value = client.read_registers(server, register_name, details)
                mqtt_client.publish_to_ha(register_name, value, server)
                sleep(read_interval)
            logger.info(f"Published all parameter values for {server.name=}")   

        # publish availability
        sleep(pause_interval)

        sleep_if_midnight()

finally:
    exit_handler(servers, clients, mqtt_client)
