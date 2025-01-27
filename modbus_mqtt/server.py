import abc
import logging
from enums import DataType
from dataclasses import dataclass
# from loader import ServerOptions

logger = logging.getLogger(__name__)


class Server(metaclass=abc.ABCMeta):
    def __init__(self, sr_options, clients):
        self.name = sr_options.name
        self.nickname = sr_options.ha_display_name
        self.serialnum = sr_options.serialnum
        self.device_addr:int| None = sr_options.modbus_id           # modbus slave_id

        try:
            idx = [str(client) for client in clients].index(sr_options.connected_client)  # TODO ugly
        except:
            raise ValueError(f"Client {sr_options.connected_client} from server {self.nickname} config not defined in client list")
        self.connected_client = clients[idx]

        
        self.model:str | None = None                                # model name
        self.model_info: dict | None = None                         # additional model-specific info e.g. 'mppt': 3

        logger.info(f"Server {self.nickname} set up.")

    def __str__(self):
        return f"{self.nickname}"
    
    def read_model(self, device_type_code_param_key="Device type code"):
        logger.info(f"Reading model for server")
        modelcode = self.connected_client.read_registers(self, device_type_code_param_key, self.registers[device_type_code_param_key])
        self.model = self.device_info[modelcode]['model']
        self.model_info = self.device_info[modelcode]
        logger.info(f"Model read as {self.model}")

        if self.model not in self.supported_models: raise NotImplementedError(f"Model not supported in implementation of Server, {self}")

    def is_available(self, register_name="Device type code"):
        """ Contacts any server register and returns true if the server is available """
        logger.info(f"Verifying availability of server {self.nickname}")

        available = True

        address = self.registers[register_name]["addr"]
        count = self.registers[register_name]["count"]
        slave_id = self.device_addr
        register_type = self.registers[register_name]['register_type']
        response = self.connected_client._read(address, count, slave_id, register_type)

        if response.isError(): 
            self.sonnected_client._handle_error_response(response)
            available = False

        return available
    
    @classmethod
    @abc.abstractmethod
    def _decoded(cls, registers: list, dtype: DataType):
        """
        Server-specific decoding must be implemented.

        Parameters:
        -----------
        registers: list: list of ints as read from 16-bit ModBus Registers
        dtype: (DataType.U16, DataType.I16, DataType.U32, DataType.I32 

        """
        pass

    @classmethod
    @abc.abstractmethod
    def _encoded(cls, content):
        "Server-specific encoding must be implemented."
        pass

    @abc.abstractmethod
    def setup_valid_registers_for_model(self):
        """ Server-specific logic for removing unsupported or selecting supported
            registers for the specific model must be implemented.
            Removes invalid registers for the specific model of inverter.
            Requires self.model. Call self.read_model() first."""
        pass
