# ui/sections/inicializacion.py

import os
import json
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox

# Importar el módulo conf_bc.py para generar boundary conditions
from ui.conf.conf_bc import generate_boundary_conditions
# Importar conf_alphat.py directamente para generar alphat
from ui.conf.bc.conf_alphat import generate_alphat_file
# Importar el módulo conf_constant.py para generar archivos del directorio constant
from ui.conf.conf_constant import generate_constant_files

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("inicializacion_debug.log", mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class Inicializacion(QWidget):
    """
    Sección donde el usuario genera los archivos de inicialización del caso.
    Aquí se llama a conf_bc.py para generar los archivos: U, T, p, p_rgh, k, etc.
    Además, aquí se añade la llamada a conf_alphat.py para generar 'alphat', y ahora
    se incorpora la funcionalidad para generar los archivos del directorio constant a partir de conf_constant.py.
    """
    def __init__(self, temp_dir=None):
        super().__init__()

        if temp_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            logging.debug(f"Directorio actual del script: {current_dir}")

            # Asumir que 'temp' está dos niveles arriba
            temp_dir = os.path.join(current_dir, "..", "..", "temp")
            temp_dir = os.path.normpath(temp_dir)
            logging.debug(f"Ruta calculada para 'temp': {temp_dir}")
        else:
            temp_dir = os.path.normpath(temp_dir)
            logging.debug(f"Ruta proporcionada para 'temp': {temp_dir}")

        self.temp_dir = os.path.abspath(temp_dir)
        logging.debug(f"Usando el directorio temp absoluto: {self.temp_dir}")

        # Se supone que case_config se carga o se construye en otro lugar.
        # Para este ejemplo, creamos un diccionario vacío.
        self.case_config = {}

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Inicialización")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        # Descripción
        description = QLabel(
            "En esta sección se generarán los archivos necesarios para la configuración del caso de OpenFOAM "
            "según los directorios establecidos en la plantilla de este programa."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # Botón para configurar condiciones iniciales y de contorno
        btn_initial_conditions = QPushButton("Configuracion de condiciones iniciales")
        btn_initial_conditions.clicked.connect(self.generate_initial_conditions)
        layout.addWidget(btn_initial_conditions)

        # Botón para configuración del directorio constant
        btn_constant_config = QPushButton("Configuracion del directorio constant")
        btn_constant_config.clicked.connect(self.generate_constant_config)
        layout.addWidget(btn_constant_config)

        # Botón para configuración del directorio system (sin funcionalidad por ahora)
        btn_system_config = QPushButton("Configuración del directorio system")
        layout.addWidget(btn_system_config)

        layout.addStretch()
        self.setLayout(layout)

    def generate_initial_conditions(self):
        logging.info("Iniciando la generación de condiciones iniciales y de contorno.")
        try:
            generate_boundary_conditions(self.temp_dir, parent=self)
            logging.info("Archivos de contorno generados correctamente.")
            self.generate_alphat_file()
            QMessageBox.information(
                self, "Éxito",
                "Se han generado correctamente los archivos de contorno y 'alphat'."
            )
        except Exception as e:
            error_msg = f"Ocurrió un error durante la generación de condiciones de contorno: {e}"
            QMessageBox.critical(self, "Error", error_msg)
            logging.error(error_msg)

    def generate_alphat_file(self):
        try:
            bc_file_path = os.path.join(self.temp_dir, "boundary_conditions.json")
            bc_file_path = os.path.normpath(bc_file_path)
            if not os.path.exists(bc_file_path):
                logging.warning(f"No se encontró el archivo {bc_file_path} para generar 'alphat'.")
                return
            with open(bc_file_path, 'r', encoding='utf-8') as f:
                bc_data = json.load(f)
            boundary_conds = bc_data.get("boundaryConditions", {})
            calculationType = bc_data.get("solverSettings", {}).get("calculationType", "Compresible")
            alpha_file_path = os.path.join(self.temp_dir, "DP0", "0", "alphat")
            alpha_file_path = os.path.normpath(alpha_file_path)
            generate_alphat_file(boundary_conds, alpha_file_path, calculationType)
            logging.info(f"Archivo 'alphat' generado exitosamente en {alpha_file_path}.")
        except Exception as e:
            logging.error(f"Error al generar 'alphat': {e}")
            raise e

    def generate_constant_config(self):
        """
        Llama a conf_constant.py para generar los archivos del directorio constant.
        """
        try:
            # Se asume que case_config contiene la información necesaria.
            from ui.conf.conf_constant import generate_constant_files
            # El directorio raíz se toma como el directorio en el que se encuentra main.py.
            main_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
            generate_constant_files(self.case_config, main_dir)
            QMessageBox.information(self, "Éxito", "Archivos del directorio constant generados correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar archivos del directorio constant:\n{e}")
            logging.error(f"Error en generate_constant_config: {e}")
