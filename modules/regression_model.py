"""
Módulo de regresión para estimación de tiempos de desarrollo.
Entrena modelo con datos históricos y predice tiempo para nuevas historias.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from typing import Dict, Tuple, Optional
from utils import load_csv_data, count_words, validate_csv_structure, load_azure_devops_csv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimeEstimationModel:
    """
    Modelo de regresión para estimación de tiempos de desarrollo.
    """
    
    def __init__(self):
        """Inicializa el modelo de estimación."""
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = ['longitud_tokens', 'criterios_invest', 'complejidad_encoded']
        self.model_metrics = {}
    
    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extrae características para el modelo de regresión.
        
        Args:
            df (pd.DataFrame): DataFrame con datos históricos
            
        Returns:
            pd.DataFrame: DataFrame con características extraídas
        """
        features_df = pd.DataFrame()
        
        # Feature 1: Longitud en tokens/palabras
        if 'Tokens' in df.columns:
            features_df['longitud_tokens'] = df['Tokens']
        else:
            # Calcular desde el texto de la historia
            features_df['longitud_tokens'] = df['Historia'].apply(count_words)
        
        # Feature 2: Criterios INVEST cumplidos
        features_df['criterios_invest'] = df['Criterios_INVEST']
        
        # Feature 3: Complejidad (si está disponible)
        if 'Complejidad' in df.columns:
            # Codificar complejidad: Baja=1, Media=2, Alta=3
            complejidad_map = {'Baja': 1, 'Media': 2, 'Alta': 3}
            features_df['complejidad_encoded'] = df['Complejidad'].map(complejidad_map).fillna(2)
        else:
            # Estimar complejidad basada en longitud y criterios
            features_df['complejidad_encoded'] = self._estimate_complexity(
                features_df['longitud_tokens'], 
                features_df['criterios_invest']
            )
        
        return features_df
    
    def _estimate_complexity(self, tokens: pd.Series, criterios: pd.Series) -> pd.Series:
        """
        Estima complejidad basada en tokens y criterios INVEST.
        
        Args:
            tokens (pd.Series): Número de tokens
            criterios (pd.Series): Criterios INVEST cumplidos
            
        Returns:
            pd.Series: Complejidad estimada (1-3)
        """
        # Lógica simple para estimar complejidad
        complexity = np.ones(len(tokens))
        
        # Basado en longitud
        complexity[tokens > 12] = 2  # Media
        complexity[tokens > 15] = 3  # Alta
        
        # Ajustar por criterios INVEST (más criterios = potencialmente más complejo)
        complexity[criterios >= 5] += 0.5
        complexity[criterios <= 3] -= 0.5
        
        # Normalizar a 1-3
        complexity = np.clip(np.round(complexity), 1, 3)
        
        return pd.Series(complexity)
    
    def train_model(self, historicos_path: str) -> Dict:
        """
        Entrena el modelo con datos históricos.
        
        Args:
            historicos_path (str): Ruta al archivo CSV con datos históricos
            
        Returns:
            Dict: Métricas del modelo entrenado
        """
        try:
            # Cargar datos históricos usando formato Azure DevOps
            df_historicos = load_azure_devops_csv(historicos_path)
            
            # Validar estructura requerida (ahora con estructura interna)
            required_columns = ['Historia', 'Horas', 'Criterios_INVEST']
            if not validate_csv_structure(df_historicos, required_columns):
                raise ValueError(f"Archivo debe contener columnas: {required_columns}")
            
            # Extraer características
            X = self._extract_features(df_historicos)
            y = df_historicos['Horas']
            
            logger.info(f"Entrenando modelo con {len(X)} ejemplos")
            logger.info(f"Características: {list(X.columns)}")
            
            # Dividir datos
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Escalar características
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Entrenar modelo
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluar modelo
            y_pred_train = self.model.predict(X_train_scaled)
            y_pred_test = self.model.predict(X_test_scaled)
            
            # Calcular métricas
            train_mae = mean_absolute_error(y_train, y_pred_train)
            test_mae = mean_absolute_error(y_test, y_pred_test)
            train_r2 = r2_score(y_train, y_pred_train)
            test_r2 = r2_score(y_test, y_pred_test)
            
            self.model_metrics = {
                'train_mae': round(train_mae, 2),
                'test_mae': round(test_mae, 2),
                'train_r2': round(train_r2, 3),
                'test_r2': round(test_r2, 3),
                'feature_importance': dict(zip(
                    self.feature_names, 
                    self.model.coef_.round(3)
                )),
                'intercept': round(self.model.intercept_, 2),
                'training_samples': len(X_train)
            }
            
            self.is_trained = True
            
            logger.info("✅ Modelo entrenado exitosamente")
            logger.info(f"📊 MAE Test: {test_mae:.2f} horas")
            logger.info(f"📊 R² Test: {test_r2:.3f}")
            
            return self.model_metrics
            
        except Exception as e:
            logger.error(f"Error entrenando modelo: {str(e)}")
            raise
    
    def predict_tiempo(self, historia: str, invest_json: Dict) -> float:
        """
        Predice tiempo de desarrollo para una historia.
        
        Args:
            historia (str): Texto de la historia de usuario
            invest_json (Dict): Resultado de evaluación INVEST
            
        Returns:
            float: Tiempo estimado en horas
        """
        if not self.is_trained:
            logger.warning("Modelo no entrenado, usando estimación heurística")
            return self._heuristic_estimation(historia, invest_json)
        
        try:
            # Extraer características de la historia
            longitud_tokens = count_words(historia)
            
            # Contar criterios INVEST cumplidos
            invest_scores = invest_json.get('INVEST', {})
            criterios_cumplidos = sum(1 for v in invest_scores.values() if v)
            
            # Estimar complejidad
            if longitud_tokens <= 10:
                complejidad = 1  # Baja
            elif longitud_tokens <= 15:
                complejidad = 2  # Media
            else:
                complejidad = 3  # Alta
            
            # Crear array de características
            features = np.array([[longitud_tokens, criterios_cumplidos, complejidad]])
            
            # Escalar características
            features_scaled = self.scaler.transform(features)
            
            # Predecir
            tiempo_predicho = self.model.predict(features_scaled)[0]
            
            # Asegurar que sea positivo y razonable
            tiempo_predicho = max(1.0, min(tiempo_predicho, 100.0))
            
            return round(tiempo_predicho, 1)
            
        except Exception as e:
            logger.error(f"Error en predicción: {str(e)}")
            return self._heuristic_estimation(historia, invest_json)
    
    def _heuristic_estimation(self, historia: str, invest_json: Dict) -> float:
        """
        Estimación heurística cuando el modelo no está disponible.
        
        Args:
            historia (str): Texto de la historia
            invest_json (Dict): Resultado INVEST
            
        Returns:
            float: Estimación heurística en horas
        """
        # Estimación base por longitud
        longitud = count_words(historia)
        if longitud <= 8:
            base_hours = 4
        elif longitud <= 15:
            base_hours = 8
        elif longitud <= 25:
            base_hours = 12
        else:
            base_hours = 16
        
        # Ajustar por criterios INVEST
        invest_scores = invest_json.get('INVEST', {})
        criterios_cumplidos = sum(1 for v in invest_scores.values() if v)
        
        # Menos criterios = más tiempo (mayor riesgo/complejidad)
        if criterios_cumplidos <= 3:
            base_hours *= 1.5
        elif criterios_cumplidos >= 5:
            base_hours *= 0.8
        
        return round(base_hours, 1)
    
    def save_model(self, model_path: str) -> bool:
        """
        Guarda el modelo entrenado.
        
        Args:
            model_path (str): Ruta donde guardar el modelo
            
        Returns:
            bool: True si se guardó exitosamente
        """
        if not self.is_trained:
            logger.warning("No hay modelo entrenado para guardar")
            return False
        
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'metrics': self.model_metrics,
                'is_trained': self.is_trained
            }
            
            joblib.dump(model_data, model_path)
            logger.info(f"Modelo guardado en: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando modelo: {str(e)}")
            return False
    
    def load_model(self, model_path: str) -> bool:
        """
        Carga un modelo previamente entrenado.
        
        Args:
            model_path (str): Ruta del modelo guardado
            
        Returns:
            bool: True si se cargó exitosamente
        """
        try:
            model_data = joblib.load(model_path)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.model_metrics = model_data['metrics']
            self.is_trained = model_data['is_trained']
            
            logger.info(f"Modelo cargado desde: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando modelo: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict:
        """
        Obtiene información del modelo actual.
        
        Returns:
            Dict: Información y métricas del modelo
        """
        if not self.is_trained:
            return {"status": "no_entrenado", "metrics": {}}
        
        return {
            "status": "entrenado",
            "metrics": self.model_metrics,
            "features": self.feature_names
        }

# Función de conveniencia para uso rápido
def quick_time_prediction(historia: str, invest_json: Dict, 
                         historicos_path: Optional[str] = None) -> float:
    """
    Predicción rápida de tiempo de desarrollo.
    
    Args:
        historia (str): Historia de usuario
        invest_json (Dict): Resultado de evaluación INVEST
        historicos_path (str, optional): Ruta a datos históricos para entrenar
        
    Returns:
        float: Tiempo estimado en horas
    """
    model = TimeEstimationModel()
    
    # Entrenar si se proporciona ruta de históricos
    if historicos_path:
        try:
            model.train_model(historicos_path)
        except Exception as e:
            logger.warning(f"No se pudo entrenar modelo: {str(e)}")
    
    return model.predict_tiempo(historia, invest_json)

if __name__ == "__main__":
    # Pruebas del módulo
    print("🧪 Probando módulo de regresión...")
    
    # Crear modelo
    model = TimeEstimationModel()
    
    # Historia de prueba
    historia_test = "Como usuario quiero iniciar sesión para acceder al sistema"
    invest_test = {
        "INVEST": {
            "Independiente": True,
            "Negociable": True,
            "Valiosa": True,
            "Estimable": True,
            "Small": True,
            "Testeable": False
        }
    }
    
    # Predicción heurística (sin entrenamiento)
    tiempo_predicho = model.predict_tiempo(historia_test, invest_test)
    print(f"Tiempo estimado (heurística): {tiempo_predicho} horas")
    
    print("✅ Pruebas completadas")
