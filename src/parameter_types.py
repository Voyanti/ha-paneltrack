from dataclasses import dataclass
from typing import Optional
from .enums import RegisterTypes, DataType


@dataclass
class ParamInfo:
    """
        Hardware information for a server parameter
    """
    name: str
    address: int
    dtype: DataType
    register_type: RegisterTypes
    unit: Optional[str]
    multiplier: Optional[int]


@dataclass
class HAParamInfo:
    """
        device_class and state_class for using hardware parameters as homeassistant entities
    """
    name: str
    device_class: str
    state_class: Optional[str]
