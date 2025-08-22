"""
Demo Técnica: Análisis INVEST y Estimación de Historias de Usuario

Aplicación Streamlit para evaluar historias de usuario con criterios INVEST,
estimar tiempos de desarrollo y visualizar resultados.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
import sys
import logging
from datetime import datetime
from typing import Dict, List

# Configurar logging
logger = logging.getLogger(__name__)

# Agregar directorio modules al path
sys.path.append('modules')

try:
    from modules.integration import InvestPipeline, procesar_backlog
    from modules.invest_agent import InvestAgent
    from modules.regression_model import TimeEstimationModel, quick_time_prediction
    from modules.utils import (validate_historia_format, format_invest_result, calculate_invest_score,
                              load_azure_devops_csv, load_csv_data)
except ImportError as e:
    st.error(f"Error importando módulos: {e}")
    st.stop()

# Configuración de página
st.set_page_config(
    page_title="Demo INVEST - Análisis de Historias de Usuario",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 5px solid #1f77b4;
}

.story-excellent {
    background-color: #d4edda;
    border-left: 5px solid #28a745;
    padding: 0.5rem;
    margin: 0.25rem 0;
}

.story-deficient {
    background-color: #f8d7da;
    border-left: 5px solid #dc3545;
    padding: 0.5rem;
    margin: 0.25rem 0;
}

.story-regular {
    background-color: #fff3cd;
    border-left: 5px solid #ffc107;
    padding: 0.5rem;
    margin: 0.25rem 0;
}

.story-good {
    background-color: #cce5ff;
    border-left: 5px solid #007bff;
    padding: 0.5rem;
    margin: 0.25rem 0;
}
</style>
""", unsafe_allow_html=True)

def main():
    """Función principal de la aplicación."""
    
    # Título principal
    st.title("📊 Demo Técnica: Análisis INVEST")
    st.markdown("**Evaluación de calidad y estimación inteligente de historias de usuario**")
    
    # Sidebar para configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Leer modo desde variable de entorno
        env_modo = os.getenv("INVEST_MODE", "").lower()
        
        # Mapear valor de variable de entorno a opciones de UI
        if env_modo in ["reglas", "rules"]:
            default_modo = "Rápido (Reglas)"
        elif env_modo in ["gptoss", "gpt", "advanced"]:
            default_modo = "Avanzado (GPT-OSS)"
        else:
            default_modo = "Rápido (Reglas)"  # Por defecto
        
        # Si hay variable de entorno, mostrar info
        if env_modo:
            st.info(f"🌍 Modo desde variable de entorno: `INVEST_MODE={env_modo}`")
        
        # Modo de análisis (con valor por defecto desde env)
        opciones_modo = ["Rápido (Reglas)", "Avanzado (GPT-OSS)"]
        index_default = opciones_modo.index(default_modo)
        
        modo_analisis = st.selectbox(
            "Modo de Análisis INVEST:",
            opciones_modo,
            index=index_default,
            help="Rápido usa reglas predefinidas, Avanzado usa modelo de lenguaje. Configurable con variable de entorno INVEST_MODE=reglas|gptoss"
        )
        
        modo_invest = "reglas" if modo_analisis == "Rápido (Reglas)" else "gptoss"
        
        st.markdown("---")
        
        # Información del sistema
        st.subheader("ℹ️ Información")
        st.markdown(f"""
        **Modo actual:** {modo_analisis}
        
        **Criterios INVEST:**
        - ✅ **I**ndependiente
        - ✅ **N**egociable  
        - ✅ **V**aliosa
        - ✅ **E**stimable
        - ✅ **S**mall
        - ✅ **T**esteable
        """)
    
    # Crear tabs principales
    tab_carga, tab_analisis, tab_individual, tab_visualizacion = st.tabs([
        "📁 Carga de Datos", 
        "🔍 Análisis Completo", 
        "📝 Historia Individual", 
        "📈 Visualización"
    ])
    
    with tab_carga:
        mostrar_carga_datos()
    
    with tab_analisis:
        mostrar_analisis_completo(modo_invest)
    
    with tab_individual:
        mostrar_analisis_individual(modo_invest)
    
    with tab_visualizacion:
        mostrar_visualizaciones()

def mostrar_carga_datos():
    """Muestra la sección de carga de datos."""
    
    st.header("📁 Carga de Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Backlog de Historias")
        
        # Opción de usar datos de ejemplo
        usar_ejemplo = st.checkbox(
            "Usar datos de ejemplo incluidos", 
            value=True,
            help="Utiliza el dataset de ejemplo para pruebas rápidas"
        )
        
        if usar_ejemplo:
            backlog_path = "data/backlog.csv"
            if os.path.exists(backlog_path):
                try:
                    # Usar función de carga para Azure DevOps
                    df_backlog = load_azure_devops_csv(backlog_path)
                    st.success(f"✅ Datos de ejemplo cargados: {len(df_backlog)} historias")
                    st.dataframe(df_backlog, use_container_width=True)
                    
                    # Guardar en session state
                    st.session_state['backlog_data'] = df_backlog
                    st.session_state['backlog_path'] = backlog_path
                    st.session_state['backlog_source'] = 'example'  # Indicar que es archivo de ejemplo
                except Exception as e:
                    st.error(f"❌ Error cargando datos de ejemplo: {str(e)}")
                    logger.error(f"Error cargando backlog de ejemplo: {e}")
                    st.info("💡 Verificando estructura del archivo...")
                    
                    # Mostrar diagnóstico del archivo
                    try:
                        import pandas as pd
                        df_raw = pd.read_csv(backlog_path)
                        st.info(f"📊 Archivo tiene {len(df_raw)} filas y columnas: {df_raw.columns.tolist()}")
                    except Exception as diag_e:
                        st.error(f"No se pudo leer el archivo: {diag_e}")
            else:
                st.error("❌ Archivo de ejemplo no encontrado")
        else:
            # Carga de archivo personalizado
            uploaded_backlog = st.file_uploader(
                "Sube tu archivo de backlog (CSV)",
                type=['csv'],
                help="Debe contener columnas: ID, Historia, Sprint (opcional), Prioridad (opcional)"
            )
            
            if uploaded_backlog is not None:
                try:
                    # Mostrar información del archivo subido
                    st.info(f"📄 Archivo subido: {uploaded_backlog.name} ({uploaded_backlog.size} bytes)")
                    
                    # Usar función de carga para Azure DevOps
                    df_backlog = load_azure_devops_csv(uploaded_backlog)
                    
                    # Validar columnas requeridas (ahora con estructura interna)
                    required_cols = ['ID', 'Historia']
                    missing_cols = [col for col in required_cols if col not in df_backlog.columns]
                    
                    if missing_cols:
                        st.error(f"❌ Columnas faltantes después del mapeo: {missing_cols}")
                        st.info("💡 Verificando estructura del archivo original...")
                        
                        # Diagnóstico del archivo original
                        uploaded_backlog.seek(0)  # Resetear posición del archivo
                        df_original = pd.read_csv(uploaded_backlog)
                        st.info(f"📊 Archivo original tiene columnas: {df_original.columns.tolist()}")
                        st.dataframe(df_original.head(3), use_container_width=True)
                    else:
                        st.success(f"✅ Archivo cargado: {len(df_backlog)} historias")
                        st.dataframe(df_backlog, use_container_width=True)
                        
                        # Guardar en session state
                        st.session_state['backlog_data'] = df_backlog
                        st.session_state['backlog_source'] = 'uploaded'  # Indicar que es archivo subido
                        
                except Exception as e:
                    st.error(f"❌ Error procesando archivo: {str(e)}")
                    logger.error(f"Error procesando archivo subido: {e}")
                    
                    # Diagnóstico adicional
                    try:
                        st.info("🔍 Intentando diagnóstico...")
                        uploaded_backlog.seek(0)  # Resetear posición
                        df_debug = pd.read_csv(uploaded_backlog)
                        st.info(f"📋 Columnas detectadas: {df_debug.columns.tolist()}")
                        st.info(f"📊 Primeras filas:")
                        st.dataframe(df_debug.head(3), use_container_width=True)
                    except Exception as debug_e:
                        st.error(f"Error en diagnóstico: {debug_e}")
                        
                except Exception as e:
                    st.error(f"❌ Error cargando archivo: {str(e)}")
    
    with col2:
        st.subheader("📈 Datos Históricos")
        
        # Opción de usar datos históricos de ejemplo
        usar_historicos = st.checkbox(
            "Usar datos históricos de ejemplo",
            value=True,
            help="Utiliza datos históricos para entrenar el modelo de regresión"
        )
        
        if usar_historicos:
            historicos_path = "data/historicos.csv"
            if os.path.exists(historicos_path):
                # Usar función de carga para Azure DevOps
                df_historicos = load_azure_devops_csv(historicos_path)
                st.success(f"✅ Datos históricos cargados: {len(df_historicos)} ejemplos")
                st.dataframe(df_historicos.head(), use_container_width=True)
                
                # Guardar en session state
                st.session_state['historicos_data'] = df_historicos
                st.session_state['historicos_path'] = historicos_path
            else:
                st.error("❌ Archivo de datos históricos no encontrado")
        else:
            # Carga de archivo histórico personalizado
            uploaded_historicos = st.file_uploader(
                "Sube tu archivo de datos históricos (CSV)",
                type=['csv'],
                help="Debe contener: ID, Historia, Horas, Criterios_INVEST"
            )
            
            if uploaded_historicos is not None:
                try:
                    # Usar función de carga para Azure DevOps
                    df_historicos = load_azure_devops_csv(uploaded_historicos)
                    
                    required_cols = ['Historia', 'Horas', 'Criterios_INVEST']
                    missing_cols = [col for col in required_cols if col not in df_historicos.columns]
                    
                    if missing_cols:
                        st.error(f"❌ Columnas faltantes: {missing_cols}")
                    else:
                        st.success(f"✅ Datos históricos cargados: {len(df_historicos)} ejemplos")
                        st.dataframe(df_historicos.head(), use_container_width=True)
                        
                        # Guardar en session state
                        st.session_state['historicos_data'] = df_historicos
                        st.session_state['historicos_path'] = None
                        
                except Exception as e:
                    st.error(f"❌ Error cargando archivo histórico: {str(e)}")

def mostrar_analisis_completo(modo_invest: str):
    """Muestra el análisis completo del backlog."""
    
    st.header("🔍 Análisis Completo del Backlog")
    
    if 'backlog_data' not in st.session_state:
        st.warning("⚠️ Primero carga los datos en la pestaña 'Carga de Datos'")
        return
    
    # Botón para procesar
    if st.button("🚀 Procesar Backlog Completo", type="primary"):
        
        with st.spinner(f"Procesando backlog en modo {modo_invest}..."):
            try:
                # Crear pipeline
                historicos_path = st.session_state.get('historicos_path')
                pipeline = InvestPipeline(modo_invest=modo_invest, historicos_path=historicos_path)
                
                # Procesar usando DataFrame directamente o desde archivo
                if st.session_state.get('backlog_source') == 'uploaded':
                    # Usar DataFrame directamente para archivos subidos
                    resultados = pipeline.procesar_backlog_dataframe(st.session_state['backlog_data'])
                elif st.session_state.get('backlog_path'):
                    # Usar archivo para datos de ejemplo
                    resultados = pipeline.procesar_backlog(st.session_state['backlog_path'])
                else:
                    st.error("❌ No hay datos de backlog disponibles")
                    return
                
                # Guardar resultados en session state
                st.session_state['resultados_analisis'] = resultados
                st.session_state['pipeline'] = pipeline
                
                st.success("✅ Análisis completado exitosamente!")
                
            except Exception as e:
                st.error(f"❌ Error en el análisis: {str(e)}")
                return
    
    # Mostrar resultados si están disponibles
    if 'resultados_analisis' in st.session_state:
        mostrar_resultados_analisis(st.session_state['resultados_analisis'])

def mostrar_resultados_analisis(resultados: List[Dict]):
    """Muestra los resultados del análisis."""
    
    st.subheader("📊 Resultados del Análisis")
    
    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)
    
    total_historias = len(resultados)
    score_promedio = sum(r['score_invest'] for r in resultados) / total_historias
    historias_excelentes = sum(1 for r in resultados if r['estado_calidad'] == 'Excelente')
    historias_deficientes = sum(1 for r in resultados if r['estado_calidad'] == 'Deficiente')
    
    with col1:
        st.metric("Total Historias", total_historias)
    with col2:
        st.metric("Score INVEST Promedio", f"{score_promedio:.2f}")
    with col3:
        st.metric("Historias Excelentes", f"{historias_excelentes} ({historias_excelentes/total_historias*100:.1f}%)")
    with col4:
        st.metric("Historias Deficientes", f"{historias_deficientes} ({historias_deficientes/total_historias*100:.1f}%)")
    
    # Tabla de resultados
    st.subheader("📋 Detalle de Historias")
    
    # Preparar DataFrame para mostrar
    df_resultados = pd.DataFrame(resultados)
    
    # Formatear columnas INVEST para visualización
    invest_cols = ['Independiente', 'Negociable', 'Valiosa', 'Estimable', 'Small', 'Testeable']
    for col in invest_cols:
        df_resultados[f'INVEST_{col}'] = df_resultados['INVEST'].apply(
            lambda x: '✅' if x.get(col, False) else '❌'
        )
    
    # Seleccionar columnas para mostrar
    columnas_mostrar = [
        'id', 'historia', 'sprint', 'prioridad', 'score_invest', 'estado_calidad',
        'estimacion_llm', 'estimacion_regresion', 'diferencia_estimacion'
    ] + [f'INVEST_{col}' for col in invest_cols]
    
    df_display = df_resultados[columnas_mostrar].copy()
    
    # Renombrar columnas para mejor visualización
    df_display.columns = [
        'ID', 'Historia', 'Sprint', 'Prioridad', 'Score INVEST', 'Estado',
        'Est. LLM', 'Est. Regresión', 'Diferencia'
    ] + [f'{col}' for col in invest_cols]
    
    # Aplicar colores según estado
    def color_estado(val):
        if val == 'Excelente':
            return 'background-color: #1E9014'
        elif val == 'Deficiente':
            return 'background-color: #8F2222'
        elif val == 'Regular':
            return 'background-color: #D16D21'
        else:
            return 'background-color: #1885AD'
    
    styled_df = df_display.style.map(color_estado, subset=['Estado'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Mostrar detalles de historia seleccionada
    st.subheader("🔍 Detalle de Historia")
    
    historia_seleccionada = st.selectbox(
        "Selecciona una historia para ver detalles:",
        options=range(len(resultados)),
        format_func=lambda x: f"{resultados[x]['id']} - {resultados[x]['historia'][:50]}..."
    )
    
    if historia_seleccionada is not None:
        resultado = resultados[historia_seleccionada]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**ID:** {resultado['id']}")
            st.markdown(f"**Historia:** {resultado['historia']}")
            st.markdown(f"**Estado:** {resultado['estado_calidad']}")
            
            # Mostrar sugerencias
            if resultado['sugerencias']:
                st.markdown("**Sugerencias de mejora:**")
                for i, sugerencia in enumerate(resultado['sugerencias'], 1):
                    st.markdown(f"{i}. {sugerencia}")
        
        with col2:
            st.markdown("**Criterios INVEST:**")
            invest_scores = resultado['INVEST']
            for criterio, cumple in invest_scores.items():
                icono = '✅' if cumple else '❌'
                st.markdown(f"{icono} {criterio}")
            
            st.markdown(f"**Score:** {resultado['score_invest']}")
            st.markdown(f"**Est. LLM:** {resultado['estimacion_llm']}h")
            st.markdown(f"**Est. Regresión:** {resultado['estimacion_regresion']}h")
    
    # Botón de exportación
    if st.button("📥 Exportar Resultados a CSV"):
        try:
            pipeline = st.session_state.get('pipeline')
            if pipeline:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"resultados_invest_{timestamp}.csv"
                
                if pipeline.exportar_resultados(resultados, output_path):
                    st.success(f"✅ Resultados exportados a {output_path}")
                    
                    # Opción de descarga
                    with open(output_path, 'rb') as file:
                        st.download_button(
                            label="⬇️ Descargar archivo CSV",
                            data=file.read(),
                            file_name=output_path,
                            mime='text/csv'
                        )
                else:
                    st.error("❌ Error exportando resultados")
        except Exception as e:
            st.error(f"❌ Error en exportación: {str(e)}")

def mostrar_analisis_individual(modo_invest: str):
    """Muestra el análisis de una historia individual."""
    
    st.header("📝 Análisis de Historia Individual")
    
    # Input para historia
    historia_input = st.text_area(
        "Ingresa una historia de usuario:",
        height=100,
        placeholder="Como usuario quiero iniciar sesión en el sistema para acceder a mi panel personal",
        help="Formato recomendado: Como [rol] quiero [acción] para [beneficio]"
    )
    
    historia_id = st.text_input(
        "ID de la historia (opcional):",
        placeholder="H_001"
    )
    
    if st.button("🔍 Analizar Historia", type="primary"):
        if not historia_input.strip():
            st.error("❌ Por favor ingresa una historia de usuario")
            return
        
        with st.spinner("Analizando historia..."):
            try:
                # Crear agente INVEST
                agent = InvestAgent(modo=modo_invest)
                
                # Evaluar historia
                resultado = agent.evaluate_story(historia_input, historia_id or "H_INDIVIDUAL")
                
                # Mostrar resultados
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("📊 Resultados del Análisis")
                    
                    # Información general
                    st.markdown(f"**Historia:** {historia_input}")
                    st.markdown(f"**ID:** {resultado.id}")
                    st.markdown(f"**Modo de evaluación:** {resultado.modo_evaluacion}")
                    
                    # Score general
                    score = calculate_invest_score(resultado.invest_scores)
                    if score >= 0.8:
                        estado = "Excelente ✨"
                        color = "green"
                    elif score >= 0.6:
                        estado = "Buena 👍"
                        color = "blue"
                    elif score >= 0.4:
                        estado = "Regular ⚠️"
                        color = "orange"
                    else:
                        estado = "Deficiente ❌"
                        color = "red"
                    
                    st.markdown(f"**Estado de calidad:** :{color}[{estado}]")
                    st.progress(score)
                    st.markdown(f"**Score INVEST:** {score:.2f}/1.0")
                
                with col2:
                    st.subheader("✅ Criterios INVEST")
                    
                    for criterio, cumple in resultado.invest_scores.items():
                        icono = '✅' if cumple else '❌'
                        color = 'green' if cumple else 'red'
                        st.markdown(f":{color}[{icono} {criterio}]")
                
                # Sugerencias
                if resultado.sugerencias:
                    st.subheader("💡 Sugerencias de Mejora")
                    for i, sugerencia in enumerate(resultado.sugerencias, 1):
                        st.markdown(f"{i}. {sugerencia}")
                
                # Estimación de tiempo
                st.subheader("⏱️ Estimación de Tiempo")
                
                # Crear modelo de tiempo para estimación
                time_model = TimeEstimationModel()
                historicos_path = st.session_state.get('historicos_path')
                
                if historicos_path and os.path.exists(historicos_path):
                    try:
                        time_model.train_model(historicos_path)
                    except:
                        pass  # Usar estimación heurística
                
                tiempo_estimado = time_model.predict_tiempo(historia_input, resultado.to_dict())
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Tiempo Estimado", f"{tiempo_estimado} horas")
                with col2:
                    if tiempo_estimado <= 8:
                        complejidad = "Baja 🟢"
                    elif tiempo_estimado <= 16:
                        complejidad = "Media 🟡"
                    else:
                        complejidad = "Alta 🔴"
                    st.metric("Complejidad", complejidad)
                
                # JSON output
                with st.expander("🔧 Resultado en JSON"):
                    st.json(resultado.to_dict())
                
            except Exception as e:
                st.error(f"❌ Error en el análisis: {str(e)}")

def mostrar_visualizaciones():
    """Muestra las visualizaciones de los resultados."""
    
    st.header("📈 Visualizaciones")
    
    if 'resultados_analisis' not in st.session_state:
        st.warning("⚠️ Primero ejecuta el análisis completo para ver las visualizaciones")
        return
    
    resultados = st.session_state['resultados_analisis']
    df = pd.DataFrame(resultados)
    
    # Gráfico de distribución de scores INVEST
    st.subheader("📊 Distribución de Scores INVEST")
    
    fig_hist = px.histogram(
        df, 
        x='score_invest', 
        nbins=10,
        title="Distribución de Scores INVEST",
        labels={'score_invest': 'Score INVEST', 'count': 'Número de Historias'},
        color_discrete_sequence=['#1f77b4']
    )
    fig_hist.update_layout(showlegend=False)
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Gráfico de estado de calidad
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Estado de Calidad")
        
        estado_counts = df['estado_calidad'].value_counts()
        colors = {
            'Excelente': '#28a745',
            'Buena': '#007bff', 
            'Regular': '#ffc107',
            'Deficiente': '#dc3545'
        }
        
        fig_pie = px.pie(
            values=estado_counts.values,
            names=estado_counts.index,
            title="Distribución de Estados de Calidad",
            color=estado_counts.index,
            color_discrete_map=colors
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("📈 Estimaciones por Sprint")
        
        sprint_data = df.groupby('sprint').agg({
            'estimacion_llm': 'sum',
            'estimacion_regresion': 'sum',
            'id': 'count'
        }).reset_index()
        sprint_data.columns = ['Sprint', 'Est. LLM', 'Est. Regresión', 'Historias']
        
        fig_sprint = px.bar(
            sprint_data,
            x='Sprint',
            y=['Est. LLM', 'Est. Regresión'],
            title="Tiempo Estimado por Sprint",
            labels={'value': 'Horas', 'variable': 'Tipo de Estimación'},
            barmode='group'
        )
        st.plotly_chart(fig_sprint, use_container_width=True)
    
    # Análisis detallado de criterios INVEST
    st.subheader("🔍 Análisis Detallado de Criterios INVEST")
    
    # Extraer datos de criterios INVEST
    criterios_data = []
    criterios = ['Independiente', 'Negociable', 'Valiosa', 'Estimable', 'Small', 'Testeable']
    
    for criterio in criterios:
        cumplimiento = sum(1 for r in resultados if r['INVEST'].get(criterio, False))
        porcentaje = (cumplimiento / len(resultados)) * 100
        criterios_data.append({
            'Criterio': criterio,
            'Cumplimiento': cumplimiento,
            'Porcentaje': porcentaje
        })
    
    df_criterios = pd.DataFrame(criterios_data)
    
    fig_criterios = px.bar(
        df_criterios,
        x='Criterio',
        y='Porcentaje',
        title="Cumplimiento de Criterios INVEST",
        labels={'Porcentaje': 'Porcentaje de Cumplimiento (%)'},
        color='Porcentaje',
        color_continuous_scale='RdYlGn'
    )
    fig_criterios.update_layout(showlegend=False)
    st.plotly_chart(fig_criterios, use_container_width=True)
    
    # Correlación entre score INVEST y estimaciones
    st.subheader("🔗 Correlación Score INVEST vs Estimaciones")
    
    fig_scatter = px.scatter(
        df,
        x='score_invest',
        y='estimacion_regresion',
        size='estimacion_llm',
        color='estado_calidad',
        title="Relación entre Score INVEST y Estimación de Tiempo",
        labels={
            'score_invest': 'Score INVEST',
            'estimacion_regresion': 'Estimación Regresión (horas)',
            'estimacion_llm': 'Estimación LLM (horas)'
        },
        hover_data=['id', 'sprint']
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Resumen por sprint
    if 'pipeline' in st.session_state:
        st.subheader("📋 Resumen por Sprint")
        
        pipeline = st.session_state['pipeline']
        resumen_sprint = pipeline.generar_resumen_sprint(resultados)
        
        # Convertir a DataFrame para mejor visualización
        df_resumen = pd.DataFrame.from_dict(resumen_sprint, orient='index').reset_index()
        df_resumen.columns = [
            'Sprint', 'Historias', 'Tiempo LLM Total', 'Tiempo Regresión Total',
            'Historias Excelentes', 'Historias Deficientes', 'Score INVEST Promedio'
        ]
        
        st.dataframe(df_resumen, use_container_width=True)

if __name__ == "__main__":
    main()
