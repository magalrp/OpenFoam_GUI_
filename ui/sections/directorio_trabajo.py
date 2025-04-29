# ui/sections/directorio_trabajo.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
import os
import json

from core.boundary_parser import parse_openfoam_boundary


class DirectorioTrabajo(QWidget):
    boundaries_loaded = pyqtSignal()  # Señal para notificar que las boundaries han sido cargadas

    def __init__(self, case_config=None):
        super().__init__()
        self.case_config = case_config
        self.boundaries_info = []

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.load_button = QPushButton("Cargar Boundaries")
        self.load_button.clicked.connect(self.load_boundaries)
        layout.addWidget(self.load_button)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "nFaces", "startFace"])
        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_boundaries(self):
        """
        Carga las boundaries desde el archivo boundary utilizando la ruta obtenida de config.json.
        """
        # Leer la configuración desde config.json
        config = self.read_config()
        if config is None:
            return  # Si hay un error al leer la configuración, no proceder

        working_directory = config.get("working_directory", "")
        if not working_directory:
            QMessageBox.critical(self, "Error", "La ruta del directorio de trabajo no está definida en config.json.")
            return

        # Construir la ruta al archivo boundary
        case_dir = os.path.join(working_directory, "constant", "polyMesh")
        boundary_file_path = os.path.join(case_dir, "boundary")

        # Verificar si el archivo boundary existe
        if not os.path.exists(boundary_file_path):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo boundary en la ruta:\n{boundary_file_path}")
            return

        try:
            self.boundaries_info = parse_openfoam_boundary(boundary_file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo parsear el archivo boundary:\n{str(e)}")
            return

        # Actualizar la tabla con la información de las boundaries
        self.table.setRowCount(len(self.boundaries_info))
        for row, boundary in enumerate(self.boundaries_info):
            self.table.setItem(row, 0, QTableWidgetItem(boundary.get("name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(boundary.get("type", "")))
            self.table.setItem(row, 2, QTableWidgetItem(str(boundary.get("nFaces", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(str(boundary.get("startFace", ""))))

        # Emitir señal para sincronizar boundaryConditions
        self.boundaries_loaded.emit()

    def read_config(self):
        """
        Lee el archivo config.json y devuelve la configuración como un diccionario.
        """
        config_file_path = os.path.join(os.getcwd(), "config.json")
        if not os.path.exists(config_file_path):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo de configuración 'config.json' en {os.getcwd()}.")
            return None

        try:
            with open(config_file_path, 'r') as config_file:
                config = json.load(config_file)
            return config
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "El archivo 'config.json' está mal formateado.")
            return None
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo 'config.json':\n{str(e)}")
            return None
