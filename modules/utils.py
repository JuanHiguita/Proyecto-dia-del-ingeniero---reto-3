"""
Módulo de utilidades para la demo técnica de análisis INVEST.
Contiene funciones auxiliares para carga de datos, validaciones y formateo.
"""

import pandas as pd
import re
import json
from typing import Dict, List, Union, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_csv_data(filepath: str) -> pd.DataFrame:
    """
    Carga datos desde archivo CSV con manejo de errores.
    
    Args:
        filepath (str): Ruta al archivo CSV
        
    Returns:
        pd.DataFrame: DataFrame con los datos cargados
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        pd.errors.EmptyDataError: Si el archivo está vacío
    """
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Datos cargados exitosamente desde {filepath}. Filas: {len(df)}")
        return df
    except FileNotFoundError:
        logger.error(f"Archivo no encontrado: {filepath}")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"Archivo vacío: {filepath}")
        raise
    except Exception as e:
        logger.error(f"Error cargando {filepath}: {str(e)}")
        raise

def validate_historia_format(historia: str) -> bool:
    """
    Valida que una historia de usuario tenga el formato básico esperado.
    
    Args:
        historia (str): Texto de la historia de usuario
        
    Returns:
        bool: True si tiene formato válido, False en caso contrario
    """
    if not isinstance(historia, str) or len(historia.strip()) == 0:
        return False
    
    # Verificar que contenga elementos básicos de una HU
    historia_lower = historia.lower().strip()
    
    # Debe contener al menos "como" y "quiero"/"necesito"/"deseo"
    tiene_como = "como" in historia_lower
    tiene_accion = any(word in historia_lower for word in ["quiero", "necesito", "deseo", "quisiera"])
    
    return tiene_como and tiene_accion

def clean_text(texto: str) -> str:
    """
    Limpia y normaliza texto para procesamiento.
    
    Args:
        texto (str): Texto a limpiar
        
    Returns:
        str: Texto limpio y normalizado
    """
    if not isinstance(texto, str):
        return ""
    
    # Eliminar espacios extra y normalizar
    texto = re.sub(r'\s+', ' ', texto.strip())
    
    # Normalizar comillas y caracteres especiales
    texto = texto.replace('"', '"').replace('"', '"')
    texto = texto.replace(''', "'").replace(''', "'")
    
    return texto

def count_words(texto: str) -> int:
    """
    Cuenta palabras en un texto de manera robusta.
    
    Args:
        texto (str): Texto a analizar
        
    Returns:
        int: Número de palabras
    """
    if not isinstance(texto, str):
        return 0
    
    # Limpiar texto y dividir por espacios
    texto_limpio = clean_text(texto)
    if not texto_limpio:
        return 0
    
    palabras = texto_limpio.split()
    return len(palabras)

def extract_user_role(historia: str) -> str:
    """
    Extrae el rol del usuario de una historia.
    
    Args:
        historia (str): Historia de usuario
        
    Returns:
        str: Rol identificado o "usuario" por defecto
    """
    if not validate_historia_format(historia):
        return "usuario"
    
    # Buscar patrón "Como [rol]"
    patron = r"como\s+([^,\s]+(?:\s+[^,\s]+)*?)(?:\s+quiero|\s+necesito|\s+deseo|\s+quisiera)"
    match = re.search(patron, historia.lower())
    
    if match:
        return match.group(1).strip()
    
    return "usuario"

def format_invest_result(invest_dict: Dict) -> str:
    """
    Formatea resultado INVEST para visualización.
    
    Args:
        invest_dict (Dict): Diccionario con resultados INVEST
        
    Returns:
        str: Resultado formateado
    """
    if not isinstance(invest_dict, dict):
        return "❌ Error en formato"
    
    criterios = ["Independiente", "Negociable", "Valiosa", "Estimable", "Small", "Testeable"]
    resultado = []
    
    for criterio in criterios:
        if criterio in invest_dict:
            icono = "✅" if invest_dict[criterio] else "❌"
            resultado.append(f"{icono} {criterio[0]}")
        else:
            resultado.append(f"❓ {criterio[0]}")
    
    return " | ".join(resultado)

def calculate_invest_score(invest_dict: Dict) -> float:
    """
    Calcula puntuación INVEST (0-1).
    
    Args:
        invest_dict (Dict): Diccionario con resultados INVEST
        
    Returns:
        float: Puntuación entre 0 y 1
    """
    if not isinstance(invest_dict, dict):
        return 0.0
    
    criterios = ["Independiente", "Negociable", "Valiosa", "Estimable", "Small", "Testeable"]
    cumplidos = sum(1 for criterio in criterios if invest_dict.get(criterio, False))
    
    return cumplidos / len(criterios)

def export_results_to_csv(results: List[Dict], output_path: str) -> bool:
    """
    Exporta resultados a archivo CSV.
    
    Args:
        results (List[Dict]): Lista de resultados a exportar
        output_path (str): Ruta del archivo de salida
        
    Returns:
        bool: True si la exportación fue exitosa
    """
    try:
        if not results:
            logger.warning("No hay resultados para exportar")
            return False
        
        # Convertir a DataFrame
        df = pd.DataFrame(results)
        
        # Guardar CSV
        df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"Resultados exportados exitosamente a {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error exportando resultados: {str(e)}")
        return False

def validate_csv_structure(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Valida que un DataFrame tenga las columnas requeridas.
    
    Args:
        df (pd.DataFrame): DataFrame a validar
        required_columns (List[str]): Columnas requeridas
        
    Returns:
        bool: True si tiene todas las columnas requeridas
    """
    if df is None or df.empty:
        return False
    
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        logger.error(f"Columnas faltantes: {missing_columns}")
        return False
    
    return True

def safe_json_loads(json_str: str) -> Dict:
    """
    Carga JSON de manera segura con manejo de errores.
    
    Args:
        json_str (str): String JSON a procesar
        
    Returns:
        Dict: Diccionario resultante o vacío si hay error
    """
    try:
        return json.loads(json_str) if isinstance(json_str, str) else {}
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Error procesando JSON: {json_str}")
        return {}

def get_default_invest_structure() -> Dict:
    """
    Retorna estructura por defecto para resultados INVEST.
    
    Returns:
        Dict: Estructura base para resultados INVEST
    """
    return {
        "id": "",
        "INVEST": {
            "Independiente": False,
            "Negociable": False,
            "Valiosa": False,
            "Estimable": False,
            "Small": False,
            "Testeable": False
        },
        "sugerencias": []
    }

if __name__ == "__main__":
    # Pruebas básicas del módulo
    print("🧪 Probando módulo de utilidades...")
    
    # Probar validación de historia
    historia_valida = "Como usuario quiero iniciar sesión para acceder al sistema"
    historia_invalida = "Esto no es una historia válida"
    
    print(f"Historia válida: {validate_historia_format(historia_valida)}")
    print(f"Historia inválida: {validate_historia_format(historia_invalida)}")
    
    # Probar conteo de palabras
    print(f"Palabras en historia: {count_words(historia_valida)}")
    
    # Probar extracción de rol
    print(f"Rol identificado: {extract_user_role(historia_valida)}")
    
    print("✅ Pruebas completadas")


def map_azure_devops_to_internal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mapea la estructura de Azure DevOps a la estructura interna del sistema.
    
    Args:
        df (pd.DataFrame): DataFrame con estructura de Azure DevOps
        
    Returns:
        pd.DataFrame: DataFrame con estructura interna
    """
    try:
        # Verificar que el DataFrame no esté vacío
        if df.empty:
            logger.warning("DataFrame vacío recibido para mapeo")
            return pd.DataFrame(columns=['ID', 'Historia', 'Sprint', 'Prioridad'])
        
        # Log de diagnóstico
        logger.info(f"Mapeando DataFrame con {len(df)} filas y columnas: {df.columns.tolist()}")
        
        # Verificar columnas requeridas con mejor diagnóstico
        required_columns = ['ID', 'Title']
        missing_columns = []
        
        for col in required_columns:
            if col not in df.columns:
                # Buscar columnas similares
                similar_cols = [c for c in df.columns if col.lower() in c.lower() or c.lower() in col.lower()]
                logger.error(f"Columna requerida '{col}' no encontrada. Columnas similares: {similar_cols}")
                missing_columns.append(col)
        
        if missing_columns:
            logger.error(f"Columnas faltantes: {missing_columns}")
            logger.error(f"Columnas disponibles: {df.columns.tolist()}")
            raise ValueError(f"Columnas requeridas faltantes: {missing_columns}")
        
        # Crear mapeo de columnas
        mapped_df = pd.DataFrame()
        
        # Mapear columnas principales
        mapped_df['ID'] = df['ID']
        mapped_df['Historia'] = df['Title']  # Title contiene la historia de usuario
        
        # Extraer Sprint y Prioridad de Tags si existen
        if 'Tags' in df.columns:
            # Separar tags por comas y extraer Sprint y Prioridad
            def extract_sprint_priority(tags_str):
                if pd.isna(tags_str) or tags_str == '':
                    return '', ''
                
                tags = [tag.strip() for tag in str(tags_str).split(',')]
                sprint = ''
                prioridad = ''
                
                for tag in tags:
                    if tag.startswith('Sprint'):
                        sprint = tag.replace('Sprint', '').strip()
                    elif tag in ['Alta', 'Media', 'Baja']:
                        prioridad = tag
                
                return sprint, prioridad
            
            df[['Sprint_temp', 'Prioridad_temp']] = df['Tags'].apply(
                lambda x: pd.Series(extract_sprint_priority(x))
            )
            
            mapped_df['Sprint'] = df['Sprint_temp']
            mapped_df['Prioridad'] = df['Prioridad_temp']
        else:
            mapped_df['Sprint'] = ''
            mapped_df['Prioridad'] = ''
        
        # Para datos históricos, mapear campos adicionales si existen
        if 'Horas' in df.columns:
            mapped_df['Horas'] = df['Horas']
        if 'Criterios_INVEST' in df.columns:
            mapped_df['Criterios_INVEST'] = df['Criterios_INVEST']
        if 'Tokens' in df.columns:
            mapped_df['Tokens'] = df['Tokens']
        if 'Complejidad' in df.columns:
            mapped_df['Complejidad'] = df['Complejidad']
            
        logger.info(f"Mapeo de Azure DevOps completado. Filas: {len(mapped_df)}")
        return mapped_df
        
    except Exception as e:
        logger.error(f"Error mapeando estructura de Azure DevOps: {e}")
        raise


def map_internal_to_azure_devops(df: pd.DataFrame, work_item_type: str = "User Story") -> pd.DataFrame:
    """
    Mapea la estructura interna del sistema a la estructura de Azure DevOps para exportación.
    
    Args:
        df (pd.DataFrame): DataFrame con estructura interna
        work_item_type (str): Tipo de work item para Azure DevOps
        
    Returns:
        pd.DataFrame: DataFrame con estructura de Azure DevOps
    """
    try:
        # Crear mapeo inverso
        azure_df = pd.DataFrame()
        
        # Mapear columnas principales
        azure_df['ID'] = df['ID']
        azure_df['Work Item Type'] = work_item_type
        azure_df['Title'] = df['Historia']
        azure_df['Assigned To'] = ''  # Vacío por defecto
        azure_df['State'] = 'Active'  # Estado por defecto
        
        # Combinar Sprint y Prioridad en Tags
        def create_tags(sprint, prioridad):
            tags = []
            if pd.notna(sprint) and sprint != '':
                tags.append(f"Sprint{sprint}")
            if pd.notna(prioridad) and prioridad != '':
                tags.append(str(prioridad))
            return ','.join(tags)
        
        if 'Sprint' in df.columns and 'Prioridad' in df.columns:
            azure_df['Tags'] = df.apply(lambda row: create_tags(row['Sprint'], row['Prioridad']), axis=1)
        else:
            azure_df['Tags'] = ''
        
        # Agregar campos adicionales si están disponibles (para históricos)
        additional_fields = ['Horas', 'Criterios_INVEST', 'Tokens', 'Complejidad']
        for field in additional_fields:
            if field in df.columns:
                azure_df[field] = df[field]
                
        logger.info(f"Mapeo a Azure DevOps completado. Filas: {len(azure_df)}")
        return azure_df
        
    except Exception as e:
        logger.error(f"Error mapeando a estructura de Azure DevOps: {e}")
        raise


def load_azure_devops_csv(filepath) -> pd.DataFrame:
    """
    Carga un archivo CSV con estructura de Azure DevOps y lo convierte a estructura interna.
    
    Args:
        filepath: Ruta al archivo CSV de Azure DevOps o objeto UploadedFile de Streamlit
        
    Returns:
        pd.DataFrame: DataFrame con estructura interna
    """
    try:
        # Manejar diferentes tipos de entrada
        if hasattr(filepath, 'read'):
            # Es un objeto UploadedFile de Streamlit o similar
            logger.info("Cargando archivo subido desde Streamlit...")
            df_azure = pd.read_csv(filepath)
        else:
            # Es una ruta de archivo string
            logger.info(f"Cargando archivo desde ruta: {filepath}")
            df_azure = load_csv_data(filepath)
        
        logger.info(f"Archivo cargado con {len(df_azure)} filas y columnas: {df_azure.columns.tolist()}")
        
        # Convertir a estructura interna
        df_internal = map_azure_devops_to_internal(df_azure)
        
        return df_internal
        
    except Exception as e:
        logger.error(f"Error cargando archivo de Azure DevOps: {e}")
        raise


def export_to_azure_devops_csv(df: pd.DataFrame, filepath: str, work_item_type: str = "User Story") -> bool:
    """
    Exporta un DataFrame con estructura interna a formato CSV de Azure DevOps.
    
    Args:
        df (pd.DataFrame): DataFrame con estructura interna
        filepath (str): Ruta donde guardar el archivo CSV
        work_item_type (str): Tipo de work item para Azure DevOps
        
    Returns:
        bool: True si la exportación fue exitosa
    """
    try:
        # Convertir a estructura de Azure DevOps
        df_azure = map_internal_to_azure_devops(df, work_item_type)
        
        # Guardar archivo CSV
        df_azure.to_csv(filepath, index=False, quoting=1)  # quoting=1 para comillas en todos los campos
        
        logger.info(f"Exportación a Azure DevOps completada: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error exportando a Azure DevOps: {e}")
        return False
