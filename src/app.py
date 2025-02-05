from time import sleep
from datetime import datetime, timedelta
import atexit
import logging
from queue import Queue

from loader import load_options
from options import Options
from client import Client
from implemented_servers import ServerTypes
from server import Server
from modbus_mqtt import MqttClient, RECV_Q
from paho.mqtt.enums import MQTTErrorCode
from paho.mqtt.client import MQTTMessage

import sys
SPOOF = False
if len(sys.argv) > 1:
    if sys.argv[1] == "SPOOF":
        from client import SpoofClient as Client
        SPOOF = True

logging.basicConfig(
    level=logging.INFO,  # Set logging level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format with timestamp
    datefmt="%Y-%m-%d %H:%M:%S"  # Date format
)
logger = logging.getLogger(__name__)

mqtt_client = None
pause_interval = 10
read_interval = 0.001

def exit_handler(servers: list[Server], modbus_clients: list[Client], mqtt_client: MqttClient):          
    logger.info("Exiting")
    # publish offline availability for each server
    for server in servers:
        mqtt_client.publish_availability(False, server)
    logger.info("Closing client connections on exit")
    for client in modbus_clients:
        client.close()

    mqtt_client.loop_stop()

# def message_handler(q: Queue[MQTTMessage], servers: list):
#     """
#         Writes appropriate server registers for each message in mqtt receive queue
#     """
#     logger.info(f"Checking for command messages.")
#     while not q.empty():
#         msg = q.get()
#         if msg is None: continue

#         # command_topic = f"{self.base_topic}/{server.nickname}/{slugify(register_name)}/set"
#         server_ha_display_name: str = msg.topic.split('/')[1]
#         s = None
#         for s in servers: 
#             if s.name == server_ha_display_name:
#                 server = s
#         if s is None: raise ValueError(f"Server {server_ha_display_name} not available. Cannot write.")
#         register_name: str = msg.topic.split('/')[2]
#         value: str = msg.payload.decode('utf-8')

#         server.write_registers(float(value), server = s, register_name = register_name, register_info=server.parameters[register_name])    


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


try:
    # Read configuration
    OPTIONS: Options = load_options()

    logger.info("Instantiate clients")
    clients = [Client(cl_options) for cl_options in OPTIONS.clients]
    logger.info(f"{len(clients)} clients set up")
    
    logger.info("Instantiate servers")
    servers = [ServerTypes[sr.server_type].value.from_ServerOptions(sr, clients) for sr in OPTIONS.servers]
    logger.info(f"{len(servers)} servers set up")
    # if len(servers) == 0: raise RuntimeError(f"No supported servers configured")

    atexit.register(exit_handler, servers, clients, mqtt_client)

    sleep_if_midnight()

    # Connect to clients
    for client in clients:
        client.connect()

    # Connect to Servers
    for server in servers:
        if SPOOF: server.model = "spoof"
        else: 
            if not server.is_available():
                logger.error(f"Server {server.name} not available")
                raise ConnectionError()                             
            server.set_model()
            server.setup_valid_registers_for_model()

    # Setup MQTT Client
    mqtt_client = MqttClient(OPTIONS)
    succeed: MQTTErrorCode = mqtt_client.connect(host=OPTIONS.mqtt_host, port=OPTIONS.mqtt_port)
    if succeed.value != 0: logger.info(f"MQTT Connection error: {succeed.name}, code {succeed.value}")
    
    sleep(read_interval)
    mqtt_client.loop_start()
    
    # Publish Discovery Topics
    for server in servers:
        # mqtt_client.subscribe_write_topics(server)
        mqtt_client.publish_discovery_topics(server)

    # every read_interval seconds, read the registers and publish to mqtt
    while True:
        for server in servers:
            for register_name, details in server.parameters.items():
                sleep(read_interval)
                value = server.read_registers(register_name)
                mqtt_client.publish_to_ha(register_name, value, server)
            logger.info(f"Published all parameter values for {server.name=}")   

            # if not RECV_Q.empty(): message_handler(RECV_Q, servers)

        # publish availability
        sleep(pause_interval)

        sleep_if_midnight()

finally:
    exit_handler(servers, clients, mqtt_client)
