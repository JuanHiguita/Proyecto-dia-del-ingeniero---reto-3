"""
Clases de datos y estructuras para resultados INVEST.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class InvestResult:
    """Estructura para resultados de evaluación INVEST."""
    id: str
    historia: str
    invest_scores: Dict[str, bool]
    sugerencias: List[str]
    modo_evaluacion: str = "reglas"
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario para JSON."""
        return {
            "id": self.id,
            "historia": self.historia,
            "INVEST": self.invest_scores,
            "sugerencias": self.sugerencias,
            "modo": self.modo_evaluacion
        }


@dataclass
class InvestEvaluation:
    """Estructura para evaluación individual de criterio INVEST."""
    criterion: str
    passed: bool
    suggestions: List[str]
    confidence: float = 1.0
    
    def __post_init__(self):
        """Validar después de inicialización."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence debe estar entre 0.0 y 1.0")
        
        if self.criterion not in ["Independiente", "Negociable", "Valiosa", "Estimable", "Small", "Testeable"]:
            raise ValueError(f"Criterio INVEST inválido: {self.criterion}")
