# Quick Start

Install required add-ons:

- MQTT broker e.g. [Mosquitto](https://github.com/home-assistant/addons/blob/master/mosquitto/DOCS.md)
- [Homeassistant MQTT integration](https://www.home-assistant.io/integrations/mqtt/) to enable discovering the MQTT devices and entities
- Configure
  - Clients(Modbus Hubs/USB to Serial Converters) and Servers(Devices/RTUs) See Configuration section for details.
  - MQTT host, port, username and password

# Configuration

## Server

Each server should be defined as

```
  - name: "Paneltrack 1"
    serialnum: "A2340700442"
    server_type: "PANELTRACK"
    connected_client: "Client1"
    modbus_id: 1
```

- `name` is used to create the HA entity unique_id, and device name. Use alphanumeric characters only. Keep it unique.
- `serialnum` not functional for Paneltrack meters. For bookkeeping purposes.
- `server_type` is used to select the class of server to instantiate. This add-on supports only PANELTRACK.
- `connected_client` specifies on which client bus (abstraction of serial port or tcp ip) the server is connected. Most systems use a single client.
- `modbus_id`: Modbus slave address of the device/server.

## Client

Each client should be defined as

```
  - name: "ModbusTCP"
    type: "TCP"
    host: "10.0.0.15"
    port: 502
```

or

```
  - name: "ModbusTCP"
    ha_display_name: "Client2"
    type: "RTU"
    port: "/dev/tty1"
    baudrate: 9600
    bytesize: 8
    parity: false
    stopbits: 1
```

- `name` see Server config above
- `type` can be one of "RTU" or "TCP"
- `port` is the com port if `type` is "RTU", TCP port if `type` is "TCP"

# Development

## Running locally

`devcontainer.json` can be used in vs code (Rebuild and reopen in container), followed by the task start Home assistant from `tasks.json` as outlined [here](https://developers.home-assistant.io/docs/add-ons/testing/).

`run_locally.sh` starts the app with default configuration, and creates a temporary local mosquitto broker

`run_tests.sh` runs all python unit test after setting the appropriate environment variables

Both make use of a spoofClient class which returns fake readings.

## Tests

- Completed tests
  - loader
  - some app functionality
- TODO tests
  - rest of app functionality
  - server
  - client
  - modbus_mqtt

### Defining a new Server type (for new add-on)

Abstract class Server in `server.py` can be implemented. See abstractmethod docstrings for information.

Add the new type to the enum in `implemented_servers.py` and use this string when declaring the `server_type` in config.yaml
