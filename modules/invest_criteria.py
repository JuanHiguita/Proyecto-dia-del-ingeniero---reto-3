"""
Evaluadores individuales para cada criterio INVEST.
"""

import re
from typing import List, Tuple
from modules.utils import count_words, clean_text


class InvestCriteriaEvaluator:
    """Evaluador de criterios INVEST individuales."""
    
    @staticmethod
    def evaluate_independent(historia: str) -> Tuple[bool, List[str]]:
        """
        Evalúa criterio Independiente.
        
        Args:
            historia: Historia de usuario a evaluar
            
        Returns:
            tuple: (bool evaluación, List[str] sugerencias)
        """
        sugerencias = []
        
        # Patrones que indican dependencias
        dependency_patterns = [
            r'\bdepende\b', r'\brequiere\b', r'\bnecesita\b',
            r'\bantes de\b', r'\bdespués de\b', r'\bjunto con\b',
            r'\buna vez que\b', r'\bcuando.*esté\b'
        ]
        
        historia_lower = historia.lower()
        
        # Buscar indicadores de dependencia
        has_dependencies = any(re.search(pattern, historia_lower) for pattern in dependency_patterns)
        
        if has_dependencies:
            sugerencias.append("Revisar dependencias explícitas con otras historias")
        
        # Verificar si menciona otros componentes/historias
        component_patterns = [
            r'\bel sistema ya debe\b', r'\bel usuario debe tener\b',
            r'\bsi existe\b', r'\bsi está configurado\b'
        ]
        
        mentions_other_components = any(re.search(pattern, historia_lower) for pattern in component_patterns)
        
        if mentions_other_components:
            sugerencias.append("Considerar dividir en historias más independientes")
        
        # Evaluar independencia
        is_independent = not (has_dependencies or mentions_other_components)
        
        if not is_independent and not sugerencias:
            sugerencias.append("Redefinir la historia para que sea más independiente")
        
        return is_independent, sugerencias
    
    @staticmethod
    def evaluate_negotiable(historia: str) -> Tuple[bool, List[str]]:
        """
        Evalúa criterio Negociable.
        
        Args:
            historia: Historia de usuario a evaluar
            
        Returns:
            tuple: (bool evaluación, List[str] sugerencias)
        """
        sugerencias = []
        
        # Patrones que indican poca flexibilidad
        rigid_patterns = [
            r'\bdebe ser exactamente\b', r'\bsolo puede\b', r'\búnicamente\b',
            r'\bexactamente como\b', r'\bsin excepción\b', r'\bobligatoriamente\b'
        ]
        
        historia_lower = historia.lower()
        
        # Buscar indicadores de rigidez
        is_rigid = any(re.search(pattern, historia_lower) for pattern in rigid_patterns)
        
        # Verificar si incluye detalles de implementación
        implementation_patterns = [
            r'\bbase de datos\b', r'\bAPI\b', r'\balgorithm\b', r'\bSQL\b',
            r'\bframework\b', r'\btecnología\b', r'\blibrería\b'
        ]
        
        has_implementation_details = any(re.search(pattern, historia_lower) for pattern in implementation_patterns)
        
        if is_rigid:
            sugerencias.append("Hacer la historia más flexible en términos de implementación")
        
        if has_implementation_details:
            sugerencias.append("Evitar especificar detalles técnicos de implementación")
        
        # Verificar longitud excesiva que podría indicar rigidez
        if count_words(historia) > 30:
            sugerencias.append("Considerar simplificar para permitir más flexibilidad")
        
        # Evaluar negociabilidad
        is_negotiable = not (is_rigid or has_implementation_details)
        
        if not is_negotiable and not sugerencias:
            sugerencias.append("Reformular para permitir diferentes enfoques de solución")
        
        return is_negotiable, sugerencias
    
    @staticmethod
    def evaluate_valuable(historia: str) -> Tuple[bool, List[str]]:
        """
        Evalúa criterio Valiosa.
        
        Args:
            historia: Historia de usuario a evaluar
            
        Returns:
            tuple: (bool evaluación, List[str] sugerencias)
        """
        sugerencias = []
        
        # Patrones que indican valor
        value_patterns = [
            r'\bpara que\b', r'\bcon el fin de\b', r'\bpara poder\b',
            r'\bpermitirme\b', r'\bayudarme\b', r'\bmejorar\b',
            r'\bpara\s+\w+'  # Incluir "para" seguido de cualquier palabra
        ]
        
        historia_lower = historia.lower()
        
        # Verificar presencia de justificación de valor
        has_value_justification = any(re.search(pattern, historia_lower) for pattern in value_patterns)
        
        # Verificar formato básico de historia de usuario
        user_story_pattern = r'\bcomo\s+.*\s+quiero\s+.*\s+(para|con el fin de)'
        has_proper_format = bool(re.search(user_story_pattern, historia_lower))
        
        # Patrones que indican falta de valor claro
        no_value_patterns = [
            r'\bsolo por\b', r'\bsin razón\b', r'\bporque sí\b',
            r'\bpor completar\b'
        ]
        
        has_no_value_indicators = any(re.search(pattern, historia_lower) for pattern in no_value_patterns)
        
        if not has_value_justification:
            sugerencias.append("Incluir el beneficio o valor que aporta al usuario")
        
        if not has_proper_format:
            sugerencias.append("Usar formato: 'Como [rol] quiero [funcionalidad] para [beneficio]'")
        
        if has_no_value_indicators:
            sugerencias.append("Definir claramente el valor de negocio de esta funcionalidad")
        
        # Verificar si es muy técnica y pierde foco en valor de usuario
        technical_patterns = [
            r'\bconfigurar servidor\b', r'\boptimizar base de datos\b',
            r'\brefactorizar\b', r'\bmantener código\b'
        ]
        
        is_too_technical = any(re.search(pattern, historia_lower) for pattern in technical_patterns)
        
        if is_too_technical:
            sugerencias.append("Enfocar en el valor del usuario final, no en tareas técnicas")
        
        # Evaluar valor
        is_valuable = has_value_justification and not (has_no_value_indicators or is_too_technical)
        
        if not is_valuable and not sugerencias:
            sugerencias.append("Clarificar el valor que esta historia aporta al usuario o negocio")
        
        return is_valuable, sugerencias
    
    @staticmethod
    def evaluate_estimable(historia: str) -> Tuple[bool, List[str]]:
        """
        Evalúa criterio Estimable.
        
        Args:
            historia: Historia de usuario a evaluar
            
        Returns:
            tuple: (bool evaluación, List[str] sugerencias)
        """
        sugerencias = []
        
        # Patrones que dificultan estimación
        vague_patterns = [
            r'\bmejor\b', r'\boptimizar\b', r'\bmás eficiente\b',
            r'\badecuado\b', r'\bapropiado\b', r'\bfácil de usar\b'
        ]
        
        historia_lower = historia.lower()
        
        # Verificar términos vagos
        has_vague_terms = any(re.search(pattern, historia_lower) for pattern in vague_patterns)
        
        if has_vague_terms:
            sugerencias.append("Definir criterios específicos y medibles")
        
        # Verificar longitud - muy corta puede indicar falta de detalle
        word_count = count_words(historia)
        if word_count < 8:
            sugerencias.append("Agregar más detalles para facilitar la estimación")
        
        # Verificar si incluye criterios de aceptación implícitos
        acceptance_patterns = [
            r'\bdebe\b', r'\btiene que\b', r'\bes necesario\b',
            r'\bpermite\b', r'\bmuestra\b', r'\bvalida\b'
        ]
        
        has_acceptance_hints = any(re.search(pattern, historia_lower) for pattern in acceptance_patterns)
        
        if not has_acceptance_hints and word_count > 5:
            sugerencias.append("Incluir criterios de aceptación claros")
        
        # Patrones que indican complejidad desconocida
        unknown_complexity_patterns = [
            r'\bintegración\b', r'\bmigracion\b', r'\bcompatibilidad\b',
            r'\brendimiento\b', r'\bescalabilidad\b'
        ]
        
        has_unknown_complexity = any(re.search(pattern, historia_lower) for pattern in unknown_complexity_patterns)
        
        if has_unknown_complexity:
            sugerencias.append("Investigar y especificar los requisitos técnicos")
        
        # Evaluar estimabilidad
        is_estimable = not (has_vague_terms or has_unknown_complexity) and word_count >= 8
        
        if not is_estimable and not sugerencias:
            sugerencias.append("Agregar más contexto para permitir estimación precisa")
        
        return is_estimable, sugerencias
    
    @staticmethod
    def evaluate_small(historia: str) -> Tuple[bool, List[str]]:
        """
        Evalúa criterio Small.
        
        Args:
            historia: Historia de usuario a evaluar
            
        Returns:
            tuple: (bool evaluación, List[str] sugerencias)
        """
        sugerencias = []
        
        # Contar palabras
        word_count = count_words(historia)
        
        # Considerar demasiado larga si tiene más de 25 palabras
        if word_count > 25:
            sugerencias.append("Considerar dividir en historias más pequeñas")
        
        # Patrones que indican múltiples funcionalidades
        multiple_action_patterns = [
            r'\by\s+(?:también|además)\b', r'\btambién\b', r'\badicionalmente\b',
            r'\by\s+poder\b', r'\by\s+además\b', r'\by\s+después\b'
        ]
        
        historia_lower = historia.lower()
        has_multiple_actions = any(re.search(pattern, historia_lower) for pattern in multiple_action_patterns)
        
        if has_multiple_actions:
            sugerencias.append("Separar en múltiples historias independientes")
        
        # Verificar si incluye múltiples verbos de acción
        action_verbs = ['crear', 'editar', 'eliminar', 'ver', 'buscar', 'filtrar', 'exportar', 'importar']
        found_verbs = [verb for verb in action_verbs if verb in historia_lower]
        
        if len(found_verbs) > 1:
            sugerencias.append("Enfocarse en una sola acción principal por historia")
        
        # Patrones que indican complejidad alta
        complex_patterns = [
            r'\bgestionar\b', r'\badministrar\b', r'\bprocesar\b',
            r'\bintegrar\b', r'\bsincronizar\b', r'\bmigrar\b'
        ]
        
        has_complex_actions = any(re.search(pattern, historia_lower) for pattern in complex_patterns)
        
        if has_complex_actions:
            sugerencias.append("Desglosar las acciones complejas en pasos más simples")
        
        # Evaluar tamaño
        is_small = word_count <= 25 and not has_multiple_actions and len(found_verbs) <= 1
        
        if not is_small and not sugerencias:
            sugerencias.append("Simplificar y enfocar en una funcionalidad específica")
        
        return is_small, sugerencias
    
    @staticmethod
    def evaluate_testable(historia: str) -> Tuple[bool, List[str]]:
        """
        Evalúa criterio Testeable.
        
        Args:
            historia: Historia de usuario a evaluar
            
        Returns:
            tuple: (bool evaluación, List[str] sugerencias)
        """
        sugerencias = []
        
        # Patrones que dificultan testing
        untestable_patterns = [
            r'\bmejor\b', r'\bmás fácil\b', r'\bmás rápido\b',
            r'\bintuitivo\b', r'\bamigable\b', r'\belegal\b'
        ]
        
        historia_lower = historia.lower()
        
        # Verificar términos no testables
        has_untestable_terms = any(re.search(pattern, historia_lower) for pattern in untestable_patterns)
        
        if has_untestable_terms:
            sugerencias.append("Reemplazar términos subjetivos con criterios medibles")
        
        # Verificar si incluye acciones verificables
        verifiable_patterns = [
            r'\bver\b', r'\bcrear\b', r'\beditar\b', r'\beliminar\b',
            r'\brecibir\b', r'\benviar\b', r'\bguardar\b', r'\bcargar\b'
        ]
        
        has_verifiable_actions = any(re.search(pattern, historia_lower) for pattern in verifiable_patterns)
        
        if not has_verifiable_actions:
            sugerencias.append("Incluir acciones específicas que se puedan verificar")
        
        # Verificar si es demasiado vaga para testing
        word_count = count_words(historia)
        if word_count < 6:
            sugerencias.append("Agregar más detalles para definir criterios de prueba")
        
        # Patrones que facilitan testing
        testable_patterns = [
            r'\bmostrar\b', r'\bvalidar\b', r'\bpermitir\b',
            r'\bredireccionar\b', r'\bnotificar\b', r'\bconfirmar\b'
        ]
        
        has_testable_elements = any(re.search(pattern, historia_lower) for pattern in testable_patterns)
        
        # Evaluar testabilidad
        is_testable = (has_verifiable_actions or has_testable_elements) and not has_untestable_terms and word_count >= 6
        
        if not is_testable and not sugerencias:
            sugerencias.append("Definir resultados específicos que se puedan probar")
        
        return is_testable, sugerencias
