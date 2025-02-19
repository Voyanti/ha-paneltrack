from enum import Enum
from typing import Optional, Any, TypedDict


class RegisterTypes(Enum):
    INPUT_REGISTER = 3  # Read Only
    HOLDING_REGISTER = 4  # Read/ Write


class DataType(Enum):
    """
    Data types used by server registers. Used to choose decoding method. depending op server.
    """

    # Unsigned integers
    U16 = "U16"
    U32 = "U32"
    U64 = "U64"

    # Signed integers
    I16 = "I16"
    I32 = "I32"
    I64 = "I64"

    # Floats
    F32 = "F32"
    F64 = "F64"

    # String
    UTF8 = "UTF8"

    @property
    def size(self) -> Optional[int]:
        """
        Returns the size in bytes for fixed-size types.
        Returns None for variable-size types (UTF8).
        """
        sizes = {
            DataType.U16: 2,
            DataType.I16: 2,
            DataType.U32: 4,
            DataType.I32: 4,
            DataType.F32: 4,
            DataType.F32: 4,
            DataType.U64: 8,
            DataType.I64: 8,
            DataType.UTF8: None,
        }
        return sizes[self]

    @property
    def min_value(self) -> Optional[int]:
        """Returns the minimum value for numeric types."""
        ranges = {
            DataType.U16: 0,
            DataType.U32: 0,
            DataType.I16: -32768,  # -2^15
            DataType.I32: -2147483648,  # -2^31
            DataType.U64: 0,
            DataType.I64: -18446744073709551616,
            DataType.UTF8: None,
        }
        return ranges[self]

    @property
    def max_value(self) -> Optional[int]:
        """Returns the maximum value for numeric types."""
        ranges = {
            DataType.U16: 65535,  # 2^16 - 1
            DataType.U32: 4294967295,  # 2^32 - 1
            DataType.I16: 32767,  # 2^15 - 1
            DataType.I32: 2147483647,  # 2^31 - 1
            DataType.U64: 18446744073709551615,
            DataType.I64: 9223372036854775807,
            DataType.UTF8: None,
        }
        return ranges[self]


# https://www.home-assistant.io/integrations/sensor#device-class
class DeviceClass(Enum):
    DATE = "date"
    ENUM = "enum"
    TIMESTAMP = "timestamp"
    APPARENT_POWER = "apparent_power"
    AQI = "aqi"
    ATMOSPHERIC_PRESSURE = "atmospheric_pressure"
    BATTERY = "battery"
    CARBON_MONOXIDE = "carbon_monoxide"
    CARBON_DIOXIDE = "carbon_dioxide"
    CURRENT = "current"
    DATA_RATE = "data_rate"
    DATA_SIZE = "data_size"
    DISTANCE = "distance"
    DURATION = "duration"
    ENERGY = "energy"
    ENERGY_STORAGE = "energy_storage"
    FREQUENCY = "frequency"
    GAS = "gas"
    HUMIDITY = "humidity"
    ILLUMINANCE = "illuminance"
    IRRADIANCE = "irradiance"
    MOISTURE = "moisture"
    MONETARY = "monetary"
    NITROGEN_DIOXIDE = "nitrogen_dioxide"
    NITROGEN_MONOXIDE = "nitrogen_monoxide"
    NITROUS_OXIDE = "nitrous_oxide"
    OZONE = "ozone"
    PH = "ph"
    PM1 = "pm1"
    PM10 = "pm10"
    PM25 = "pm25"
    POWER_FACTOR = "power_factor"
    POWER = "power"
    PRECIPITATION = "precipitation"
    PRECIPITATION_INTENSITY = "precipitation_intensity"
    PRESSURE = "pressure"
    REACTIVE_POWER = "reactive_power"
    SIGNAL_STRENGTH = "signal_strength"
    SOUND_PRESSURE = "sound_pressure"
    SPEED = "speed"
    SULPHUR_DIOXIDE = "sulphur_dioxide"
    TEMPERATURE = "temperature"
    VOLATILE_ORGANIC_COMPOUNDS = "volatile_organic_compounds"
    VOLATILE_ORGANIC_COMPOUNDS_PARTS = "volatile_organic_compounds_parts"
    VOLTAGE = "voltage"
    VOLUME = "volume"
    VOLUME_STORAGE = "volume_storage"
    VOLUME_FLOW_RATE = "volume_flow_rate"
    WATER = "water"
    WEIGHT = "weight"
    WIND_SPEED = "wind_speed"


Parameter = TypedDict(
    "Parameter",
    {
        "addr": int,
        "count": int,
        "dtype": DataType,
        "multiplier": float,
        "unit": str,
        "device_class": DeviceClass,
        "register_type": RegisterTypes,
    },
)

if __name__ == "__main__":
    print(DataType.U16.min_value)
