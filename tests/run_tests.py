"""
Test runner para ejecutar todos los tests unitarios.
"""

import unittest
import sys
from pathlib import Path

# Agregar paths necesarios
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "modules"))

def run_all_tests():
    """Ejecuta todos los tests unitarios."""
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("🧪 Ejecutando Tests Unitarios INVEST")
    print("=" * 50)
    
    success = run_all_tests()
    
    if success:
        print("\n✅ Todos los tests pasaron correctamente")
        sys.exit(0)
    else:
        print("\n❌ Algunos tests fallaron")
        sys.exit(1)
