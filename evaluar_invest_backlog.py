#!/usr/bin/env python3
"""
Script para evaluar las historias de usuario del backlog según criterios INVEST
"""

import pandas as pd
import sys
import os

# Agregar el módulo al path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from modules.utils import load_azure_devops_csv
from modules.invest_agent import InvestAgent

def evaluar_backlog_invest():
    """Evalúa todas las historias del backlog con criterios INVEST"""
    try:
        print("🧪 Evaluando Backlog con Criterios INVEST")
        print("=" * 50)
        
        # Cargar datos del backlog
        df_backlog = load_azure_devops_csv('data/backlog.csv')
        print(f"\n📊 Historias cargadas: {len(df_backlog)}")
        
        # Inicializar agente INVEST en modo reglas
        agent = InvestAgent(modo="reglas")
        
        # Evaluar cada historia
        resultados = []
        
        for index, row in df_backlog.iterrows():
            historia_id = row['ID']
            historia_texto = row['Historia']
            
            print(f"\n🔍 Evaluando Historia #{historia_id}")
            print(f"📝 Texto: {historia_texto[:80]}...")
            
            # Evaluar con INVEST
            resultado = agent.evaluate_story(historia_texto)
            
            if resultado and 'INVEST' in resultado:
                invest_data = resultado['INVEST']
                
                # Calcular puntuación
                criterios_cumplidos = sum(1 for v in invest_data.values() if v)
                puntuacion = criterios_cumplidos / 6 * 100  # Porcentaje
                
                # Mostrar resultado
                print(f"⭐ Puntuación INVEST: {puntuacion:.1f}% ({criterios_cumplidos}/6)")
                
                # Detallar criterios
                criterios = {
                    'Independiente': '🔗',
                    'Negociable': '🤝', 
                    'Valiosa': '💎',
                    'Estimable': '📏',
                    'Small': '📦',
                    'Testeable': '🧪'
                }
                
                for criterio, icono in criterios.items():
                    estado = "✅" if invest_data.get(criterio, False) else "❌"
                    print(f"  {icono} {criterio}: {estado}")
                
                # Guardar resultado
                resultados.append({
                    'ID': historia_id,
                    'Historia': historia_texto,
                    'Puntuacion_INVEST': puntuacion,
                    'Criterios_Cumplidos': criterios_cumplidos,
                    **{f"INVEST_{k}": v for k, v in invest_data.items()}
                })
                
                if resultado.get('sugerencias'):
                    print(f"💡 Sugerencias: {'; '.join(resultado['sugerencias'])}")
            else:
                print("❌ Error evaluando historia")
                resultados.append({
                    'ID': historia_id,
                    'Historia': historia_texto,
                    'Puntuacion_INVEST': 0,
                    'Criterios_Cumplidos': 0
                })
        
        # Resumen general
        print("\n" + "=" * 50)
        print("📈 RESUMEN GENERAL DEL BACKLOG")
        print("=" * 50)
        
        if resultados:
            df_resultados = pd.DataFrame(resultados)
            
            # Estadísticas generales
            promedio_puntuacion = df_resultados['Puntuacion_INVEST'].mean()
            mediana_puntuacion = df_resultados['Puntuacion_INVEST'].median()
            historias_buenas = len(df_resultados[df_resultados['Puntuacion_INVEST'] >= 70])
            historias_regulares = len(df_resultados[(df_resultados['Puntuacion_INVEST'] >= 50) & (df_resultados['Puntuacion_INVEST'] < 70)])
            historias_malas = len(df_resultados[df_resultados['Puntuacion_INVEST'] < 50])
            
            print(f"📊 Puntuación promedio: {promedio_puntuacion:.1f}%")
            print(f"📊 Puntuación mediana: {mediana_puntuacion:.1f}%")
            print(f"✅ Historias buenas (≥70%): {historias_buenas}")
            print(f"⚠️  Historias regulares (50-69%): {historias_regulares}")
            print(f"❌ Historias problemáticas (<50%): {historias_malas}")
            
            # Top y bottom historias
            print(f"\n🏆 TOP 3 MEJORES HISTORIAS:")
            top_historias = df_resultados.nlargest(3, 'Puntuacion_INVEST')
            for _, row in top_historias.iterrows():
                print(f"  #{row['ID']}: {row['Puntuacion_INVEST']:.1f}% - {row['Historia'][:60]}...")
            
            print(f"\n⚠️  TOP 3 HISTORIAS A MEJORAR:")
            bottom_historias = df_resultados.nsmallest(3, 'Puntuacion_INVEST')
            for _, row in bottom_historias.iterrows():
                print(f"  #{row['ID']}: {row['Puntuacion_INVEST']:.1f}% - {row['Historia'][:60]}...")
            
            # Análisis por criterio
            print(f"\n📋 ANÁLISIS POR CRITERIO INVEST:")
            criterios_invest = ['Independiente', 'Negociable', 'Valiosa', 'Estimable', 'Small', 'Testeable']
            for criterio in criterios_invest:
                col_name = f"INVEST_{criterio}"
                if col_name in df_resultados.columns:
                    cumplimiento = df_resultados[col_name].sum()
                    porcentaje = cumplimiento / len(df_resultados) * 100
                    print(f"  {criterio}: {cumplimiento}/{len(df_resultados)} ({porcentaje:.1f}%)")
            
            # Guardar resultados
            df_resultados.to_csv('resultados_invest_backlog.csv', index=False)
            print(f"\n💾 Resultados guardados en: resultados_invest_backlog.csv")
        
    except Exception as e:
        print(f"\n❌ Error en evaluación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    evaluar_backlog_invest()
