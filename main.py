#!/usr/bin/env pvpython

import sys
import json
import os
import logging
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.config import DEFAULT_SOLVER, DEFAULT_SIMULATION_TYPE, DEFAULT_CALCULATION_TYPE


def main():
    # Configuración de logging para depuración
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s"
    )

    app = QApplication(sys.argv)

    # Ruta temporal del caso de prueba (reemplazar con diálogo de "Abrir proyecto" más adelante)
    test_case_dir = r"/home/miguel/01_GUI_openFoam/01_Test"

    # Crear configuración inicial
    config = {
        "working_directory": test_case_dir,
        "solver": DEFAULT_SOLVER,
        "simulation_type": DEFAULT_SIMULATION_TYPE,
        "calculation_type": DEFAULT_CALCULATION_TYPE
    }

    # Ruta al archivo config.json
    config_file_path = os.path.join(os.getcwd(), "config.json")

    # Guardar configuración en JSON
    try:
        with open(config_file_path, 'w') as config_file:
            json.dump(config, config_file, indent=4)
        logging.info(f"Configuración guardada en {config_file_path}")
    except Exception as e:
        logging.error(f"Error al guardar la configuración: {e}")
        sys.exit(1)

    # Instanciar y mostrar ventana principal
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
