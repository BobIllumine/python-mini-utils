import re
import warnings
from typing import overload
from enum import Enum


class UnitType:
    def __init__(self, name: str, match: str):
        self.name = name
        self.match = match
        if '{EXP_TEMP}' not in self.match:
            warnings.warn(f"Unit type {self.name} has no '{EXP_TEMP}' in match, it will be added before the match automatically") # noqa
            self.match = "{EXP_TEMP}" + self.match


class UnitExp:
    def __init__(self, name: str, exp: float):
        self.name = name
        self.exp = exp
    
class UnitStore:
    unit_list = []
    exp_list = []
    
    @classmethod
    def register_type(cls, type: UnitType):
        cls.unit_list.append(type)

    @classmethod
    def register_exp(cls, exp: UnitExp):
        cls.exp_list.append(exp)

class Unit:
    @overload
    def __init__(self, entity: str):
        ...
    @overload
    def __init__(self, value: float, unit: UnitType, exp: UnitExp):
        ...

    def __init__(
        self,
        entity: str | None = None,
        value: float | None = None,
        unit: UnitType | None = None,
        exp: UnitExp | None = None,
    ):
        if entity is not None:
            self.entity = entity
            value, unit, exp = self._parse_entity()
            self.value = value
            self.unit = unit
            self.exp = exp
        elif value is not None and unit is not None and exp is not None:
            self.value = value
            self.unit = unit
            self.exp = exp
        else:
            raise ValueError("Invalid unit initialization")

    def _parse_entity(self, entity: str) -> tuple[float, UnitType, UnitExp]:
        match = re.match(r"(\d+([.,']\d+)?)(?:*.*?)([a-zA-Z]+)", entity)
        if match:
            value, unit, exp = match.groups()   
            return float(value), UnitType(unit), UnitExp(exp)
        else:
            raise ValueError("Invalid unit entity")

