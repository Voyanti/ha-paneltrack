import abc
import logging
from typing import Optional
from enums import DataType
from client import Client
from options import ServerOptions
from parameter_types import ParamInfo, HAParamInfo

logger = logging.getLogger(__name__)


class Server(metaclass=abc.ABCMeta):
    """
        Base server class. Represents modbus server: its name, serial, model, modbus slave_id. e.g. SungrowInverter(Server).

        Includes functions to be abstracted by model/ manufacturer-specific implementations for 
        decoding, encoding data read/ write, reading model code, setting up model-specific registers and checking availability.
    """
    def __init__(self, name, serial, modbus_id, connected_client):
        self.name: str = name
        self.serial: str = serial
        self.modbus_id: int = modbus_id
        self.connected_client: Client = connected_client
        
        # Define in implementation
        self.supported_models: list = []
        self.manufacturer:str | None = None
        self.model:str | None = None
        self.device_info:dict | None = None
        self.parameters: Optional[dict[str, ParamInfo]] = None

        # Optional: if used for home assistant
        self.ha_parameters: Optional[dict[str, HAParamInfo]] = None

        logger.info(f"Server {self.name} set up.")

    def __str__(self):
        return f"{self.name}"
    
    def read_registers(self, parameter_name:str):
        """ Read a group of registers (parameter) using pymodbus 
        
            Requires implementation of the abstract method 'Server._decoded()'

            Parameters:
            -----------
                - parameter_name: str: slave parameter name string as defined in register map
        """
        param = self.parameters[parameter_name]

        address = param["addr"]
        dtype =  param["dtype"]
        multiplier = param["multiplier"]
        # count = param.get('count', dtype.size // 2) #TODO
        count = param["count"] #TODO
        unit = param["unit"]
        slave_id = self.modbus_id
        register_type = param['register_type']

        logger.info(f"Reading param {parameter_name} ({register_type}) of {dtype=} from {address=}, {multiplier=}, {count=}, {self.modbus_id=}") # TODO count

        result = self.connected_client._read(address, count, self.modbus_id, register_type)

        if result.isError(): 
            self.connected_client._handle_error_response(result)
            raise Exception(f"Error reading register {parameter_name}")

        logger.info(f"Raw register begin value: {result.registers[0]}")
        val = self._decoded(result.registers, dtype)
        if multiplier != 1: val*=multiplier
        if isinstance(val, int) or isinstance(val, float): val = round(val, 2)
        logger.info(f"Decoded Value = {val} {unit}")

        return val
    
    def write_registers(self, value:float, parameter_name: str):
        """ 
            Write to an individual register using pymodbus.

            Reuires implementation of the abstract methods 
            'Server._validate_write_val()' and 'Server._encode()'
        """
        logger.info(f"Validating write message")
        self._validate_write_val(parameter_name, value)

        param = self.parameters[parameter_name]
        address = param["addr"]
        dtype =  param["dtype"]
        multiplier = param["multiplier"]
        count = param["count"]
        unit = param["unit"]
        slave_id = self.modbus_id
        register_type = param['register_type']

        if multiplier != 1: value/=multiplier
        values = self._encoded(value)
        
        logger.info(f"Writing {value=} {unit=} to param {parameter_name} at {address=}, {dtype=}, {multiplier=}, {count=}, {register_type=}, {slave_id=}")
        
        self.connected_client.client.write_registers( address=address-1,
                                    value=values,
                                    slave=slave_id)


    @abc.abstractmethod
    def read_model(self) -> str:
        """
            Reads model name register and decodes it. Returns model name string. 

            Must be overridden.
        """
    
    def set_model(self):
        """
            Reads model-holding register, decodes it and sets self.model: str to its value..
            Specify decoding in Server.device_info = {modelcode:    {name:modelname, ...}  }
        """
        logger.info(f"Reading model for server {self.name}")
        self.model = self.read_model()
        logger.info(f"Model read as {self.model}")

        if self.model not in self.supported_models: raise NotImplementedError(f"Model not supported in implementation of Server, {self}")

    def is_available(self, register_name="Device type code"):
        """ Contacts any server register and returns true if the server is available """
        logger.info(f"Verifying availability of server {self.name}")

        available = True

        address = self.parameters[register_name]["addr"]
        dtype =  self.parameters[register_name]["dtype"]
        multiplier = self.parameters[register_name]["multiplier"]
        count = dtype.size // 2 # TODO
        unit = self.parameters[register_name]["unit"]
        slave_id = self.modbus_id
        register_type = self.parameters[register_name]['register_type']

        # count = self.parameters[register_name].dtype TODO
        response = self.connected_client._read(address, count, slave_id, register_type)

        if response.isError(): 
            self.connected_client._handle_error_response(response)
            available = False

        return available
    
    @classmethod
    @abc.abstractmethod
    def _decoded(cls, registers: list, dtype: DataType):
        """
        Server-specific decoding for registers read.

        Must be overridden.

        Parameters:
        -----------
        registers: list: list of ints as read from 16-bit ModBus Registers
        dtype: (DataType.U16, DataType.I16, DataType.U32, DataType.I32, ...)

        """

    @classmethod
    @abc.abstractmethod
    def _encoded(cls, content):
        "Server-specific encoding must be implemented."

    @abc.abstractmethod
    def setup_valid_registers_for_model(self):
        """ Server-specific logic for removing unsupported or selecting supported
            registers for the specific model must be implemented.
            Removes invalid registers for the specific model of inverter.
            Requires self.model. Call self.read_model() first."""

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
            idx = [str(client) for client in clients].index(opts.connected_client)  # TODO ugly
        except:
            raise ValueError(f"Client {opts.connected_client} from server {name} config not defined in client list")
        connected_client = clients[idx]

        return cls(name, serial, modbus_id, connected_client)
