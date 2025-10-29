from .enums import RegisterTypes
from .options import ModbusTCPOptions, ModbusRTUOptions
from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from pymodbus.pdu import ExceptionResponse
from pymodbus import ModbusException
import logging
from time import sleep
logger = logging.getLogger(__name__)


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
        self.client: ModbusSerialClient | ModbusTcpClient

        if isinstance(cl_options, ModbusTCPOptions):
            self.client = ModbusTcpClient(
                host=cl_options.host, port=cl_options.port)
        elif isinstance(cl_options, ModbusRTUOptions):
            self.client = ModbusSerialClient(port=cl_options.port, baudrate=cl_options.baudrate,
                                             bytesize=cl_options.bytesize, parity='Y' if cl_options.parity else 'N',
                                             stopbits=cl_options.stopbits)

    def read(self, address, count, slave_id, register_type):
        """
        Read modbus registers with proper error handling.

        Handles both ModbusException (connection/communication failures) and
        device-reported errors (checked via result.isError()).

        Returns:
            Response object with registers or error state

        Raises:
            ModbusException: Re-raised for connection/communication failures
        """
        try:
            if register_type == RegisterTypes.HOLDING_REGISTER:
                result = self.client.read_holding_registers(address=address-1,
                                                            count=count,
                                                            slave=slave_id)
            elif register_type == RegisterTypes.INPUT_REGISTER:
                result = self.client.read_input_registers(address=address-1,
                                                          count=count,
                                                          slave=slave_id)
            else:
                logger.info(f"unsupported register type {register_type}")
                raise ValueError(f"unsupported register type {register_type}")
            return result
        except ModbusException as exc:
            logger.error(f"ModbusException reading slave {slave_id} at address {address}: {exc}")
            raise

    def connect(self, num_retries=2, sleep_interval=3) -> None:
        logger.info(f"Connecting to client {self}")

        for i in range(num_retries):
            connected: bool = self.client.connect()
            if connected:
                break

            logging.info(f"Couldn't connect to {self}. Retrying")
            sleep(sleep_interval)

        if not connected:
            logger.error(
                f"Client Connection Issue after {num_retries} attempts.")
            raise ConnectionError(f"Client {self} Connection Issue")

        logger.info(f"Sucessfully connected to {self}")

    def close(self):
        logger.info(f"Closing connection to {self}")
        self.client.close()

    def __str__(self):
        """
            self.nickname is used as a unique id for finding the client to which each server is connected.
        """
        return f"{self.name}"

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

            error_message = exception_messages.get(
                exception_code, "Unknown Exception")
            logger.error(
                f"Modbus Exception Code {exception_code}: {error_message}")
        else:
            logger.error(
                f"Non Standard Modbus Exception. Cannot Decode Response")


class SpoofClient:
    """
        Spoofed Modbus client representation: name, nickname (ha_display_name), and pymodbus client.

        Wraps around pymodbus.client.ModbusSerialClient | pymodbus.client.ModbusTCPClient to
        fan out dictionary information, and decode/ encode register values when reading/ writing/
    """
    class SpoofResponse:
        def __init__(self, registers: list[int]):
            self.registers = registers

        def isError(self): return False

    def __init__(self, name: str):
        self.name = name

    def read(self, address, count, slave_id, register_type):
        logger.info(f"SPOOFING READ {slave_id=} {address=}")
        response = SpoofClient.SpoofResponse([73 for _ in range(count)])
        return response

    def connect(self, num_retries=2, sleep_interval=3):
        logger.info(f"SPOOFING CONNECT to {self}")

    def close(self):
        logger.info(f"SPOOFING DISCONNECT to {self}")

    def __str__(self):
        """
            self.nickname is used as a unique id for finding the client to which each server is connected.
        """
        return f"{self.name}"
