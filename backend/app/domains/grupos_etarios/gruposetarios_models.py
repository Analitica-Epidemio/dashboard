from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlmodel import SQLModel, Field
from typing import Any

class ConfiguracionRangos(SQLModel, table=True):
    __tablename__ = "configuracion_rangos"

    id: int = Field(default=None, primary_key=True)
    nombre: str
    rangos: Any = Field(sa_column=Column(JSON, nullable=False))

