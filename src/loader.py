from dataclasses import dataclass
import json
import os
import logging
import yaml
from cattrs import structure, unstructure, Converter
from .options import *
from .implemented_servers import ServerTypes

logger = logging.getLogger(__name__)

"""
    Validation:
    schema already validates most types and required fields
    x at least one server, client, mqtt configuration is required

    requires validation:
    x unique ha_display_name
    - connected client exists done in server constructer at the moment
    x case connection type TCP: specs(name, host, port)
    x case connection type RTU: specs(name, baudrate: int, bytesize: int, parity: bool, stopbits: int
"""


def validate_names(names: list) -> None:
    """
    Verify unique alphanumeric names for clients and servers of options. Used as unique identifiers.
    """
    if len(set(names)) != len(names):
        raise ValueError(f"Device/ Client names must be unique")

    if not all([c.isalnum() for c in names]):
        raise ValueError(f"Client names must be alphanumeric")


def validate_server_implemented(servers: list):
    """Validate that the specified server type is specified in implemented servers enum."""
    for server in servers:
        if server.server_type not in [t.name for t in ServerTypes]:
            raise ValueError(
                f"Server type {server.server_type} not defined in implemented_servers.ServerTypes"
            )


def validate_options(opts: Options) -> None:
    client_names = [c.name for c in opts.clients]
    server_names = [s.name for s in opts.servers]
    validate_names(client_names)
    validate_names(server_names)
    validate_server_implemented(opts.servers)


def read_json(json_rel_path):
    with open(json_rel_path) as f:
        data = json.load(f)
    return data


def read_yaml(json_rel_path):
    with open(json_rel_path) as file:
        data = yaml.load(file, Loader=yaml.FullLoader)["options"]
    return data


def load_options(json_rel_path="/data/options.json") -> Options:
    """Load server, client configurations and connection specs as dicts from options json."""
    converter = Converter()

    logger.info(
        f"Attempting to read configuration json at path {os.path.join(os.getcwd(), json_rel_path)}"
    )

    # Homeassistant add-ons parse the user confi.yaml into a json.
    # Support yaml parsing for testing purposes.
    if os.path.exists(json_rel_path):
        if json_rel_path[-4:] == "json":
            data = read_json(json_rel_path)
        elif json_rel_path[-4:] == "yaml":
            data = read_yaml(json_rel_path)
    else:
        logger.info("ConfigLoader error")
        logger.info(os.path.join(os.getcwd(), json_rel_path))
        raise FileNotFoundError(
            f"Config options json/yaml not found at {os.path.join(os.getcwd(), json_rel_path)}")

    opts = converter.structure(data, Options)
    return opts


def load_validate_options(json_rel_path="/data/options.json") -> Options:
    """Load and Validate Options"""
    opts = load_options(json_rel_path)

    validate_options(opts)

    logger.info("Successfully read configuration")
    return opts


if __name__ == "__main__":
    import pprint

    opts = load_validate_options('config.yaml')
    pprint.pprint(opts)
