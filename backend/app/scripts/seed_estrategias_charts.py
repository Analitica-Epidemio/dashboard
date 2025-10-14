#!/usr/bin/env python3
"""
Script para ejecutar solo los pasos 5 y 6 del seed:
- Estrategias epidemiológicas
- Gráficos del dashboard
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.scripts.seeds.strategies import seed_all_strategies
from app.scripts.seeds.charts import seed_charts


def main():
    """Ejecuta seed de estrategias y charts solamente"""
    print("\n" + "="*70)
    print("🎯 SEED PARCIAL - ESTRATEGIAS Y GRÁFICOS")
    print("="*70)

    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://epidemiologia_user:epidemiologia_password@localhost:5432/epidemiologia_db")
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(DATABASE_URL)

    try:
        # PASO 5: Estrategias
        print("\n" + "="*70)
        print("PASO 5/6: ESTRATEGIAS")
        print("="*70)
        try:
            with Session(engine) as session:
                seed_all_strategies(session)
                print("✅ Estrategias epidemiológicas cargadas")
        except Exception as e:
            print(f"⚠️  Error cargando estrategias: {e}")
            import traceback
            traceback.print_exc()

        # PASO 6: Gráficos
        print("\n" + "="*70)
        print("PASO 6/6: GRÁFICOS")
        print("="*70)
        try:
            with Session(engine) as session:
                seed_charts(session)
                print("✅ Configuración de gráficos cargada")
        except Exception as e:
            print(f"⚠️  Error cargando charts: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "="*70)
        print("✅ SEED PARCIAL COMPLETADO")
        print("="*70)
        print("\n  ✅ Estrategias epidemiológicas")
        print("  ✅ Configuración de gráficos")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
