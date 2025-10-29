from abc import abstractmethod, ABC
import logging
from typing import Optional, TypedDict

from pymodbus import ModbusException
from .enums import DataType, RegisterTypes, Parameter, DeviceClass
from .client import Client
from .options import ServerOptions
from .parameter_types import ParamInfo, HAParamInfo

logger = logging.getLogger(__name__)

class ReadException(Exception):
    pass


class Server(ABC):
    """
        Base server class. Represents modbus server: its name, serial, model, modbus slave_id. e.g. SungrowInverter(Server).

        Includes functions to be abstracted by model/ manufacturer-specific implementations for
        decoding, encoding data read/ write, reading model code, setting up model-specific registers and checking availability.
    """

    def __init__(self, name, serial, modbus_id, connected_client) -> None:
        self.name: str = name
        self.serial: str = serial
        self.modbus_id: int = modbus_id
        self.connected_client: Client = connected_client

        self._model: str = "unknown"

        logger.info(f"Server {self.name} set up.")

    def __str__(self):
        return f"{self.name}"

    @property
    @abstractmethod
    def supported_models(self) -> tuple[str, ...]:
        """ Return a tuple of string names of all supported models for the implementation."""

    @property
    @abstractmethod
    def manufacturer(self) -> str:
        """ Return a string manufacturer name for the implementation."""

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Parameter]:
        """ Return a string model name for the implementation."""

    @abstractmethod
    def read_model(self) -> str:
        """
            Reads model name register if available and decodes it.

            :returns: model_name
        """

    @abstractmethod
    def setup_valid_registers_for_model(self):
        """ Server-specific logic for removing unsupported or selecting supported
            registers for the specific model must be implemented.
            Removes invalid registers for the specific model of inverter.
            Requires self.model. Call self.read_model() first."""

    @classmethod
    @abstractmethod
    def _decoded(cls, registers: list, dtype: DataType):
        """
        Server-specific decoding for registers read.

        Parameters:
        -----------
        registers: list: list of ints as read from 16-bit ModBus Registers
        dtype: (DataType.U16, DataType.I16, DataType.U32, DataType.I32, ...)
        """

    @classmethod
    @abstractmethod
    def _encoded(cls, content):
        "Server-specific encoding of content"

    @property
    def model(self) -> str:
        """ Return a string model name for the implementation.
            Ahould be read in using server.read_model(). 
            server.set_model is called in server.connect(), which sets the model.
            
            model is used in seupt_valid_registers_for_model
            Provided to fascilitate server types where the model cannot be read."""
        return self._model
    
    @model.setter
    def model(self, value):
        self._model = value

    def set_model(self):
        """
            Reads model-holding register, decodes it and sets self.model: str to its value..
            Specify decoding in Server.device_info = {modelcode:    {name:modelname, ...}  }
        """
        logger.info(f"Reading model for server {self.name}")
        self.model = self.read_model()
        logger.info(f"Model read as {self.model}")

        if self.model not in self.supported_models:
            raise NotImplementedError(
                f"Model not supported in implementation of Server, {self}")

    def is_available(self, register_name="Device type code"):
        """ Contacts any server register and returns true if the server is available """
        logger.info(f"Verifying availability of server {self.name}")

        available = True

        address = self.parameters[register_name]["addr"]
        dtype = self.parameters[register_name]["dtype"]
        count = self.parameters[register_name]['count']
        register_type = self.parameters[register_name]['register_type']
        slave_id = self.modbus_id
        
        # if device is completely offline e.g. power out
        try: 
            response = self.connected_client.read(
                address, count, slave_id, register_type)
        except ModbusException as e:
            logger.error(f"{e.with_traceback}")
            return False

        # other errors
        if response.isError():
            self.connected_client._handle_error_response(response)
            available = False

        return available

    def read_registers(self, parameter_name: str):
        """Read a group of registers (parameter) using pymodbus

            Requires implementation of the abstract method 'Server._decoded()'

        Args:
            parameter_name (str): slave parameter name string as defined in register map

        Raises:
            ReadException: _description_

        Returns:
            _type_: _description_
        """
        device_class_to_rounding: dict[DeviceClass, int] = {    # TODO define in deviceClass type
            DeviceClass.REACTIVE_POWER: 0,
            DeviceClass.ENERGY: 1,
            DeviceClass.FREQUENCY: 1,
            DeviceClass.POWER_FACTOR: 1,
            DeviceClass.APPARENT_POWER: 0, 
            DeviceClass.CURRENT: 1,
            DeviceClass.VOLTAGE: 0,
            DeviceClass.POWER: 0
        }
        param = self.parameters[parameter_name]  # type: ignore

        address = param["addr"]
        dtype = param["dtype"]
        multiplier = param["multiplier"]
        # count = param.get('count', dtype.size // 2) #TODO
        count = param["count"]  # TODO
        unit = param["unit"]
        device_class = param['device_class']
        slave_id = self.modbus_id
        register_type = param['register_type']

        # TODO count
        logger.debug(
            f"Reading param {parameter_name} ({register_type}) of {dtype=} from {address=}, {multiplier=}, {count=}, {self.modbus_id=}")

        result = self.connected_client.read(
            address, count, self.modbus_id, register_type)

        if result.isError(): # config error, not connection
            self.connected_client._handle_error_response(result)
            raise ReadException(f"Error reading register {parameter_name}") 

        logger.debug(f"Raw register begin value: {result.registers[0]}")
        val = self._decoded(result.registers, dtype)
        if multiplier != 1:
            val *= multiplier
        if isinstance(val, int) or isinstance(val, float):
            val = round(
                val, device_class_to_rounding.get(device_class, 2))
        logger.debug(f"Read {parameter_name} = {val} {unit}")

        return val

    # def write_registers(self, value: float, parameter_name: str):
    #     """
    #         Write to an individual register using pymodbus.

    #         Reuires implementation of the abstract methods
    #         'Server._validate_write_val()' and 'Server._encode()'
    #     """
    #     logger.info(f"Validating write message")
    #     self._validate_write_val(parameter_name, value)

    #     param = self.parameters[parameter_name]
    #     address = param["addr"]
    #     dtype = param["dtype"]
    #     multiplier = param["multiplier"]
    #     count = param["count"]
    #     unit = param["unit"]
    #     slave_id = self.modbus_id
    #     register_type = param['register_type']

    #     if multiplier != 1:
    #         value /= multiplier
    #     values = self._encoded(value)

    #     logger.info(
    #         f"Writing {value=} {unit=} to param {parameter_name} at {address=}, {dtype=}, {multiplier=}, {count=}, {register_type=}, {slave_id=}")

    #     self.connected_client.client.write_registers(address=address-1,
    #                                                  value=values,
    #                                                  slave=slave_id)

    def connect(self) -> bool:
        if not self.is_available():
            logger.error(f"Server {self.name} not available")
            return False
        
        self.set_model()
        self.setup_valid_registers_for_model()
        return True

    @classmethod
    def from_ServerOptions(
        cls,
        opts: ServerOptions,
        clients: list[Client]
    ):
        """
            Initialises modbus_mqtt.server.Server from modbus_mqtt.loader.ServerOptions object

            Parameters:
            -----------
                - sr_options: modbus_mqtt.loader.ServerOptions - options as read from config json
                - clients: list[modbus_mqtt.client.Client] - list of all TCP/Serial clients connected to machine
        """
        name = opts.name
        serial = opts.serialnum
        modbus_id: int = opts.modbus_id           # modbus slave_id

        try:
            idx = [str(client) for client in clients].index(
                opts.connected_client)  # TODO ugly
        except:
            raise ValueError(
                f"Client {opts.connected_client} from server {name} config not defined in client list")
        connected_client = clients[idx]

        return cls(name, serial, modbus_id, connected_client)

