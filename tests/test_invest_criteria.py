"""
Tests unitarios para los evaluadores de criterios INVEST.
"""

import unittest
import sys
from pathlib import Path

# Agregar path del proyecto
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "modules"))

from invest_criteria import InvestCriteriaEvaluator


class TestInvestCriteriaEvaluator(unittest.TestCase):
    """Tests para la clase InvestCriteriaEvaluator."""
    
    def setUp(self):
        """Configuración antes de cada test."""
        self.evaluator = InvestCriteriaEvaluator()
        
    def test_evaluate_independent_buena(self):
        """Test criterio Independiente con historia buena."""
        historia = "Como usuario quiero hacer login para acceder al sistema"
        passed, suggestions = self.evaluator.evaluate_independent(historia)
        
        self.assertTrue(passed)
        self.assertEqual(len(suggestions), 0)
        
    def test_evaluate_independent_con_dependencia(self):
        """Test criterio Independiente con dependencias."""
        historia = "Como usuario quiero hacer login después de que el sistema esté configurado"
        passed, suggestions = self.evaluator.evaluate_independent(historia)
        
        self.assertFalse(passed)
        self.assertGreater(len(suggestions), 0)
        
    def test_evaluate_negotiable_buena(self):
        """Test criterio Negociable con historia flexible."""
        historia = "Como usuario quiero buscar productos para encontrar lo que necesito"
        passed, suggestions = self.evaluator.evaluate_negotiable(historia)
        
        self.assertTrue(passed)
        
    def test_evaluate_negotiable_rigida(self):
        """Test criterio Negociable con historia rígida."""
        historia = "Como usuario quiero buscar usando exactamente el algoritmo X en base de datos Y"
        passed, suggestions = self.evaluator.evaluate_negotiable(historia)
        
        self.assertFalse(passed)
        self.assertGreater(len(suggestions), 0)
        
    def test_evaluate_valuable_buena(self):
        """Test criterio Valiosa con historia que aporta valor."""
        historia = "Como usuario quiero exportar reportes para analizar datos de ventas"
        passed, suggestions = self.evaluator.evaluate_valuable(historia)
        
        self.assertTrue(passed)
        
    def test_evaluate_valuable_sin_proposito(self):
        """Test criterio Valiosa sin propósito claro."""
        historia = "Como usuario quiero hacer clic en botones"
        passed, suggestions = self.evaluator.evaluate_valuable(historia)
        
        self.assertFalse(passed)
        self.assertGreater(len(suggestions), 0)
        
    def test_evaluate_estimable_buena(self):
        """Test criterio Estimable con historia clara."""
        historia = "Como usuario quiero crear una cuenta nueva para registrarme en el sistema"
        passed, suggestions = self.evaluator.evaluate_estimable(historia)
        
        self.assertTrue(passed)
        
    def test_evaluate_estimable_vaga(self):
        """Test criterio Estimable con historia vaga."""
        historia = "Como usuario quiero mejor"
        passed, suggestions = self.evaluator.evaluate_estimable(historia)
        
        self.assertFalse(passed)
        self.assertGreater(len(suggestions), 0)
        
    def test_evaluate_small_buena(self):
        """Test criterio Small con historia pequeña."""
        historia = "Como usuario quiero editar mi perfil"
        passed, suggestions = self.evaluator.evaluate_small(historia)
        
        self.assertTrue(passed)
        
    def test_evaluate_small_muy_larga(self):
        """Test criterio Small con historia muy larga."""
        historia = ("Como administrador del sistema quiero gestionar usuarios y permisos "
                   "y configurar roles y validar accesos y generar reportes de auditoría "
                   "y mantener la seguridad del sistema y controlar accesos")
        passed, suggestions = self.evaluator.evaluate_small(historia)
        
        self.assertFalse(passed)
        self.assertGreater(len(suggestions), 0)
        
    def test_evaluate_testable_buena(self):
        """Test criterio Testeable con historia verificable."""
        historia = "Como usuario quiero crear una cuenta para registrarme"
        passed, suggestions = self.evaluator.evaluate_testable(historia)
        
        self.assertTrue(passed)
        
    def test_evaluate_testable_subjetiva(self):
        """Test criterio Testeable con criterios subjetivos."""
        historia = "Como usuario quiero una interfaz más fácil y mejor"
        passed, suggestions = self.evaluator.evaluate_testable(historia)
        
        self.assertFalse(passed)
        self.assertGreater(len(suggestions), 0)
        
    def test_todos_los_criterios_historia_perfecta(self):
        """Test de todos los criterios con historia bien formada."""
        historia = "Como usuario registrado quiero editar mi perfil para mantener mis datos actualizados"
        
        criterios = [
            self.evaluator.evaluate_independent,
            self.evaluator.evaluate_negotiable, 
            self.evaluator.evaluate_valuable,
            self.evaluator.evaluate_estimable,
            self.evaluator.evaluate_small,
            self.evaluator.evaluate_testable
        ]
        
        for criterio_func in criterios:
            passed, suggestions = criterio_func(historia)
            # Al menos debería pasar la mayoría de criterios
            self.assertIsInstance(passed, bool)
            self.assertIsInstance(suggestions, list)


if __name__ == '__main__':
    unittest.main()
