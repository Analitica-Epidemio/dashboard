"""
⚕️ ATENCIÓN MÉDICA - SUPPORTING DOMAIN

Contexto médico, clínico y sanitario de los eventos epidemiológicos.

MÓDULOS:
├── diagnosticos_models.py      🔬 Diagnósticos médicos
├── salud_models.py            💊 Datos de salud (síntomas, muestras, vacunas, comorbilidades)
└── investigaciones_models.py   🔍 Investigaciones epidemiológicas

AGGREGATE ROOTS:
- Diagnostico: Diagnóstico médico asociado a evento
- Muestra: Muestra de laboratorio para análisis
- Sintoma: Síntoma reportado por paciente
- Vacuna: Registro de vacunación
- Investigacion: Investigación epidemiológica detallada

BOUNDED CONTEXT:
Todo lo relacionado con la atención médica, síntomas, diagnósticos,
muestras de laboratorio, vacunas y aspectos clínicos de los eventos
epidemiológicos.
"""
