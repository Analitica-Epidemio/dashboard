from app.core.models import BaseModel
from sqlalchemy import Column
from "../eventos_epidemiologicos/clasificacion/models" import TipoClasificacion


class Consulta(BaseModel, table=true):
	__tablename__ = "consulta"
    
    
    user_id: int = Field(foreign_key="user.id", index=True)
    fecha_desde: int = Field
    
    user: "User" = Relationship(back_populates="consultas")


