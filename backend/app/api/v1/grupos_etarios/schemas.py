from pydantic import BaseModel
from typing import Optional, List

class RangoEdadSchema(BaseModel):
    desde: float
    hasta: Optional[float] = None
    unidad: str

class ConfiguracionRangosBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    rangos: List[RangoEdadSchema]

class ConfiguracionRangosCreate(ConfiguracionRangosBase):
    pass

class ConfiguracionRangosOut(ConfiguracionRangosBase):
    id: int

    class Config:
        orm_mode = True
