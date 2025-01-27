# Quick Start
Requirements: 
    - MQTT Integration for discovering entities and devices
    - MQTT Broker e.g. Mosquitto

# Configuration
Before using, state all the modbus devices in `config.yaml`. Multiple servers and clients can be added

## Server 
Each server should be defined as 
```
  - name: "Paneltrack 1"
    ha_display_name: "SG1"
    serialnum: "A2340700442"
    server_type: "PANELTRACK"
    connected_client: "Client1"
    modbus_id: 1
```
- `server_type` is used to select the class of server to instantiate. PANELTRACK with its register maps are pre-defined, but additional classes can be added. See adding custom server types
- `connected_client` specifies on which client bus (abstraction of serial port or tcp ip) the server is connected. Most systems use a single client.
- `modbus_id`: Modbus slave address of the server

## Client
Each client should be defined as
```
  - name: "ModbusTCP"
    ha_display_name: "Client1"
    type: "TCP"
    host: "10.0.0.15"
    port: 502
```

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
- `type` can be one of "RTU" or "TCP"
- `ha_display_name` is used to reference the correct connected client for each server - keep it unique
- `port` is the com port if `type` is "RTU", TCP port if `type` is "TCP"

# Developing Custom Server Types
requires implementing
      - device_info 
      - supprted_models
      - registers
      - manufacturer
override:
      - read_model
      - is_available
      - _decoded
      - _encoded

### Defining a new Server type
Inherit from server class in `server.py`. See abstracted_server.py.
add the new type to implemented_server.py and use this string when declaring the server_type in config.yaml
