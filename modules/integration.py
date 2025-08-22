"""
Módulo de integración para orquestar el pipeline completo.
Procesa backlog de historias con análisis INVEST y estimación de tiempos.
"""

import pandas as pd
import logging
import os
from typing import List, Dict, Optional
from .utils import load_csv_data, validate_csv_structure, export_results_to_csv, load_azure_devops_csv
from .invest_agent import InvestAgent
from .regression_model import TimeEstimationModel

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InvestPipeline:
    """
    Pipeline completo para procesamiento de backlog con INVEST y estimación.
    """
    
    def __init__(self, modo_invest: str = None, 
                historicos_path: Optional[str] = None):
        """
        Inicializa el pipeline de procesamiento.
        
        Args:
            modo_invest (str): "reglas" o "gptoss" para evaluación INVEST. 
            Si es None, lee desde variable de entorno INVEST_MODE
            historicos_path (str, optional): Ruta a datos históricos para entrenar regresión
        """
        # Si no se especifica modo, leer desde variable de entorno
        if modo_invest is None:
            env_modo = os.getenv("INVEST_MODE", "reglas").lower()
            # Normalizar valores de variable de entorno
            if env_modo in ["reglas", "rules"]:
                modo_invest = "reglas"
            elif env_modo in ["gptoss", "gpt", "advanced"]:
                modo_invest = "gptoss"
            else:
                modo_invest = "reglas"  # Por defecto
                logger.warning(f"Valor INVEST_MODE no reconocido: '{env_modo}'. Usando 'reglas'")
        
        self.modo_invest = modo_invest
        self.historicos_path = historicos_path
        
        logger.info(f"Inicializando pipeline en modo: {self.modo_invest}")
        
        # Inicializar componentes
        self.invest_agent = InvestAgent(modo=modo_invest)
        self.time_model = TimeEstimationModel()
        
        # Entrenar modelo de tiempo si se proporcionan datos históricos
        if historicos_path:
            self._initialize_time_model()
    
    def _initialize_time_model(self):
        """Inicializa y entrena el modelo de estimación de tiempo."""
        try:
            logger.info("Entrenando modelo de estimación de tiempo...")
            metrics = self.time_model.train_model(self.historicos_path)
            logger.info(f"Modelo entrenado. MAE: {metrics['test_mae']} horas")
        except Exception as e:
            logger.warning(f"No se pudo entrenar modelo de tiempo: {str(e)}")
            logger.info("Usando estimación heurística")
    
    def _estimate_llm_time(self, historia: str, invest_result: Dict) -> float:
        """
        Estimación de tiempo usando LM Studio (GPT-OSS).
        
        Args:
            historia (str): Historia de usuario
            invest_result (Dict): Resultado de evaluación INVEST
            
        Returns:
            float: Estimación en horas
        """
        # Intentar estimación con LM Studio si está disponible y en modo gptoss
        if (self.modo_invest == "gptoss" and 
            hasattr(self.invest_agent, 'lm_client') and 
            self.invest_agent.lm_client and 
            self.invest_agent.lm_client.is_available()):
            
            invest_scores = invest_result.get('INVEST', {})
            tiempo_llm = self.invest_agent.lm_client.estimate_development_time(historia, invest_scores)
            
            if tiempo_llm is not None:
                logger.info(f"⏱️ Estimación LLM exitosa: {tiempo_llm} horas")
                return tiempo_llm
            else:
                logger.warning("🔄 LLM no pudo estimar tiempo, usando fallback heurístico")
        
        # Fallback a estimación heurística si LLM no está disponible
        return self._estimate_heuristic_time(historia, invest_result)
    
    def _estimate_heuristic_time(self, historia: str, invest_result: Dict) -> float:
        """
        Estimación heurística de respaldo cuando LLM no está disponible.
        
        Args:
            historia (str): Historia de usuario
            invest_result (Dict): Resultado de evaluación INVEST
            
        Returns:
            float: Estimación en horas
        """
        from utils import count_words
        
        # Estimación base por longitud
        palabras = count_words(historia)
        
        if palabras <= 8:
            base_time = 4
        elif palabras <= 15:
            base_time = 8
        elif palabras <= 25:
            base_time = 12
        else:
            base_time = 16
        
        # Ajustar por criterios INVEST cumplidos
        invest_scores = invest_result.get('INVEST', {})
        criterios_cumplidos = sum(1 for v in invest_scores.values() if v)
        
        # Factor de complejidad basado en INVEST
        if criterios_cumplidos >= 5:
            factor = 0.8  # Bien definida, menos tiempo
        elif criterios_cumplidos >= 3:
            factor = 1.0  # Normal
        else:
            factor = 1.3  # Mal definida, más tiempo
        
        # Ajustes específicos por criterio
        if not invest_scores.get('Estimable', True):
            factor *= 1.2  # Dificultad para estimar = más tiempo
        
        if not invest_scores.get('Small', True):
            factor *= 1.3  # Historia grande = más tiempo
        
        if not invest_scores.get('Testeable', True):
            factor *= 1.1  # Difícil de probar = tiempo extra
        
        tiempo_estimado = base_time * factor
        
        # Agregar variación realista (±15%)
        import random
        variacion = random.uniform(0.85, 1.15)
        tiempo_estimado *= variacion

        return round(tiempo_estimado, 1)
    
    def _process_single_story(self, row: pd.Series) -> Dict:
        """
        Procesa una historia individual.
        
        Args:
            row (pd.Series): Fila del DataFrame con datos de la historia
            
        Returns:
            Dict: Resultado procesado de la historia
        """
        # Obtener datos de la historia
        historia_id = str(row.get('ID', ''))
        historia_text = str(row.get('Historia', ''))
        sprint = row.get('Sprint', 1)
        prioridad = row.get('Prioridad', 'Media')
        
        try:
            # Evaluación INVEST
            invest_result = self.invest_agent.evaluate_story(historia_text, historia_id)
            invest_dict = invest_result.to_dict()
            
            # Estimación LLM (ahora usa GPT-OSS cuando está disponible)
            estimacion_llm = self._estimate_llm_time(historia_text, invest_dict)
            
            # Determinar método de estimación usado
            metodo_estimacion = "LLM (GPT-OSS)" if (
                self.modo_invest == "gptoss" and 
                hasattr(self.invest_agent, 'lm_client') and 
                self.invest_agent.lm_client and 
                self.invest_agent.lm_client.is_available()
            ) else "Heurística"
            
            # Estimación por regresión
            estimacion_regresion = self.time_model.predict_tiempo(historia_text, invest_dict)
            
            # Calcular score INVEST
            invest_scores = invest_dict['INVEST']
            score_invest = sum(1 for v in invest_scores.values() if v) / len(invest_scores)
            
            # Determinar estado de calidad
            if score_invest >= 0.8:
                estado_calidad = "Excelente"
            elif score_invest >= 0.6:
                estado_calidad = "Buena"
            elif score_invest >= 0.4:
                estado_calidad = "Regular"
            else:
                estado_calidad = "Deficiente"
            
            return {
                "id": historia_id,
                "historia": historia_text,
                "sprint": sprint,
                "prioridad": prioridad,
                "INVEST": invest_scores,
                "score_invest": round(score_invest, 2),
                "estado_calidad": estado_calidad,
                "estimacion_llm": estimacion_llm,
                "metodo_estimacion": metodo_estimacion,
                "estimacion_regresion": estimacion_regresion,
                "diferencia_estimacion": round(abs(estimacion_llm - estimacion_regresion), 1),
                "sugerencias": invest_dict.get('sugerencias', []),
                "modo_evaluacion": invest_dict.get('modo', self.modo_invest)
            }
            
        except Exception as e:
            logger.error(f"Error procesando historia {historia_id}: {str(e)}")
            return {
                "id": historia_id,
                "historia": historia_text,
                "sprint": sprint,
                "prioridad": prioridad,
                "INVEST": {
                    "Independiente": False,
                    "Negociable": False,
                    "Valiosa": False,
                    "Estimable": False,
                    "Small": False,
                    "Testeable": False
                },
                "score_invest": 0.0,
                "estado_calidad": "Error",
                "estimacion_llm": 8.0,
                "estimacion_regresion": 8.0,
                "diferencia_estimacion": 0.0,
                "sugerencias": [f"Error procesando historia: {str(e)}"],
                "modo_evaluacion": self.modo_invest
            }
    
    def procesar_backlog(self, backlog_path: str) -> List[Dict]:
        """
        Procesa backlog completo de historias desde archivo.
        
        Args:
            backlog_path (str): Ruta al archivo CSV del backlog
            
        Returns:
            List[Dict]: Lista de resultados procesados
        """
        try:
            # Cargar backlog usando formato Azure DevOps
            df_backlog = load_azure_devops_csv(backlog_path)
            return self.procesar_backlog_dataframe(df_backlog)
            
        except Exception as e:
            logger.error(f"Error procesando backlog: {e}")
            raise
    
    def procesar_backlog_dataframe(self, df_backlog: pd.DataFrame) -> List[Dict]:
        """
        Procesa backlog completo de historias desde DataFrame.
        
        Args:
            df_backlog (pd.DataFrame): DataFrame con estructura interna del backlog
            
        Returns:
            List[Dict]: Lista de resultados procesados
        """
        try:
            # Validar estructura (ahora con estructura interna)
            required_columns = ['ID', 'Historia']
            if not validate_csv_structure(df_backlog, required_columns):
                raise ValueError(f"El backlog debe contener las columnas: {required_columns}")

            logger.info(f"Procesando {len(df_backlog)} historias en modo {self.modo_invest}")
            
            # Procesar cada historia
            resultados = []
            for idx, row in df_backlog.iterrows():
                logger.info(f"Procesando historia {idx + 1}/{len(df_backlog)}: {row['ID']}")
                resultado = self._process_single_story(row)
                resultados.append(resultado)
            
            logger.info("✅ Procesamiento completado")
            return resultados
            
        except Exception as e:
            logger.error(f"Error procesando backlog DataFrame: {e}")
            raise
            raise
    
    def generar_resumen_sprint(self, resultados: List[Dict]) -> Dict:
        """
        Genera resumen por sprint de los resultados.
        
        Args:
            resultados (List[Dict]): Resultados procesados
            
        Returns:
            Dict: Resumen por sprint
        """
        resumen = {}
        
        for resultado in resultados:
            sprint = resultado.get('sprint', 1)
            
            if sprint not in resumen:
                resumen[sprint] = {
                    'historias': 0,
                    'tiempo_llm_total': 0,
                    'tiempo_regresion_total': 0,
                    'historias_excelentes': 0,
                    'historias_deficientes': 0,
                    'score_invest_promedio': 0
                }
            
            resumen[sprint]['historias'] += 1
            resumen[sprint]['tiempo_llm_total'] += resultado.get('estimacion_llm', 0)
            resumen[sprint]['tiempo_regresion_total'] += resultado.get('estimacion_regresion', 0)
            
            if resultado.get('estado_calidad') == 'Excelente':
                resumen[sprint]['historias_excelentes'] += 1
            elif resultado.get('estado_calidad') == 'Deficiente':
                resumen[sprint]['historias_deficientes'] += 1
            
            resumen[sprint]['score_invest_promedio'] += resultado.get('score_invest', 0)
        
        # Calcular promedios
        for sprint_data in resumen.values():
            if sprint_data['historias'] > 0:
                sprint_data['score_invest_promedio'] = round(
                    sprint_data['score_invest_promedio'] / sprint_data['historias'], 2
                )
                sprint_data['tiempo_llm_total'] = round(sprint_data['tiempo_llm_total'], 1)
                sprint_data['tiempo_regresion_total'] = round(sprint_data['tiempo_regresion_total'], 1)
        
        return resumen
    
    def exportar_resultados(self, resultados: List[Dict], output_path: str) -> bool:
        """
        Exporta resultados a CSV.
        
        Args:
            resultados (List[Dict]): Resultados a exportar
            output_path (str): Ruta del archivo de salida
            
        Returns:
            bool: True si la exportación fue exitosa
        """
        try:
            # Preparar datos para exportación (aplanar INVEST)
            datos_export = []
            
            for resultado in resultados:
                fila = {
                    'ID': resultado['id'],
                    'Historia': resultado['historia'],
                    'Sprint': resultado['sprint'],
                    'Prioridad': resultado['prioridad'],
                    'Score_INVEST': resultado['score_invest'],
                    'Estado_Calidad': resultado['estado_calidad'],
                    'Estimacion_LLM': resultado['estimacion_llm'],
                    'Estimacion_Regresion': resultado['estimacion_regresion'],
                    'Diferencia_Estimacion': resultado['diferencia_estimacion'],
                    'Modo_Evaluacion': resultado['modo_evaluacion']
                }
                
                # Agregar criterios INVEST individuales
                invest_scores = resultado['INVEST']
                for criterio, cumple in invest_scores.items():
                    fila[f'INVEST_{criterio}'] = 'Sí' if cumple else 'No'
                
                # Agregar sugerencias como texto
                fila['Sugerencias'] = ' | '.join(resultado['sugerencias'])
                
                datos_export.append(fila)
            
            return export_results_to_csv(datos_export, output_path)
            
        except Exception as e:
            logger.error(f"Error exportando resultados: {str(e)}")
            return False

# Función de conveniencia para uso directo
def procesar_backlog(backlog_csv: str, modo: str = "gptoss", 
                    historicos_csv: Optional[str] = None) -> List[Dict]:
    """
    Función de conveniencia para procesar backlog completo.
    
    Args:
        backlog_csv (str): Ruta al archivo de backlog
        modo (str): "reglas" o "gptoss" para evaluación INVEST
        historicos_csv (str, optional): Ruta a datos históricos
        
    Returns:
        List[Dict]: Lista de resultados procesados
    """
    pipeline = InvestPipeline(modo_invest=modo, historicos_path=historicos_csv)
    return pipeline.procesar_backlog(backlog_csv)

if __name__ == "__main__":
    # Pruebas del módulo
    print("🧪 Probando módulo de integración...")
    
    # Crear pipeline
    pipeline = InvestPipeline(modo_invest="gptoss")
    
    print("✅ Pipeline inicializado")
    print(f"Modo INVEST: {pipeline.modo_invest}")
    print(f"Modelo de tiempo entrenado: {pipeline.time_model.is_trained}")
    
    print("✅ Pruebas completadas")
