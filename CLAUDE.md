# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Home Assistant add-on that communicates with Paneltrack meters over Modbus TCP, publishing all available values to MQTT for Home Assistant integration. The add-on supports multiple Modbus TCP hubs, each connected to multiple Paneltrack meters.

## Common Development Commands

### Running Locally
```bash
./run_locally.sh
```
Starts the app with default configuration and creates a temporary local mosquitto broker. Uses spoofed client for testing without real hardware.

### Running Tests
```bash
./run_tests.sh
```
Runs all Python unit tests. Sets up PYTHONPATH and starts a local mosquitto broker on port 1884.

**Note**: Tests are incomplete. Current coverage includes loader and some app functionality. Missing tests for: rest of app, server, client, and modbus_mqtt modules.

To run a single test:
```bash
export PYTHONPATH=src/
mosquitto -p 1884 -d
python3 -m unittest tests.test_app.TestClassName.test_method_name -v
kill $(pgrep -f "mosquitto -p 1884")
```

### Docker Build
```bash
docker build -t ha-paneltrack .
```

## Architecture

### Core Components

**App Flow (src/app.py)**
1. **Setup Phase**: Load configuration, instantiate clients (Modbus connections) and servers (meter representations)
2. **Connect Phase**: Establish Modbus client connections, verify server availability, connect to MQTT broker, publish HA discovery topics
3. **Loop Phase**: Continuously read registers from all servers and publish values to MQTT

**Client-Server Pattern**
- **Client** (src/client.py): Represents Modbus TCP/RTU connection hubs. Wraps pymodbus client, handles connection retries, error decoding
- **Server** (src/server.py): Abstract base class representing individual Modbus devices (meters). Each implementation defines register maps and encoding/decoding logic
- **PanelTrack** (src/implemented_servers.py): Concrete server implementation for Paneltrack meters with F32/I32 register decoding

### Configuration Loading

**Loader** (src/loader.py): Parses config.yaml into typed AppOptions using cattrs. Validates server-client relationships and configuration schema.

### MQTT Integration

**MqttClient** (src/modbus_mqtt.py): Extends paho.mqtt.client
- Publishes HA discovery topics with device metadata and sensor configurations
- Publishes sensor state updates and availability
- Handles connection failures by killing the process (fail-fast pattern)
- Uses unique UUID-based client identifiers

**MQTT Topics**:
- Discovery: `{ha_discovery_topic}/sensor/{device_nickname}/{parameter}/config`
- State: `{mqtt_base_topic}/{device_nickname}/{parameter}/state`
- Availability: `{mqtt_base_topic}/{device_nickname}/availability`

### Key Design Patterns

**Dependency Injection**: Client/server instantiation uses callbacks, allowing test doubles (SpoofClient) to be injected for local development

**Server Abstraction**: Abstract Server class defines interface for new meter types:
- `read_model()`: Read device model identification
- `setup_valid_registers_for_model()`: Filter registers based on model
- `_decoded()/_encoded()`: Model-specific data encoding/decoding
- `parameters`: Dict of register definitions with address, dtype, multiplier, unit, device_class

**Connection Retry Logic**:
- Servers that fail initial connection are moved to `disconnected_servers` list
- App retries connection to disconnected servers each loop iteration
- Unavailable servers publish "offline" availability to MQTT

**Midnight Sleep Feature**: Optional sleep window (23:57-00:0X) to avoid meter resets, configurable via `midnight_sleep_enabled` and `midnight_sleep_wakeup_after`

## Adding New Server Types

1. Create new class extending Server in src/implemented_servers.py or new file
2. Define register_map with addr, count, dtype, multiplier, unit, device_class, register_type
3. Implement abstract methods: `supported_models`, `manufacturer`, `parameters`, `read_model()`, `setup_valid_registers_for_model()`, `_decoded()`, `_encoded()`
4. Add to ServerTypes enum in src/implemented_servers.py
5. Update config.yaml schema to include new server_type

## Configuration Structure

**config.yaml** defines:
- **servers**: List of meters with name, serialnum, server_type (PANELTRACK), connected_client, modbus_id
- **clients**: List of Modbus connections with name, type (TCP/RTU), host/port or serial parameters
- **MQTT settings**: host, port, credentials, topics, reconnect attempts
- **Timing**: pause_interval_seconds, midnight_sleep settings

## Testing Notes

- Tests are incomplete and provide limited coverage
- Completed tests: loader, some app functionality
- TODO: rest of app, server, client, modbus_mqtt
- SpoofClient class provides fake readings for testing without hardware
- Tests require mosquitto broker running on port 1884

## Dependencies

Python 3.10 with key packages:
- pymodbus 3.8.3: Modbus TCP/RTU communication
- paho-mqtt 2.1.0: MQTT client
- cattrs 24.1.2: Configuration deserialization
- PyYAML 6.0.2: Config file parsing
