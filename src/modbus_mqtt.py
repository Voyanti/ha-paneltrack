import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import json
import logging
from .loader import Options

from random import getrandbits
from time import time, sleep
from queue import Queue

logger = logging.getLogger(__name__)
RECV_Q: Queue = Queue()


def slugify(text):
    return text.replace(' ', '_').replace('(', '').replace(')', '').replace('/', 'OR').replace('&', ' ').replace(':', '').replace('.', '').lower()


class MqttClient(mqtt.Client):
    """
        paho MQTT abstraction for home assistant
    """

    def __init__(self, options: Options):
        def generate_uuid():
            random_part = getrandbits(64)
            # Get current timestamp in milliseconds
            timestamp = int(time() * 1000)
            node = getrandbits(48)  # Simulating a network node (MAC address)

            uuid_str = f'{timestamp:08x}-{random_part >> 32:04x}-{random_part & 0xFFFF:04x}-{node >> 24:04x}-{node & 0xFFFFFF:06x}'
            return uuid_str

        uuid = generate_uuid()
        super().__init__(CallbackAPIVersion.VERSION2, f"modbus-{uuid}")
        self.username_pw_set(options.mqtt_user, options.mqtt_password)
        self.base_topic = options.mqtt_base_topic
        self.ha_discovery_topic = options.mwtt_ha_discovery_topic

        def on_connect(client, userdata, connect_flags, reason_code, properties):
            if reason_code == 0:
                logger.info(f"Connected to MQTT broker.")
            else:
                logger.info(
                    f"Not connected to MQTT broker.\nReturn code: {reason_code=}")

        def on_disconnect(client, userdata, message):
            logger.info("Disconnected from MQTT broker")

        def on_message(client, userdata, message):
            logger.info("Received message on MQTT")
            sleep(0.01)
            RECV_Q.put(message)                         # thread-safe

        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_message = on_message

    def publish_discovery_topics(self, server):
        while not self.is_connected():
            logger.info(
                f"Not connected to mqtt broker yet, sleep 100ms and retry. Before publishing discovery topics.")
            sleep(0.1)
        # TODO check if more separation from server is necessary/ possible
        nickname = server.name
        if not server.model or not server.manufacturer or not server.serial or not nickname or not server.parameters:
            logging.info(
                f"Server not properly configured. Cannot publish MQTT info")
            raise ValueError(
                f"Server not properly configured. Cannot publish MQTT info")

        logger.info(f"Publishing discovery topics for {nickname}")
        device = {
            "manufacturer": server.manufacturer(),
            "model": server.model(),
            "identifiers": [f"{nickname}"],
            "name": f"{nickname}"
            # "name": f"{server.manufacturer} {server.serialnum}"
        }

        # publish discovery topics for legal registers
        # assume registers in server.registers
        availability_topic = f"{self.base_topic}_{nickname}/availability"

        parameters = server.parameters()

        for register_name, details in parameters.items():
            state_topic = f"{self.base_topic}/{nickname}/{slugify(register_name)}/state"
            discovery_payload = {
                "name": register_name,
                "unique_id": f"{nickname}_{slugify(register_name)}",
                "state_topic": state_topic,
                "availability_topic": availability_topic,
                "device": device,
                "device_class": details["device_class"],
                "unit_of_measurement": details["unit"],
            }
            state_class = details.get("state_class", False)
            if state_class:
                discovery_payload['state_class'] = state_class
            discovery_topic = f"{self.ha_discovery_topic}/sensor/{nickname}/{slugify(register_name)}/config"

            self.publish(discovery_topic, json.dumps(
                discovery_payload), retain=True)

        self.publish_availability(True, server)

        # for register_name, details in server.write_parameters.items():
        #     discovery_payload = {
        #         "name": register_name,
        #         "unique_id": f"{nickname}_{slugify(register_name)}",
        #         "command_topic": f"{self.base_topic}/{nickname}/{slugify(register_name)}/set",
        #         "unit_of_measurement": details["unit"],
        #         "availability_topic": availability_topic,
        #         "device": device
        #     }

        #     discovery_topic = f"{self.ha_discovery_topic}/number/{nickname}/{slugify(register_name)}/config"
        #     self.publish(discovery_topic, json.dumps(discovery_payload), retain=True)

    def publish_to_ha(self, register_name, value, server):
        nickname = server.name
        state_topic = f"{self.base_topic}/{nickname}/{slugify(register_name)}/state"
        self.publish(state_topic, value)  # , retain=True)

    def publish_availability(self, avail, server):
        nickname = server.name
        availability_topic = f"{self.base_topic}_{nickname}/availability"
        self.publish(availability_topic,
                     "online" if avail else "offline", retain=True)
