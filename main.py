import sys
import json
import os
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.config import DEFAULT_SOLVER, DEFAULT_SIMULATION_TYPE, DEFAULT_CALCULATION_TYPE

def main():
    app = QApplication(sys.argv)
    
    # Definir la ruta del caso de prueba (ruta fija por ahora)
    test_case_dir = r"/home/miguel/00_TFM/04_Quemador_KIAI_dyn_mesh"  # Ruta fija por ahora
    
    # Crear configuración
    config = {
        "working_directory": test_case_dir,
        "solver": DEFAULT_SOLVER,
        "simulation_type": DEFAULT_SIMULATION_TYPE,
        "calculation_type": DEFAULT_CALCULATION_TYPE
    }
    
    # Definir la ruta del archivo config.json
    config_file_path = os.path.join(os.getcwd(), "config.json")
    
    # Guardar configuración en el archivo JSON
    try:
        with open(config_file_path, 'w') as config_file:
            json.dump(config, config_file, indent=4)
        print(f"Configuración guardada en {config_file_path}")
    except Exception as e:
        print(f"Error al guardar la configuración: {e}")
        sys.exit(1)
    
    # Crear instancia de la ventana principal
    window = MainWindow()
    
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
