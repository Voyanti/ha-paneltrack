from dataclasses import dataclass
import json
import os
import logging
import yaml
from cattrs import structure, unstructure, Converter
from options import *
from implemented_servers import ServerTypes

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

def validate_nicknames(opts: Options):
    """
    Verify unique names for clients and servers of options. Used as unique identifiers.
    """
    for cs in ('clients', 'servers'):
        names = [c.name for c in getattr(opts, cs)]
        if len(set(names)) != len(names): 
            raise ValueError(f"{cs[:-1]} names must be unique")
        
        if not all([c.isalnum() for c in names]):
            raise ValueError(f"Client names must be alphanumeric")
        
def validate_server_implemented(opts: Options):
    """ Validate that the specified server type is specified in implemented servers enum. """
    for server in opts.servers:
        if server.server_type not in [t.name for t in ServerTypes]:
            raise ValueError(f"Server type {server.server_type} not defined in implemented_servers.ServerTypes")

def load_options(json_rel_path="/data/options.json") -> tuple[dict, dict]:
    """ Load server, client configurations and connection specs as dicts from options json. """
    converter = Converter()

    logger.info("Attempting to read configuration json")
    if os.path.exists(json_rel_path):
        if json_rel_path[-4:] == 'json':
            with open(json_rel_path) as f:
                data = json.load(f)
        elif json_rel_path[-4:] == 'yaml':
            with open(json_rel_path) as file:
                data = yaml.load(file, Loader=yaml.FullLoader)['options']
    elif os.path.exists('config.yaml'):
        logging.info("Loading config.yaml")
        with open('config.yaml') as file:
            data = yaml.load(file, Loader=yaml.FullLoader)['options']
    else:
        logger.info("ConfigLoader error")
        logger.info(os.path.join(os.getcwd(), json_rel_path))
        raise FileNotFoundError(f"Config options json/yaml not found.")

    opts = converter.structure(data, Options)
    validate_nicknames(opts)
    validate_server_implemented(opts)
    logger.info("Successfully read configuration")

    return opts


if __name__ == "__main__":
    import pprint
    opts = load_options()
    pprint.pprint(opts)