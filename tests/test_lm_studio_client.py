"""
Tests unitarios para el cliente LM Studio.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

# Agregar path del proyecto
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from clients.lm_studio_client import LMStudioClient


class TestLMStudioClient(unittest.TestCase):
    """Tests para la clase LMStudioClient."""
    
    def setUp(self):
        """Configuración antes de cada test."""
        self.client = LMStudioClient()
        
    def test_init_default_values(self):
        """Test inicialización con valores por defecto."""
        self.assertEqual(self.client.base_url, "http://127.0.0.1:1234")
        self.assertEqual(self.client.model_name, "openai/gpt-oss-20b")
        self.assertFalse(self.client.is_connected)
        self.assertEqual(self.client.available_models, [])
        
    def test_init_custom_values(self):
        """Test inicialización con valores personalizados."""
        client = LMStudioClient(base_url="http://localhost:8080", model_name="custom-model")
        self.assertEqual(client.base_url, "http://localhost:8080")
        self.assertEqual(client.model_name, "custom-model")
        
    @patch('clients.lm_studio_client.requests.get')
    def test_connect_success(self, mock_get):
        """Test conexión exitosa."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "openai/gpt-oss-20b"},
                {"id": "other-model"}
            ]
        }
        mock_get.return_value = mock_response
        
        result = self.client.connect()
        
        self.assertTrue(result)
        self.assertTrue(self.client.is_connected)
        self.assertIn("openai/gpt-oss-20b", self.client.available_models)
        
    @patch('clients.lm_studio_client.requests.get')
    def test_connect_model_not_found(self, mock_get):
        """Test conexión con modelo no disponible."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "other-model"}]
        }
        mock_get.return_value = mock_response
        
        result = self.client.connect()
        
        self.assertFalse(result)
        self.assertFalse(self.client.is_connected)
        
    @patch('clients.lm_studio_client.requests.get')
    def test_connect_connection_error(self, mock_get):
        """Test error de conexión."""
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        result = self.client.connect()
        
        self.assertFalse(result)
        self.assertFalse(self.client.is_connected)
        
    @patch('clients.lm_studio_client.requests.post')
    def test_generate_text_success(self, mock_post):
        """Test generación de texto exitosa."""
        self.client.is_connected = True
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "Texto generado"}}
            ]
        }
        mock_post.return_value = mock_response
        
        result = self.client.generate_text("Test prompt")
        
        self.assertEqual(result, "Texto generado")
        
    def test_generate_text_not_connected(self):
        """Test generación de texto sin conexión."""
        self.client.is_connected = False
        
        result = self.client.generate_text("Test prompt")
        
        self.assertIsNone(result)
        
    @patch('clients.lm_studio_client.requests.post')
    def test_generate_text_error(self, mock_post):
        """Test error en generación de texto."""
        self.client.is_connected = True
        mock_post.side_effect = Exception("Error de red")
        
        result = self.client.generate_text("Test prompt")
        
        self.assertIsNone(result)
        
    @patch.object(LMStudioClient, 'generate_text')
    def test_evaluate_invest_story_success(self, mock_generate):
        """Test evaluación INVEST exitosa."""
        mock_generate.return_value = '''
        {
          "Independiente": true,
          "Negociable": false,
          "Valiosa": true,
          "Estimable": true,
          "Small": true,
          "Testeable": true,
          "sugerencias": ["Mejorar negociabilidad"]
        }
        '''
        
        result = self.client.evaluate_invest_story("Historia de prueba")
        
        self.assertIsNotNone(result)
        self.assertTrue(result["Independiente"])
        self.assertFalse(result["Negociable"])
        self.assertEqual(len(result["sugerencias"]), 1)
        
    @patch.object(LMStudioClient, 'generate_text')
    def test_evaluate_invest_story_invalid_json(self, mock_generate):
        """Test evaluación con JSON inválido."""
        mock_generate.return_value = "Respuesta no JSON"
        
        result = self.client.evaluate_invest_story("Historia de prueba")
        
        self.assertIsNone(result)
        
    @patch.object(LMStudioClient, 'generate_text')
    def test_evaluate_invest_story_no_response(self, mock_generate):
        """Test evaluación sin respuesta."""
        mock_generate.return_value = None
        
        result = self.client.evaluate_invest_story("Historia de prueba")
        
        self.assertIsNone(result)
        
    def test_is_available(self):
        """Test verificación de disponibilidad."""
        self.client.is_connected = False
        self.assertFalse(self.client.is_available())
        
        self.client.is_connected = True
        self.assertTrue(self.client.is_available())
        
    def test_get_available_models(self):
        """Test obtener modelos disponibles."""
        self.client.available_models = ["model1", "model2"]
        models = self.client.get_available_models()
        
        self.assertEqual(models, ["model1", "model2"])
        # Verificar que es una copia
        models.append("model3")
        self.assertEqual(len(self.client.available_models), 2)


if __name__ == '__main__':
    unittest.main()
