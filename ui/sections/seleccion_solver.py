# ui/sections/seleccion_solver.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QComboBox,
    QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal

from core.json_manager import JSONManager
from ui.conf.bc.conf_alphat import generate_alphat_file  # Importar la función para generar alphat

import json
import os
import logging


class SeleccionSolver(QWidget):
    # Señal para notificar cambios que puedan requerir guardar datos
    solver_changed = pyqtSignal()

    def __init__(self, case_config):
        super().__init__()
        self.case_config = case_config
        self.json_manager = JSONManager()
        self.section_name = "solver_settings"

        # Asegurarse de que 'solverSettings' exista en case_config
        self.case_config.setdefault("solverSettings", {
            "simulationType": "Transitorio",
            "calculationType": "Compresible",
            "solver": "reactingParcelFoam"
        })

        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Selección de Solver")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        # Tipo de Simulación
        sim_layout = QHBoxLayout()
        sim_label = QLabel("Tipo de Simulación:")
        self.sim_combo = QComboBox()
        self.sim_combo.addItems(["Transitorio", "Estacionario"])
        self.sim_combo.currentTextChanged.connect(self.update_simulation_type)
        sim_layout.addWidget(sim_label)
        sim_layout.addWidget(self.sim_combo)
        layout.addLayout(sim_layout)

        # Tipo de Cálculo
        calc_layout = QHBoxLayout()
        calc_label = QLabel("Tipo de Cálculo:")
        self.calc_combo = QComboBox()
        self.calc_combo.addItems(["Compresible", "Incompresible"])
        self.calc_combo.currentTextChanged.connect(self.update_calculation_type)
        calc_layout.addWidget(calc_label)
        calc_layout.addWidget(self.calc_combo)
        layout.addLayout(calc_layout)

        # Selección de Solver
        solver_layout = QHBoxLayout()
        solver_label = QLabel("Solver:")
        self.solver_combo = QComboBox()
        self.solver_combo.addItems(["reactingParcelFoam", "simpleFoam", "pisoFoam"])  # Añadir más solvers si es necesario
        self.solver_combo.currentTextChanged.connect(self.update_solver_selection)
        solver_layout.addWidget(solver_label)
        solver_layout.addWidget(self.solver_combo)
        layout.addLayout(solver_layout)

        # Botón para guardar configuraciones del solver
        save_solver_button = QPushButton("Guardar Configuración del Solver")
        save_solver_button.clicked.connect(self.save_solver_settings)
        layout.addWidget(save_solver_button)

        layout.addStretch()
        self.setLayout(layout)

    def update_simulation_type(self, text):
        """
        Actualiza el tipo de simulación en case_config.
        """
        self.case_config["solverSettings"]["simulationType"] = text
        self.solver_changed.emit()  # Emitir señal de cambio
        print(f"Tipo de Simulación actualizado a: {text}")  # Línea de depuración

    def update_calculation_type(self, text):
        """
        Actualiza el tipo de cálculo en case_config.
        """
        self.case_config["solverSettings"]["calculationType"] = text
        self.solver_changed.emit()  # Emitir señal de cambio
        print(f"Tipo de Cálculo actualizado a: {text}")  # Línea de depuración

    def update_solver_selection(self, text):
        """
        Actualiza la selección del solver en case_config.
        """
        self.case_config["solverSettings"]["solver"] = text
        self.solver_changed.emit()  # Emitir señal de cambio
        print(f"Solver seleccionado: {text}")  # Línea de depuración

    def save_solver_settings(self):
        """
        Guarda las configuraciones del solver en un archivo JSON específico y genera el archivo alphat.
        """
        data = {
            "simulationType": self.case_config["solverSettings"].get("simulationType", "Transitorio"),
            "calculationType": self.case_config["solverSettings"].get("calculationType", "Compresible"),
            "solver": self.case_config["solverSettings"].get("solver", "reactingParcelFoam")
        }
        success, msg = self.json_manager.save_section(self.section_name, data)
        if success:
            QMessageBox.information(self, "Guardado", msg)
            print("Solver Settings guardados exitosamente.")  # Línea de depuración

            # Generar el archivo alphat después de guardar las configuraciones del solver
            self.generate_alphat_file()
        else:
            QMessageBox.critical(self, "Error", msg)
            print(f"Error al guardar Solver Settings: {msg}")  # Línea de depuración

    def load_data(self):
        """
        Carga las configuraciones del solver desde el archivo JSON.
        """
        # Verificar si el archivo solver_settings.json existe en el directorio temp
        temp_dir = "temp"
        json_path = os.path.join(temp_dir, "solver_settings.json")
        if os.path.exists(json_path):
            data = self.json_manager.load_section(self.section_name)
        else:
            data = None

        if data:
            simulationType = data.get("simulationType", "Transitorio")
            calculationType = data.get("calculationType", "Compresible")
            solver = data.get("solver", "reactingParcelFoam")

            self.sim_combo.setCurrentText(simulationType)
            self.calc_combo.setCurrentText(calculationType)
            self.solver_combo.setCurrentText(solver)

            # Actualizar case_config
            self.case_config["solverSettings"]["simulationType"] = simulationType
            self.case_config["solverSettings"]["calculationType"] = calculationType
            self.case_config["solverSettings"]["solver"] = solver

            print("Solver Settings cargados desde JSON:")  # Línea de depuración
            print(json.dumps(data, indent=4))  # Línea de depuración
        else:
            # Si no existe el archivo, usar los valores por defecto ya establecidos en __init__
            print("No se encontró solver_settings.json. Usando valores por defecto.")
            # Asegurarse de que los valores por defecto ya están establecidos en __init__

    def generate_alphat_file(self):
        """
        Genera el archivo 'alphat' basado en las condiciones de contorno y la configuración del solver.
        """
        boundary_conditions = self.case_config.get("boundaryConditions", {})
        # Obtener el tipo de cálculo desde las configuraciones del solver
        calculationType = self.case_config["solverSettings"].get("calculationType", "Compresible")
        # Definir la ruta del archivo 'alphat'
        alpha_file_path = os.path.join("temp", "DP0", "0", "alphat")
        # Generar el archivo 'alphat'
        generate_alphat_file(boundary_conditions, alpha_file_path, calculationType)
