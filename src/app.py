from time import sleep
from datetime import datetime, timedelta
import atexit
import logging
from queue import Queue

from .loader import load_validate_options
from .options import Options
from .client import Client
from .implemented_servers import ServerTypes
from .server import Server
from .modbus_mqtt import MqttClient, RECV_Q
from paho.mqtt.enums import MQTTErrorCode
from paho.mqtt.client import MQTTMessage

import sys

SPOOF = False
if len(sys.argv) > 1:
    if sys.argv[1] == "SPOOF":
        from .client import SpoofClient as Client

        SPOOF = True

logging.basicConfig(
    level=logging.INFO,  # Set logging level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format with timestamp
    datefmt="%Y-%m-%d %H:%M:%S",  # Date format
)
logger = logging.getLogger(__name__)

mqtt_client = None
READ_INTERVAL = 0.001


def exit_handler(
    servers: list[Server], modbus_clients: list[Client], mqtt_client: MqttClient
) -> None:
    logger.info("Exiting")
    # publish offline availability for each server
    for server in servers:
        mqtt_client.publish_availability(False, server)
    logger.info("Closing client connections on exit")
    for client in modbus_clients:
        client.close()

    mqtt_client.loop_stop()


def sleep_if_midnight(midnight_sleep_enabled=True, minutes_wakeup_after=5) -> None:
    """
    Sleeps if the current time is within 3 minutes before or 5 minutes after midnight.
    Uses efficient sleep intervals instead of busy waiting.
    """
    while midnight_sleep_enabled:
        current_time = datetime.now()
        is_before_midnight = current_time.hour == 23 and current_time.minute >= 57
        is_after_midnight = current_time.hour == 0 and current_time.minute < minutes_wakeup_after

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
            next_check = current_time.replace(hour=0, minute=minutes_wakeup_after, second=0, microsecond=0)

        # Sleep until next check, but no longer than 30 seconds at a time
        sleep_duration = min(30, (next_check - current_time).total_seconds())
        sleep(sleep_duration)


def loop(servers: list[Server], mqtt_client: MqttClient, midnight_sleep_enabled, minutes_wakeup_after, pause_interval) -> None:
    while True:
        for server in servers:
            for register_name, details in server.parameters.items():
                sleep(READ_INTERVAL)
                value = server.read_registers(register_name)
                mqtt_client.publish_to_ha(register_name, value, server)
            logger.info(f"Published all parameter values for {server.name=}")

        # publish availability
        sleep(pause_interval)

        sleep_if_midnight(midnight_sleep_enabled, minutes_wakeup_after)


def main() -> None:
    try:
        # Read configuration
        OPTIONS: Options = load_validate_options()
        midnight_sleep_enabled, minutes_wakeup_after = OPTIONS.sleep_over_midnight, OPTIONS.sleep_midnight_minutes
        pause_interval = OPTIONS.pause_interval_seconds
    
        logger.info("Instantiate clients")
        clients = [Client(cl_options) for cl_options in OPTIONS.clients]
        logger.info(f"{len(clients)} clients set up")

        logger.info("Instantiate servers")
        servers = [
            ServerTypes[sr.server_type].value.from_ServerOptions(sr, clients)
            for sr in OPTIONS.servers
        ]
        logger.info(f"{len(servers)} servers set up")
        # if len(servers) == 0: raise RuntimeError(f"No supported servers configured")

        sleep_if_midnight(OPTIONS.sleep_over_midnight, OPTIONS.sleep_midnight_minutes)

        # Connect to clients
        for client in clients:
            client.connect()

        # Connect to Servers
        for server in servers:
            if SPOOF:
                server.model = "spoof"
            else:
                if not server.is_available():
                    logger.error(f"Server {server.name} not available")
                    raise ConnectionError()
                server.set_model()
                server.setup_valid_registers_for_model()

        # Setup MQTT Client
        mqtt_client = MqttClient(OPTIONS)
        succeed: MQTTErrorCode = mqtt_client.connect(
            host=OPTIONS.mqtt_host, port=OPTIONS.mqtt_port
        )
        if succeed.value != 0:
            logger.info(f"MQTT Connection error: {succeed.name}, code {succeed.value}")

        atexit.register(exit_handler, servers, clients, mqtt_client)

        sleep(READ_INTERVAL)
        mqtt_client.loop_start()

        # Publish Discovery Topics
        for server in servers:
            mqtt_client.publish_discovery_topics(server)

        # every read_interval seconds, read the registers and publish to mqtt
        loop(servers, mqtt_client, midnight_sleep_enabled, minutes_wakeup_after, pause_interval)

    finally:
        exit_handler(servers, clients, mqtt_client)


if __name__ == "__main__":
    main()
