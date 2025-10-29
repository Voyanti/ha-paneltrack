from time import sleep
from datetime import datetime, timedelta
import atexit
import logging
from queue import Queue
from typing import Callable

from pymodbus import ModbusException

from .loader import load_validate_options
from .options import AppOptions
from .client import Client
from .implemented_servers import ServerTypes
from .server import Server
from .modbus_mqtt import MqttClient, RECV_Q
from paho.mqtt.enums import MQTTErrorCode
from paho.mqtt.client import MQTTMessage

import sys

logging.basicConfig(
    level=logging.INFO,  # Set logging level
    # Format with timestamp
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",  # Date format
)
logger = logging.getLogger(__name__)

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


class App:
    def __init__(self, client_instantiator_callback, server_instantiator_callback, options_rel_path=None) -> None:
        self.OPTIONS: AppOptions
        # Read configuration
        if options_rel_path:
            self.OPTIONS = load_validate_options(options_rel_path)
        else:
            self.OPTIONS = load_validate_options()

        self.midnight_sleep_enabled, self.minutes_wakeup_after = self.OPTIONS.midnight_sleep_enabled, self.OPTIONS.midnight_sleep_wakeup_after
        self.pause_interval = self.OPTIONS.pause_interval_seconds
        # midnight_sleep_enabled=True, minutes_wakeup_after=5

        self.disconnect_stack = []

        # Setup callbacks
        self.client_instantiator_callback = client_instantiator_callback
        self.server_instantiator_callback: Callable[[AppOptions, list[Client]], list[Server]] = server_instantiator_callback

    def setup(self) -> None:
        self.sleep_if_midnight()

        logger.info("Instantiate clients")
        self.clients = self.client_instantiator_callback(self.OPTIONS)
        logger.info(f"{len(self.clients)} clients set up")

        logger.info("Instantiate servers")
        self.servers = self.server_instantiator_callback(
            self.OPTIONS, self.clients)
        logger.info(f"{len(self.servers)} servers set up")
        # if len(servers) == 0: raise RuntimeError(f"No supported servers configured")

    def connect(self) -> None:
        for client in self.clients:
            client.connect()

        # Unavailable servers are noted for reconnect attempts later. Does not cause a crash
        connected_servers = []
        disconnected_servers= []
        for server in self.servers:
            success: bool = server.connect()
            if success:
                connected_servers.append(server) 
            else:
                logger.error(f"Error Connecting to server {server.name}. Disable reading untill next loop")
                disconnected_servers.append(server)
        self.servers: list[Server]= connected_servers
        self.disconnected_servers: list[Server] = disconnected_servers


        # Setup MQTT Client
        self.mqtt_client = MqttClient(self.OPTIONS)
        succeed: MQTTErrorCode = self.mqtt_client.connect(
            host=self.OPTIONS.mqtt_host, port=self.OPTIONS.mqtt_port
        )
        if succeed.value != 0:
            logger.info(
                f"MQTT Connection error: {succeed.name}, code {succeed.value}")
            
        for server in disconnected_servers:
            self.mqtt_client.publish_availability(False, server)

        atexit.register(exit_handler, self.servers + self.disconnected_servers,
                        self.clients, self.mqtt_client)

        sleep(READ_INTERVAL)
        self.mqtt_client.loop_start()
        sleep(READ_INTERVAL)

        self.mqtt_client.ensure_connected(self.OPTIONS.mqtt_reconnect_attempts)

        # Publish Discovery Topics
        for server in self.servers:
            self.mqtt_client.publish_discovery_topics(server)

    def loop(self, loop_count: int | None = None) -> None:
        # if not self.servers or not self.clients:
        #     logger.info(f"In loop but no app servers or clients setup up or available")
        #     raise ValueError(
        #         f"In loop but no app servers or clients setup up or available")

        # every read_interval seconds, read the registers and publish to mqtt
        i = 0
        while True:
            self.mqtt_client.ensure_connected(self.OPTIONS.mqtt_reconnect_attempts)

            for server in self.servers:
                sleep(READ_INTERVAL)
                try: 
                    for register_name, details in server.parameters.items():
                        value = server.read_registers(register_name)
                        self.mqtt_client.publish_to_ha(
                            register_name, value, server)
                    logger.info(
                        f"Published all parameter values for {server.name=}")
                except ModbusException as e:
                    logger.error(f"Error reading register from {server.name=}: {e} ")
                    self.disconnect_stack.append(server)
                    continue

            for disconn_server in self.disconnect_stack:
                self.servers.remove(disconn_server)
                self.disconnected_servers.append(disconn_server)
            self.disconnect_stack = []

            # TODO: publish availability
            sleep(self.pause_interval)

            # try reconnecting to disconnected servers
            for server in reversed(self.disconnected_servers):
                logger.info("Retrying connection to %s" % server.name)
                success: bool = server.connect()
                if success:
                    logger.info("Succesfully reconnected to %s" % server.name)
                    self.servers.append(server) 
                    self.disconnected_servers.pop()
                else:
                    logger.error(f"Error Connecting to server %s. Disable reading untill next loop" % server.name)

            self.sleep_if_midnight()

            i += 1
            if loop_count is not None and i >= loop_count:
                break

    def sleep_if_midnight(self) -> None:
        """
        Sleeps if the current time is within 3 minutes before or 5 minutes after midnight.
        Uses efficient sleep intervals instead of busy waiting.
        """
        while self.midnight_sleep_enabled:
            current_time = datetime.now()
            is_before_midnight = current_time.hour == 23 and current_time.minute >= 57
            is_after_midnight = current_time.hour == 0 and current_time.minute < self.minutes_wakeup_after

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
                    hour=0, minute=self.minutes_wakeup_after, second=0, microsecond=0)

            # Sleep until next check, but no longer than 30 seconds at a time
            sleep_duration = min(
                30, (next_check - current_time).total_seconds())
            sleep(sleep_duration)


def instantiate_clients(OPTIONS: AppOptions) -> list[Client]:
    return [Client(cl_options) for cl_options in OPTIONS.clients]


def instantiate_servers(OPTIONS: AppOptions, clients: list[Client]) -> list[Server]:
    return [
        ServerTypes[sr.server_type].value.from_ServerOptions(sr, clients)
        for sr in OPTIONS.servers
    ]


if __name__ == "__main__":
    if len(sys.argv) <= 1:  # deployed on homeassistant
        app = App(instantiate_clients, instantiate_servers)
        app.setup()
        app.connect()
        app.loop()
    else:                   # running locally
        from .client import SpoofClient
        app = App(instantiate_clients, instantiate_servers, sys.argv[1])
        app.OPTIONS.mqtt_host = "localhost"
        app.OPTIONS.mqtt_port = 1884

        def instantiate_spoof_clients(OPTS: AppOptions) -> list[SpoofClient]:
            return [SpoofClient(client_opts.name) for client_opts in OPTS.clients]

        app = App(
            client_instantiator_callback=instantiate_spoof_clients,
            server_instantiator_callback=instantiate_servers,
            options_rel_path="config.yaml"
        )

        app.setup()
        for s in app.servers:
            s.connect = lambda: True
        app.connect()
        app.loop(2)

    # finally:
    #     exit_handler(servers, clients, mqtt_client) TODO NB
