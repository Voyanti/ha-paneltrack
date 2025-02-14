# Voyanti Paneltrack

[Homeassistant](https://www.home-assistant.io/) (HA) Add-on for [Paneltrack Meters](https://www.submetering.co.za/products/metering-solutions/paneltrack/).

Communicates with Paneltrack meters over Modbus TCP, and publishes all available values to MQTT.

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https://github.com/Voyanti/ha-modbus-addons)

**Features**

- Customisable read interval at which all registers are updated
- Supports using multiple Modbus TCP hubs, each connected to multiple Paneltrack meters

**Requires**

- MQTT broker e.g. [Mosquitto](https://github.com/home-assistant/addons/blob/master/mosquitto/DOCS.md)
- [Homeassistant MQTT integration](https://www.home-assistant.io/integrations/mqtt/) to enable discovering the MQTT devices and entities

**Tested with**

- Python 3.10
- Homeassistant version x
- Supervisor version x

<!-- ![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]
![Supports armhf Architecture][armhf-shield]
![Supports armv7 Architecture][armv7-shield]
![Supports i386 Architecture][i386-shield] -->
