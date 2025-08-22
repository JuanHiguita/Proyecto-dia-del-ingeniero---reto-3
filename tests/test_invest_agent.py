"""
Tests unitarios para el módulo InvestAgent.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Agregar path del proyecto
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "modules"))

from modules.invest_agent import InvestAgent
from modules.invest_result import InvestResult


class TestInvestAgent(unittest.TestCase):
    """Tests para la clase InvestAgent."""
    
    def setUp(self):
        """Configuración antes de cada test."""
        self.historia_valida = "Como usuario quiero hacer login para acceder al sistema"
        self.historia_invalida = "Historia incompleta"
        
    def test_init_modo_reglas(self):
        """Test inicialización en modo reglas."""
        agent = InvestAgent(modo="reglas")
        self.assertEqual(agent.get_mode(), "reglas")
        self.assertFalse(agent.is_lm_studio_available())
        
    @patch('invest_agent.LMStudioClient')
    def test_init_modo_gptoss_sin_conexion(self, mock_client_class):
        """Test inicialización modo gptoss sin conexión LM Studio."""
        mock_client = Mock()
        mock_client.connect.return_value = False
        mock_client_class.return_value = mock_client
        
        agent = InvestAgent(modo="gptoss")
        self.assertEqual(agent.get_mode(), "reglas")  # Fallback
        self.assertFalse(agent.is_lm_studio_available())
        
    @patch('invest_agent.LMStudioClient')
    def test_init_modo_gptoss_con_conexion(self, mock_client_class):
        """Test inicialización modo gptoss con conexión exitosa."""
        mock_client = Mock()
        mock_client.connect.return_value = True
        mock_client.is_available.return_value = True
        mock_client_class.return_value = mock_client
        
        agent = InvestAgent(modo="gptoss")
        self.assertEqual(agent.get_mode(), "gptoss")
        self.assertTrue(agent.is_lm_studio_available())
        
    def test_evaluate_story_reglas(self):
        """Test evaluación de historia usando reglas."""
        agent = InvestAgent(modo="reglas")
        resultado = agent.evaluate_story(self.historia_valida, "TEST_001")
        
        self.assertIsInstance(resultado, InvestResult)
        self.assertEqual(resultado.id, "TEST_001")
        self.assertEqual(resultado.historia, self.historia_valida)
        self.assertEqual(resultado.modo_evaluacion, "reglas")
        self.assertIn("Independiente", resultado.invest_scores)
        self.assertIn("Negociable", resultado.invest_scores)
        self.assertIn("Valiosa", resultado.invest_scores)
        self.assertIn("Estimable", resultado.invest_scores)
        self.assertIn("Small", resultado.invest_scores)
        self.assertIn("Testeable", resultado.invest_scores)
        
    def test_evaluate_story_id_auto(self):
        """Test evaluación con ID automático."""
        agent = InvestAgent(modo="reglas")
        resultado = agent.evaluate_story(self.historia_valida)
        
        self.assertTrue(resultado.id.startswith("STORY_"))
        self.assertEqual(len(resultado.id), 10)  # STORY_xxxx
        
    @patch('invest_agent.validate_historia_format')
    def test_evaluate_story_formato_invalido(self, mock_validate):
        """Test evaluación de historia con formato inválido."""
        mock_validate.return_value = False
        
        agent = InvestAgent(modo="reglas")
        resultado = agent.evaluate_story("Historia inválida", "INVALID")
        
        self.assertEqual(resultado.id, "INVALID")
        self.assertEqual(resultado.modo_evaluacion, "reglas")
        self.assertEqual(list(resultado.invest_scores.values()), [False] * 6)
        self.assertIn("Formato de historia de usuario inválido", resultado.sugerencias)
        
    def test_evaluate_stories_batch(self):
        """Test evaluación de múltiples historias."""
        agent = InvestAgent(modo="reglas")
        historias = [
            "Como usuario quiero hacer login para acceder",
            "Como admin quiero gestionar usuarios para mantener seguridad"
        ]
        
        resultados = agent.evaluate_stories_batch(historias)
        
        self.assertEqual(len(resultados), 2)
        self.assertEqual(resultados[0].id, "BATCH_001")
        self.assertEqual(resultados[1].id, "BATCH_002")
        
    def test_get_evaluation_summary_vacio(self):
        """Test resumen de evaluaciones sin resultados."""
        agent = InvestAgent(modo="reglas")
        resumen = agent.get_evaluation_summary([])
        
        self.assertIn("error", resumen)
        self.assertEqual(resumen["error"], "No hay resultados para analizar")
        
    def test_get_evaluation_summary(self):
        """Test resumen de evaluaciones con datos."""
        agent = InvestAgent(modo="reglas")
        
        # Crear resultado mock
        resultado1 = InvestResult(
            id="TEST_1",
            historia="Historia 1",
            invest_scores={"Independiente": True, "Negociable": True, "Valiosa": False,
                          "Estimable": True, "Small": True, "Testeable": False},
            sugerencias=[],
            modo_evaluacion="reglas"
        )
        
        resultado2 = InvestResult(
            id="TEST_2", 
            historia="Historia 2",
            invest_scores={"Independiente": True, "Negociable": True, "Valiosa": True,
                          "Estimable": True, "Small": True, "Testeable": True},
            sugerencias=[],
            modo_evaluacion="reglas"
        )
        
        resumen = agent.get_evaluation_summary([resultado1, resultado2])
        
        self.assertEqual(resumen["total_historias"], 2)
        self.assertEqual(resumen["completamente_invest"], 1)
        self.assertEqual(resumen["porcentaje_completas"], 50.0)
        self.assertEqual(resumen["criterios_porcentaje"]["Independiente"], 100.0)
        self.assertEqual(resumen["criterios_porcentaje"]["Valiosa"], 50.0)
        self.assertEqual(resumen["modo_evaluacion"], "reglas")


if __name__ == '__main__':
    unittest.main()
