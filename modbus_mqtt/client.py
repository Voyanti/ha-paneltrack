from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from pymodbus.pdu import ExceptionResponse
from enums import RegisterTypes, DataType
import logging
from loader import ModbusTCPOptions, ModbusRTUOptions
from time import sleep
logger = logging.getLogger(__name__)

from server import Server


class Client:
    """
        Modbus client representation: name, nickname (ha_display_name), and pymodbus client. 

        Wraps around pymodbus.client.ModbusSerialClient | pymodbus.client.ModbusTCPClient to 
        fan out dictionary information, and decode/ encode register values when reading/ writing/
    """
    def __init__(self, cl_options: ModbusTCPOptions | ModbusRTUOptions):
        """
            Initialised from modbus_mqtt.loader.ClientOptions object

            Parameters:
            -----------
                - cl_options: modbus_mqtt.loader.ClientOptions - options as read from config json

            TODO move to classmethod, to separate home-assistant dependency out
        """
        self.name = cl_options.name
        self.nickname = cl_options.ha_display_name
        self.client: ModbusSerialClient | ModbusTcpClient

        if isinstance(cl_options, ModbusTCPOptions):
            self.client = ModbusTcpClient(host=cl_options.host, port=cl_options.port)
        elif isinstance(cl_options, ModbusRTUOptions):
            self.client = ModbusSerialClient(port=cl_options.port, baudrate=cl_options.baudrate, 
                                                bytesize=cl_options.bytesize, parity='Y' if cl_options.parity else 'N', 
                                                stopbits=cl_options.stopbits)

    def _read(self, address, count, slave_id, register_type):
        if register_type == RegisterTypes.HOLDING_REGISTER:
            result = self.client.read_holding_registers(address=    address-1,
                                                        count=      count,
                                                        slave=      slave_id)
        elif register_type == RegisterTypes.INPUT_REGISTER:
            result = self.client.read_input_registers(address=      address-1,
                                                        count=      count,
                                                        slave=      slave_id)
        else: 
            logger.info(f"unsupported register type {register_type}") # will maybe never happen?
            raise ValueError(f"unsupported register type {register_type}")
        return result

    def read_registers(self, server:Server, register_name:str, register_info:dict):
        """ Read a group of registers (parameter) using pymodbus 
        
            Requires implementation of the abstract method 'Server._decoded()'

            Parameters:
            -----------
                - server: modbus_mqtt.server.Server: used to find client and modbus slave address to read from
                - register_name: str: slave parameter name
                - register_info: dict: slave parameter info dict(addr=, dtyoe=, multiplier=. count=. unit=, slave_id=, register_type=)

        """

        address = register_info["addr"]
        dtype =  register_info["dtype"]
        multiplier = register_info["multiplier"]
        count = register_info["count"]
        unit = register_info["unit"]
        slave_id = server.device_addr
        register_type = register_info['register_type']

        logger.info(f"Reading param {register_name} ({register_type}) of {dtype=} from {address=}, {multiplier=}, {count=}, {slave_id=}")

        result = self._read(address, count, slave_id, register_type)

        if result.isError(): 
            self._handle_error_response(result)
            raise Exception(f"Error reading register {register_name}")

        logger.info(f"Raw register begin value: {result.registers[0]}")
        val = server._decoded(result.registers, dtype)
        if multiplier != 1: val*=multiplier
        if isinstance(val, int) or isinstance(val, float): val = round(val, 2)
        logger.info(f"Decoded Value = {val} {unit}")

        return val

    def write_registers(self, value:float, server:Server, register_name: str, register_info:dict):
        """ 
            Write to an individual register using pymodbus.

            Reuires implementation of the abstract methods 
            'Server._validate_write_val()' and 'Server._encode()'
        """
        logger.info(f"Validating write message")
        server._validate_write_val(register_name, value)

        address = register_info["addr"]
        dtype =  register_info["dtype"]
        multiplier = register_info["multiplier"]
        count = register_info["count"]
        unit = register_info["unit"]
        slave_id = server.device_addr
        register_type = register_info['register_type']

        if multiplier != 1: value/=multiplier
        values = server._encoded(value)
        
        logger.info(f"Writing {value=} {unit=} to param {register_name} at {address=}, {dtype=}, {multiplier=}, {count=}, {register_type=}, {slave_id=}")
        
        self.client.write_registers( address=address-1,
                                    value=values,
                                    slave=slave_id)

    def connect(self, num_retries=2, sleep_interval=3):
        logger.info(f"Connecting to client {self}")

        for i in range(num_retries):
            connected: bool = self.client.connect()
            if connected: break

            logging.info(f"Couldn't connect to {self}. Retrying")
            sleep(sleep_interval)

        if not connected: 
            logger.error(f"Client Connection Issue after {num_retries} attempts.")
            raise ConnectionError(f"Client {self} Connection Issue")

        logger.info(f"Sucessfully connected to {self}")

    def close(self):
        logger.info(f"Closing connection to {self}")
        self.client.close()

    def __str__(self):
        """
            self.nickname is used as a unique id for finding the client to which each server is connected.
        """
        return f"{self.nickname}"

    def _handle_error_response(self, result):
        if isinstance(result, ExceptionResponse):
            exception_code = result.exception_code

            # Modbus exception codes and their meanings
            exception_messages = {
                1: "Illegal Function",
                2: "Illegal Data Address",
                3: "Illegal Data Value",
                4: "Slave Device Failure",
                5: "Acknowledge",
                6: "Slave Device Busy",
                7: "Negative Acknowledge",
                8: "Memory Parity Error",
                10: "Gateway Path Unavailable",
                11: "Gateway Target Device Failed to Respond"
            }

            error_message = exception_messages.get(exception_code, "Unknown Exception")
            logger.error(f"Modbus Exception Code {exception_code}: {error_message}")
        else: logger.error(f"Non Standard Modbus Exception. Cannot Decode Response")
