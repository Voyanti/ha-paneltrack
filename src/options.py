from dataclasses import dataclass
from typing import Union


@dataclass
class ServerOptions:
    """ Modbus Server Options as read from config json"""
    name: str
    serialnum: str
    server_type: str
    connected_client: str
    modbus_id: int


@dataclass
class ClientOptions:
    """ Modbus Client Options as read from config json"""
    name: str
    type: str


@dataclass
class ModbusTCPOptions(ClientOptions):
    host: str
    port: int


@dataclass
class ModbusRTUOptions(ClientOptions):
    port: str
    baudrate: int
    bytesize: int
    parity: bool
    stopbits: int


@dataclass
class AppOptions:
    """ Concatenated options for reading specific format of all options from config json """
    servers: list[ServerOptions]
    clients: list[Union[ModbusRTUOptions, ModbusTCPOptions]]

    pause_interval_seconds: int

    midnight_sleep_enabled: bool
    midnight_sleep_wakeup_after: int

    mqtt_host: str
    mqtt_port: int
    mqtt_user: str
    mqtt_password: str
    mwtt_ha_discovery_topic: str
    mqtt_base_topic: str
    mqtt_reconnect_attempts: int
