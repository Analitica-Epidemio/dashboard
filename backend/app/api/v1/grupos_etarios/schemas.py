
from pydantic import BaseModel


class RangoEdadSchema(BaseModel):
    desde: float
    hasta: float | None = None
    unidad: str

class ConfiguracionRangosBase(BaseModel):
    nombre: str
    descripcion: str | None = None
    rangos: list[RangoEdadSchema]

class ConfiguracionRangosCreate(ConfiguracionRangosBase):
    pass

class ConfiguracionRangosOut(ConfiguracionRangosBase):
    id: int

    class Config:
        orm_mode = True
