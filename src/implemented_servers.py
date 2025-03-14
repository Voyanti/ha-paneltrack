from typing import final
from .enums import DeviceClass, RegisterTypes, DataType
from .server import Server
from pymodbus.client import ModbusSerialClient
import struct
import logging
from enum import Enum

logger = logging.getLogger(__name__)


@final
class PanelTrack(Server):
    ################################################################################################################################################
    register_map = {
        'Vab': {'addr': 1, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'V', 'device_class': DeviceClass.VOLTAGE, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Vbc': {'addr': 3, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'V', 'device_class': DeviceClass.VOLTAGE, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Vca': {'addr': 5, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'V', 'device_class': DeviceClass.VOLTAGE, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Va': {'addr': 7, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'V', 'device_class': DeviceClass.VOLTAGE, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Vb': {'addr': 9, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'V', 'device_class': DeviceClass.VOLTAGE, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Vc': {'addr': 11, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'V', 'device_class': DeviceClass.VOLTAGE, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Ia': {'addr': 13, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'A', 'device_class': DeviceClass.CURRENT, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Ib': {'addr': 15, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'A', 'device_class': DeviceClass.CURRENT, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Ic': {'addr': 17, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'A', 'device_class': DeviceClass.CURRENT, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Pa': {'addr': 19, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'W', 'device_class': DeviceClass.POWER, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Pb': {'addr': 21, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'W', 'device_class': DeviceClass.POWER, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Pc': {'addr': 23, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'W', 'device_class': DeviceClass.POWER, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Qa': {'addr': 25, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'var', 'device_class': DeviceClass.REACTIVE_POWER, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Qb': {'addr': 27, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'var', 'device_class': DeviceClass.REACTIVE_POWER, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Qc': {'addr': 29, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'var', 'device_class': DeviceClass.REACTIVE_POWER, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Sa': {'addr': 31, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'VA', 'device_class': DeviceClass.APPARENT_POWER, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Sb': {'addr': 33, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'VA', 'device_class': DeviceClass.APPARENT_POWER, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Sc': {'addr': 35, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'VA', 'device_class': DeviceClass.APPARENT_POWER, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Pfa': {'addr': 37, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': '', 'device_class': DeviceClass.POWER_FACTOR, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Pfb': {'addr': 39, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': '', 'device_class': DeviceClass.POWER_FACTOR, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Pfc': {'addr': 41, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': '', 'device_class': DeviceClass.POWER_FACTOR, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'PSum': {'addr': 43, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'W', 'device_class': DeviceClass.POWER, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'QSum': {'addr': 45, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'var', 'device_class': DeviceClass.REACTIVE_POWER, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'SSum': {'addr': 47, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'VA', 'device_class': DeviceClass.APPARENT_POWER, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'pfSum': {'addr': 49, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': '', 'device_class': DeviceClass.POWER_FACTOR, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Freq': {'addr': 51, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'Hz', 'device_class': DeviceClass.FREQUENCY, 'register_type': RegisterTypes.HOLDING_REGISTER},
        'MonthkWhTotal': {'addr': 53, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'kWh', 'device_class': DeviceClass.ENERGY, 'register_type': RegisterTypes.HOLDING_REGISTER, 'state_class': 'total_increasing'},
        'DaykWhTotal': {'addr': 55, 'count': 2, 'dtype': DataType.F32, 'multiplier': 1, 'unit': 'kWh', 'device_class': DeviceClass.ENERGY, 'register_type': RegisterTypes.HOLDING_REGISTER, 'state_class': 'total_increasing'},
        'TotalImportEnergy': {'addr': 57, 'count': 2, 'dtype': DataType.I32, 'multiplier': 1, 'unit': 'kWh', 'device_class': DeviceClass.ENERGY, 'state_class': 'total_increasing', 'register_type': RegisterTypes.HOLDING_REGISTER, 'state_class': 'total'},
        'TotalExportEnergy': {'addr': 59, 'count': 2, 'dtype': DataType.I32, 'multiplier': 1, 'unit': 'kWh', 'device_class': DeviceClass.ENERGY, 'state_class': 'total_increasing', 'register_type': RegisterTypes.HOLDING_REGISTER, 'state_class': 'total'},
    }
    # Source https://gith ub.com/heinrich321/voyanti-paneltrack/blob/main/paneltrack.py
    ################################################################################################################################################

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parameters = PanelTrack.register_map
        self.write_parameters = {}
        self._model = "paneltrack"

    @property
    def parameters(self):
        return self._parameters

    @property
    def manufacturer(self):
        return "Paneltrack"

    @property
    def supported_models(self):
        return ('paneltrack',)

    def read_model(self, device_type_code_param_key="Device Type Code"):
        return self.model

    def setup_valid_registers_for_model(self):
        """ Removes invalid registers for the specific model of inverter.
            Requires self.model. Call self.read_model() first."""
        return

    def is_available(self):
        return super().is_available(register_name="TotalImportEnergy")

    def _decode_f32(registers):
        raw = struct.pack('>HH', registers[0], registers[1])
        return struct.unpack('>f', raw)[0]

    def _decode_i32(registers):
        raw = struct.pack('>HH', registers[0], registers[1])
        return struct.unpack('>I', raw)[0]

    @classmethod
    def _decoded(cls, registers, dtype):
        if dtype == DataType.F32:
            return cls._decode_f32(registers)
        elif dtype == DataType.I32:
            return cls._decode_i32(registers)
        else:
            raise NotImplementedError(
                f"Data type {dtype} decoding not implemented")

    @classmethod
    def _encoded(cls, value):
        """ Convert a float or integer to big-endian register.
            Supports U16 only.
        """
        pass

    def _validate_write_val(self, register_name: str, val):
        """ Model-specific writes might be necessary to support more models """
        pass

# Declare all defined server abstractions here. Add to schema in config.yaml to enable selecting.


class ServerTypes(Enum):
    PANELTRACK = PanelTrack


if __name__ == "__main__":
    serv = PanelTrack(name="", serial="", modbus_id=1, connected_client=None)
    serv.set_model()
