# 🚀 Demo Técnica INVEST - Evaluación Inteligente de Historias de Usuario

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.48-red.svg)](https://streamlit.io)
[![LM Studio](https://img.shields.io/badge/LM%20Studio-API-green.svg)](https://lmstudio.ai)

## 🎯 Descripción

Demo técnica escalable y modular en Python para evaluación automática de historias de usuario utilizando los criterios **INVEST** (Independent, Negotiable, Valuable, Estimable, Small, Testable). 

### 🔧 Modos de Análisis

- **`reglas`**: Evaluación rápida basada en reglas predefinidas y patrones regex
- **`gptoss`**: Evaluación avanzada usando modelo GPT-OSS-20B vía LM Studio API

El modo se configura mediante la variable de entorno `INVEST_MODE`.

## 🏗️ Arquitectura del Proyecto

```
Proyecto/
│── app.py                      # Aplicación Streamlit principal
│── requirements.txt            # Dependencias del proyecto
│── .env.example               # Ejemplo de configuración
│── README.md                  # Documentación principal
│
├── data/
│   ├── backlog.csv            # Dataset de historias de usuario
│   └── historicos.csv         # Dataset histórico para regresión
│
├── modules/                   # Módulos principales
│   ├── __init__.py
│   ├── invest_agent.py        # Agente principal de evaluación INVEST
│   ├── invest_criteria.py     # Evaluadores de criterios individuales
│   ├── invest_result.py       # Estructuras de datos para resultados
│   ├── regression_model.py    # Modelo de regresión predictiva
│   ├── integration.py         # Orquestación e integración
│   ├── utils.py              # Utilidades y helpers
│   └── config.py             # Configuración del sistema
│
├── clients/                   # Clientes para servicios externos
│   ├── __init__.py
│   └── lm_studio_client.py   # Cliente para LM Studio API
│
├── tests/                     # Tests unitarios
│   ├── __init__.py
│   ├── run_tests.py          # Ejecutor de tests
│   ├── test_invest_agent.py  # Tests del agente principal
│   ├── test_invest_criteria.py # Tests de criterios INVEST
│   └── test_lm_studio_client.py # Tests del cliente LM Studio
│
└── .streamlit/               # Configuración de Streamlit
    └── config.toml
```

## 🚀 Instalación y Configuración

### 1. Prerrequisitos
- Python 3.8+
- pip
- LM Studio (para modo gptoss)

### 2. Instalación
```bash
# Clonar/descargar el proyecto
cd "Proyecto dia del ingeniero - reto 3"

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configuración de Variables de Entorno

Crear archivo `.env` basado en `.env.example`:

```env
# Modo de análisis: "reglas" o "gptoss"
INVEST_MODE=gptoss

# Configuración LM Studio (solo para modo gptoss)
LM_STUDIO_URL=http://127.0.0.1:1234
LM_STUDIO_MODEL=openai/gpt-oss-20b
```

### 4. Configuración de LM Studio (para modo gptoss)

1. Instalar y abrir LM Studio
2. Descargar el modelo `openai/gpt-oss-20b`
3. Cargar el modelo en el servidor local
4. Iniciar el servidor en `http://127.0.0.1:1234`

## 🎮 Uso del Sistema

### Aplicación Web (Streamlit)
```bash
# Ejecutar la aplicación web
streamlit run app.py
```

### Uso Programático
```python
from modules.invest_agent import InvestAgent
import os

# Configurar modo
os.environ['INVEST_MODE'] = 'gptoss'  # o 'reglas'

# Crear agente
agent = InvestAgent()

# Evaluar historia
resultado = agent.evaluate_story(
    "Como usuario quiero iniciar sesión para acceder al sistema",
    story_id="USER_001"
)

# Ver resultados
print(f"ID: {resultado.id}")
print(f"Modo: {resultado.modo_evaluacion}")
print(f"INVEST: {resultado.invest_scores}")
print(f"Sugerencias: {resultado.sugerencias}")
```

### Evaluación en Lote
```python
# Evaluar múltiples historias
historias = [
    "Como usuario quiero registrarme para crear una cuenta",
    "Como admin quiero gestionar usuarios para mantener el sistema"
]

resultados = agent.evaluate_stories_batch(historias)
resumen = agent.get_evaluation_summary()

print(f"Total evaluadas: {resumen['total_evaluadas']}")
print(f"Promedio INVEST: {resumen['porcentaje_invest_completo']:.1f}%")
```

## 🧪 Testing

El proyecto incluye un conjunto completo de tests unitarios:

```bash
# Ejecutar todos los tests
python tests/run_tests.py

# Ejecutar tests específicos
python -m unittest tests.test_invest_agent
python -m unittest tests.test_invest_criteria
python -m unittest tests.test_lm_studio_client
```

### Cobertura de Tests
- ✅ **InvestAgent**: Inicialización, evaluación, manejo de errores
- ✅ **InvestCriteria**: Todos los criterios INVEST individuales
- ✅ **LMStudioClient**: Conexión, generación de texto, manejo de errores
- ✅ **Integración**: Flujos completos de evaluación

## 📊 Criterios INVEST Implementados

| Criterio | Descripción | Validaciones |
|----------|-------------|--------------|
| **Independent** | Historia independiente de otras | Detecta dependencias explícitas |
| **Negotiable** | Flexible y negociable | Identifica especificaciones rígidas |
| **Valuable** | Aporta valor al usuario/negocio | Verifica justificación de valor |
| **Estimable** | Claridad para estimación | Evalúa concretude y ambigüedad |
| **Small** | Tamaño apropiado para sprint | Analiza complejidad y alcance |
| **Testable** | Criterios de aceptación claros | Detecta elementos subjetivos |

## 🔍 Funcionalidades Avanzadas

### Modo Reglas
- ✅ Evaluación basada en patrones regex
- ✅ Análisis sintáctico de historias
- ✅ Detección de palabras clave
- ✅ Validaciones de formato
- ✅ Sugerencias específicas por criterio

### Modo GPT-OSS
- ✅ Integración con LM Studio API
- ✅ Análisis semántico avanzado
- ✅ Comprensión de contexto
- ✅ Respuestas estructuradas en JSON
- ✅ Fallback automático a modo reglas

### Capacidades del Sistema
- 🔄 **Auto-switching**: Cambio automático entre modos según disponibilidad
- 📈 **Escalabilidad**: Evaluación en lote optimizada
- 🛡️ **Robustez**: Manejo de errores y timeouts
- 📊 **Analytics**: Métricas y resúmenes de evaluación
- 🧪 **Testing**: Cobertura completa de tests unitarios

## 🚦 Estados del Sistema

### Modo Reglas Activo
```
INFO:invest_agent:🔧 Modo de reglas activado
```

### Modo GPT-OSS Activo
```
INFO:invest_agent:✅ LM Studio conectado exitosamente
INFO:invest_agent:🎯 Modelo openai/gpt-oss-20b disponible
```

### Fallback Automático
```
WARNING:invest_agent:⚠️ No se pudo conectar con LM Studio, cambiando a modo reglas
```

## 🔧 Solución de Problemas

### LM Studio No Conecta
1. Verificar que LM Studio esté ejecutándose
2. Confirmar que el puerto 1234 esté disponible
3. Verificar que el modelo esté cargado
4. Revisar la configuración de `LM_STUDIO_URL`

### Tests Fallan
```bash
# Verificar configuración del entorno
python -c "import os; print('INVEST_MODE:', os.getenv('INVEST_MODE', 'NO_SET'))"

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### Problemas de Importación
```bash
# Verificar estructura de módulos
python -c "import modules.invest_agent; print('OK')"
python -c "import clients.lm_studio_client; print('OK')"
```

## 📈 Métricas de Calidad

- **Cobertura de Tests**: 35 tests unitarios
- **Criterios INVEST**: 6 criterios implementados completamente
- **Modos de Evaluación**: 2 (reglas + gptoss)
- **Arquitectura**: Modular y escalable
- **Documentación**: Completa con ejemplos

## 🤝 Contribución

1. El código está completamente modularizado
2. Tests unitarios incluidos para todas las funcionalidades
3. Documentación integrada en el código
4. Configuración flexible vía variables de entorno
5. Manejo robusto de errores y fallbacks

## 📄 Licencia

Proyecto de demostración técnica para evaluación de competencias en ingeniería de software.

---

**🎉 Proyecto completado y listo para demostración**
```

### Ejecutar la aplicación
```bash
# Opción 1: Con entorno virtual activado
streamlit run app.py

# Opción 2: Directamente
.\venv\Scripts\python.exe -m streamlit run app.py
```

### Ejecutar pruebas
```bash
# Con entorno virtual activado
python test_project.py

# Directamente
.\venv\Scripts\python.exe test_project.py
```

## 📊 Funcionalidades

### Evaluación INVEST
- **I** (Independiente): Verifica que la HU no dependa de otras
- **N** (Negociable): Identifica flexibilidad en los requerimientos
- **V** (Valiosa): Confirma que aporte valor al usuario/negocio
- **E** (Estimable): Valida que sea suficientemente clara para estimar
- **S** (Small): Verifica que sea de tamaño adecuado (≤30 palabras)
- **T** (Testeable): Confirma que tenga criterios de aceptación verificables

### Modos de Análisis
1. **Modo Rápido (Reglas)**: Evaluación con regex y keywords
2. **Modo Avanzado (GPT-OSS)**: Análisis con modelo de lenguaje avanzado

### Estimación de Tiempos
- Modelo de regresión lineal entrenado con datos históricos
- Features: longitud de HU y criterios INVEST cumplidos
- Comparación entre estimación LLM y regresión

### Interfaz Gráfica
- Carga de archivos CSV
- Tabla interactiva con resultados
- Visualizaciones de estimaciones por Sprint
- Exportación de resultados

## 🔧 Configuración

### Datos de Entrada
Los archivos CSV deben tener la siguiente estructura:

**backlog.csv:**
```csv
ID,Historia,Sprint,Prioridad
H1,"Como usuario quiero...",1,Alta
```

**historicos.csv:**
```csv
ID,Historia,Horas,Criterios_INVEST
H1,"Como usuario...",8,5
```

## 📈 Resultados
El sistema genera:
- Análisis INVEST por historia
- Estimaciones de tiempo (LLM vs Regresión)
- Sugerencias de mejora
- Visualizaciones interactivas
- Reporte exportable en CSV

## 🛠️ Desarrollo
- Código modular y bien comentado
- Salidas estructuradas en JSON
- Manejo de errores robusto
- Optimizado para presentaciones técnicas
