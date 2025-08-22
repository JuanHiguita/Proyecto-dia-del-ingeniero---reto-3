"""
Cliente para comunicación con LM Studio API.
"""

import json
import logging
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LMStudioClient:
    """Cliente para interactuar con LM Studio API."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:1234", model_name: str = "openai/gpt-oss-20b"):
        """
        Inicializa cliente LM Studio.
        
        Args:
            base_url: URL base del servidor LM Studio
            model_name: Nombre del modelo a usar
        """
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.is_connected = False
        self.available_models = []
        
    def connect(self) -> bool:
        """
        Conecta con LM Studio y verifica disponibilidad del modelo.
        
        Returns:
            bool: True si conexión exitosa, False en caso contrario
        """
        try:
            logger.info("Intentando conectar con LM Studio...")
            
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                self.available_models = [m.get('id', '') for m in models_data.get('data', [])]
                logger.info(f"✅ LM Studio conectado. Modelos: {self.available_models}")
                
                # Verificar que nuestro modelo está disponible
                if any(self.model_name in model for model in self.available_models):
                    self.is_connected = True
                    logger.info(f"🎯 Modelo {self.model_name} disponible")
                    return True
                else:
                    logger.warning(f"⚠️ Modelo {self.model_name} no encontrado")
                    return False
            else:
                raise Exception(f"Error de conexión: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            logger.warning("⚠️ LM Studio no está corriendo")
            return False
        except Exception as e:
            logger.warning(f"⚠️ Error conectando con LM Studio: {str(e)}")
            return False
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """
        Genera texto usando LM Studio API.
        
        Args:
            prompt: Texto de entrada
            max_tokens: Máximo número de tokens
            temperature: Temperatura para generación
            
        Returns:
            str: Texto generado o None si error
        """
        if not self.is_connected:
            logger.error("Cliente no conectado a LM Studio")
            return None
            
        try:
            logger.info("🚀 Evaluando con LM Studio...")
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                logger.info("📝 Respuesta recibida de LM Studio")
                return content
            else:
                logger.error(f"Error en respuesta LM Studio: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error generando texto: {str(e)}")
            return None
    
    def evaluate_invest_story(self, historia: str) -> Optional[Dict]:
        """
        Evalúa historia usando LM Studio con prompt específico para INVEST.
        
        Args:
            historia: Historia de usuario a evaluar
            
        Returns:
            dict: Resultado de evaluación o None si error
        """
        prompt = f"""Eres un Product Owner pragmático evaluando esta historia de usuario. Usa criterios INVEST pero con mentalidad práctica de equipo ágil:

                    Historia: "{historia}"

                    **Evalúa con criterio práctico:**

                    **Independiente**: ¿Se puede trabajar sin depender críticamente de otras historias específicas?
                    (Acepta dependencias de infraestructura común como autenticación, base de datos, etc.)

                    **Negociable**: ¿El equipo puede conversar sobre el alcance durante el desarrollo?
                    (Si tiene formato "Como X quiero Y para Z", generalmente es negociable)

                    **Valiosa**: ¿Resuelve un problema real del usuario o aporta valor al negocio?
                    (Si es funcionalidad que usuarios realmente usarían)

                    **Estimable**: ¿El equipo de desarrollo puede entender qué construir y estimar esfuerzo?
                    (No necesita ser perfecta, solo suficiente claridad para developers)

                    **Small**: ¿Se puede completar en 1-2 semanas por el equipo?
                    (Si no es una épica gigante con múltiples flujos complejos)

                    **Testeable**: ¿Se puede verificar que funciona correctamente?
                    (Si puedes definir criterios básicos de "terminado")

                    **Guías prácticas:**
                    - Historias con formato correcto "Como X quiero Y para Z" ya cumplen varios criterios
                    - Solo marca FALSE si hay problemas evidentes que bloquearían el desarrollo
                    - Prioriza valor funcional sobre perfección académica
                    - Equipos ágiles pueden refinar historias durante el sprint

                    Responde SOLO con JSON válido:
                    {{
                    "Independiente": true/false,
                    "Negociable": true/false,
                    "Valiosa": true/false,
                    "Estimable": true/false,
                    "Small": true/false,
                    "Testeable": true/false,
                    "sugerencias": ["sugerencia práctica 1", "sugerencia práctica 2"]
                    }}

                    Sugerencias solo para criterios FALSE, y deben ser específicas y ejecutables."""

        response_text = self.generate_text(prompt, max_tokens=500, temperature=0.3)
        
        if response_text:
            try:
                # Limpiar respuesta y extraer JSON
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    return json.loads(json_str)
                else:
                    logger.error("No se encontró JSON válido en la respuesta")
                    return None
                    
            except json.JSONDecodeError as e:
                logger.error(f"Error parseando JSON de LM Studio: {str(e)}")
                return None
        
        return None
    
    def estimate_development_time(self, historia: str, invest_scores: Dict = None) -> Optional[float]:
        """
        Estima tiempo de desarrollo usando LM Studio con prompt específico para estimación.
        
        Args:
            historia: Historia de usuario a evaluar
            invest_scores: Scores INVEST opcionales para contexto adicional
            
        Returns:
            float: Tiempo estimado en horas o None si error
        """
        # Construir contexto adicional si hay scores INVEST
        contexto_invest = ""
        if invest_scores:
            criterios_cumplidos = sum(1 for v in invest_scores.values() if v)
            contexto_invest = f"""
            Contexto INVEST (criterios cumplidos: {criterios_cumplidos}/6):
            - Independiente: {'✓' if invest_scores.get('Independiente', False) else '✗'}
            - Negociable: {'✓' if invest_scores.get('Negociable', False) else '✗'}
            - Valiosa: {'✓' if invest_scores.get('Valiosa', False) else '✗'}
            - Estimable: {'✓' if invest_scores.get('Estimable', False) else '✗'}
            - Small: {'✓' if invest_scores.get('Small', False) else '✗'}
            - Testeable: {'✓' if invest_scores.get('Testeable', False) else '✗'}
            """

        prompt = f"""Como un experto en estimación de desarrollo de software con más de 10 años de experiencia, necesitas estimar el tiempo de desarrollo para esta historia de usuario.

                Historia de usuario: "{historia}"
                {contexto_invest}

                Considera los siguientes factores para tu estimación:
                1. Complejidad técnica de la implementación
                2. Cantidad de componentes involucrados (frontend, backend, base de datos)
                3. Necesidad de investigación o aprendizaje
                4. Testing y validación requeridos
                5. Integración con sistemas existentes
                6. Calidad de los criterios INVEST (historias mejor definidas = estimación más precisa)

                Factores de tiempo típicos:
                - Historia simple (formulario básico, CRUD simple): 4-8 horas
                - Historia media (lógica de negocio, validaciones, integraciones simples): 8-16 horas
                - Historia compleja (algoritmos complejos, múltiples integraciones, UI avanzada): 16-32 horas
                - Historia muy compleja (nueva arquitectura, investigación, múltiples sistemas): 32+ horas

                IMPORTANTE: Responde SOLO con un número decimal que represente las horas estimadas. 
                No incluyas texto adicional, explicaciones o rangos. Solo el número.

                Ejemplo de respuesta correcta: 12.5
                Ejemplo de respuesta incorrecta: "Entre 10 y 15 horas" o "12.5 horas"

                Tiempo estimado en horas:"""

        response_text = self.generate_text(prompt, max_tokens=50, temperature=0.3)
        
        if response_text:
            try:
                # Extraer número de la respuesta
                import re
                # Buscar número decimal en la respuesta
                match = re.search(r'\d+\.?\d*', response_text.strip())
                if match:
                    tiempo_estimado = float(match.group())
                    # Validar rango razonable (1-100 horas)
                    if 1.0 <= tiempo_estimado <= 100.0:
                        logger.info(f"⏱️ Tiempo estimado por LLM: {tiempo_estimado} horas")
                        return tiempo_estimado
                    else:
                        logger.warning(f"Tiempo estimado fuera de rango: {tiempo_estimado}")
                        return None
                else:
                    logger.error("No se encontró número válido en la respuesta del LLM")
                    return None
                    
            except (ValueError, TypeError) as e:
                logger.error(f"Error parseando tiempo estimado: {str(e)}")
                return None
        
        return None
    
    def is_available(self) -> bool:
        """Verifica si el cliente está conectado y disponible."""
        return self.is_connected
    
    def get_available_models(self) -> List[str]:
        """Retorna lista de modelos disponibles."""
        return self.available_models.copy()
