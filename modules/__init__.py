"""
Módulos para la demo técnica de análisis INVEST.
"""

__version__ = "1.0.0"
__author__ = "Demo INVEST Team"

# Exportar componentes principales
from .invest_result import InvestResult, InvestEvaluation  
from .invest_criteria import InvestCriteriaEvaluator
from . import utils

__all__ = [
    'InvestResult', 
    'InvestEvaluation',
    'InvestCriteriaEvaluator',
    'utils'
]
