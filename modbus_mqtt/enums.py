import enum
from typing import Optional, Any


class RegisterTypes(enum.Enum):
    INPUT_REGISTER = 3          # Read Only
    HOLDING_REGISTER = 4        # Read/ Write


# class ClientTypes(enum.Enum):
#     RTU


class DataType(enum.Enum):
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
            DataType.UTF8: None
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
            DataType.UTF8: None
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
            DataType.UTF8: None
        }
        return ranges[self]

    def encode(self, value: Any) -> bytes:
        """
        Encode a Python value to bytes according to the data type.
        
        Args:
            value: The value to encode
            
        Returns:
            bytes: The encoded value
            
        Raises:
            ValueError: If the value is out of range for the type
        """
        # TODO: Implement encoding logic
        raise NotImplementedError

    def decode(self, data: bytes) -> Any:
        """
        Decode bytes to a Python value according to the data type.
        
        Args:
            data: The bytes to decode
            
        Returns:
            The decoded value
            
        Raises:
            ValueError: If the data cannot be decoded
        """
        # TODO: Implement decoding logic
        raise NotImplementedError


if __name__ == "__main__":
    print(DataType.U16.min_value)