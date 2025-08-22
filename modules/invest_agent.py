"""
Agente para evaluación INVEST de historias de usuario.
Orquesta la evaluación usando reglas o LM Studio API.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

# Agregar paths necesarios
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Importar módulos modularizados
from modules.invest_result import InvestResult
from clients.lm_studio_client import LMStudioClient
from modules.invest_criteria import InvestCriteriaEvaluator
from modules.utils import validate_historia_format, get_default_invest_structure

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InvestAgent:
    """
    Agente principal para evaluación INVEST de historias de usuario.
    Orquesta la evaluación usando reglas o LM Studio API.
    """
    
    def __init__(self, modo: str = "gptoss"):
        """
        Inicializa el agente INVEST.
        
        Args:
            modo (str): "reglas" para modo rápido, "gptoss" para avanzado
        """
        self.modo = modo.lower()
        self.lm_client = None
        self.criteria_evaluator = InvestCriteriaEvaluator()
        
        # Inicializar cliente LM Studio si está en modo gptoss
        if self.modo == "gptoss":
            self._initialize_lm_studio()
        else:
            logger.info("🔧 Modo de reglas activado")
    
    def _initialize_lm_studio(self):
        """Inicializa cliente LM Studio para modo gptoss."""
        try:
            self.lm_client = LMStudioClient()
            
            if self.lm_client.connect():
                logger.info("✅ LM Studio conectado exitosamente")
            else:
                logger.warning("⚠️ No se pudo conectar con LM Studio, cambiando a modo reglas")
                self.modo = "reglas"
                self.lm_client = None
                
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando LM Studio: {str(e)}")
            logger.info("🔄 Cambiando a modo rápido (reglas)")
            self.modo = "reglas"
            self.lm_client = None
    
    def evaluate_story(self, historia: str, story_id: str = "AUTO") -> InvestResult:
        """
        Evalúa una historia de usuario usando criterios INVEST.
        
        Args:
            historia (str): Historia de usuario a evaluar
            story_id (str): ID único para la historia
            
        Returns:
            InvestResult: Resultado de la evaluación
        """
        if story_id == "AUTO":
            story_id = f"STORY_{hash(historia) % 10000:04d}"
        
        # Validar formato básico
        if not validate_historia_format(historia):
            return InvestResult(
                id=story_id,
                historia=historia,
                invest_scores=get_default_invest_structure()["INVEST"],
                sugerencias=["Formato de historia de usuario inválido"],
                modo_evaluacion=self.modo
            )
        
        # Evaluar según el modo
        if self.modo == "gptoss" and self.lm_client and self.lm_client.is_available():
            return self._evaluate_with_lm_studio(historia, story_id)
        else:
            return self._evaluate_with_rules(historia, story_id)
    
    def _evaluate_with_rules(self, historia: str, story_id: str) -> InvestResult:
        """
        Evalúa historia usando reglas predefinidas.
        
        Args:
            historia: Historia de usuario
            story_id: ID de la historia
            
        Returns:
            InvestResult: Resultado de evaluación
        """
        invest_scores = {}
        all_suggestions = []
        
        # Evaluar cada criterio INVEST
        criterios = {
            "Independiente": self.criteria_evaluator.evaluate_independent,
            "Negociable": self.criteria_evaluator.evaluate_negotiable,
            "Valiosa": self.criteria_evaluator.evaluate_valuable,
            "Estimable": self.criteria_evaluator.evaluate_estimable,
            "Small": self.criteria_evaluator.evaluate_small,
            "Testeable": self.criteria_evaluator.evaluate_testable
        }
        
        for criterion, evaluator_func in criterios.items():
            passed, suggestions = evaluator_func(historia)
            invest_scores[criterion] = passed
            all_suggestions.extend(suggestions)
        
        return InvestResult(
            id=story_id,
            historia=historia,
            invest_scores=invest_scores,
            sugerencias=all_suggestions,
            modo_evaluacion="reglas"
        )
    
    def _evaluate_with_lm_studio(self, historia: str, story_id: str) -> InvestResult:
        """
        Evalúa historia usando LM Studio API.
        
        Args:
            historia: Historia de usuario
            story_id: ID de la historia
            
        Returns:
            InvestResult: Resultado de evaluación
        """
        # Intentar evaluación con LM Studio
        lm_result = self.lm_client.evaluate_invest_story(historia)
        
        if lm_result:
            # Extraer scores INVEST
            invest_scores = {
                "Independiente": lm_result.get("Independiente", False),
                "Negociable": lm_result.get("Negociable", False),
                "Valiosa": lm_result.get("Valiosa", False),
                "Estimable": lm_result.get("Estimable", False),
                "Small": lm_result.get("Small", False),
                "Testeable": lm_result.get("Testeable", False)
            }
            
            sugerencias = lm_result.get("sugerencias", [])
            
            return InvestResult(
                id=story_id,
                historia=historia,
                invest_scores=invest_scores,
                sugerencias=sugerencias,
                modo_evaluacion="gptoss"
            )
        else:
            # Fallback a reglas si LM Studio falla
            logger.info("🔄 LM Studio no disponible, usando reglas")
            return self._evaluate_with_rules(historia, story_id)
    
    def evaluate_stories_batch(self, historias: List[str]) -> List[InvestResult]:
        """
        Evalúa múltiples historias en lote.
        
        Args:
            historias: Lista de historias de usuario
            
        Returns:
            List[InvestResult]: Lista de resultados
        """
        results = []
        for i, historia in enumerate(historias, 1):
            story_id = f"BATCH_{i:03d}"
            result = self.evaluate_story(historia, story_id)
            results.append(result)
        
        return results
    
    def get_evaluation_summary(self, results: List[InvestResult]) -> Dict:
        """
        Genera resumen de evaluaciones.
        
        Args:
            results: Lista de resultados de evaluación
            
        Returns:
            dict: Resumen estadístico
        """
        if not results:
            return {"error": "No hay resultados para analizar"}
        
        total_stories = len(results)
        criteria_stats = {
            "Independiente": 0, "Negociable": 0, "Valiosa": 0,
            "Estimable": 0, "Small": 0, "Testeable": 0
        }
        
        for result in results:
            for criterion, passed in result.invest_scores.items():
                if passed:
                    criteria_stats[criterion] += 1
        
        # Calcular porcentajes
        criteria_percentages = {
            criterion: round((count / total_stories) * 100, 1)
            for criterion, count in criteria_stats.items()
        }
        
        # Historias que pasan todos los criterios
        fully_compliant = sum(1 for result in results 
                            if all(result.invest_scores.values()))
        
        return {
            "total_historias": total_stories,
            "completamente_invest": fully_compliant,
            "porcentaje_completas": round((fully_compliant / total_stories) * 100, 1),
            "criterios_porcentaje": criteria_percentages,
            "modo_evaluacion": results[0].modo_evaluacion if results else "unknown"
        }
    
    def is_lm_studio_available(self) -> bool:
        """Verifica si LM Studio está disponible."""
        return (self.lm_client is not None and 
                self.lm_client.is_available())
    
    def get_mode(self) -> str:
        """Retorna el modo actual de evaluación."""
        return self.modo
