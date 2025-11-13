from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.models import BaseModel

class ConfiguracionRangos(BaseMode, table=True):
    __tablename__ = "configuracion_rangos"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False)

    # array con diccionario de grupos etarios
    rangos = Column(JSON, nullable=False)

