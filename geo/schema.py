from ninja import ModelSchema, Schema
from .models import Asignatura, MatriculaAutomatica


class AsignaturaSchema(ModelSchema):
    class Config:
        model = Asignatura
        model_fields = '__all__'


class MatriculaAutomaticaSchema(ModelSchema):
    """Fields we want to return when working with MatriculaAutomatica data."""

    class Config:
        model = MatriculaAutomatica
        model_fields = [
            'id',
            'courseid',
            'active',
            'fijo',
            'asignatura_id',
            'cod_grupo_asignatura',
            'plan',
            'centro',
        ]


class NotFoundSchema(Schema):
    """Single field returned when no model object is found for the ID provided as a path parameter."""

    message: str
