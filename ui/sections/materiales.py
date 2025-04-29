# ui/sections/materiales.py
"""
Este archivo pertenece a la ruta: ui/sections/materiales.py

Corrige el error al configurar un material:
- Se eliminan las referencias a 'setNotation' que podrían no existir
  en algunas versiones de PyQt.
"""

import os
import json

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QPushButton, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal

from core.json_manager import JSONManager
from ui.dialogs.config_material_dialog import ConfigMaterialDialog

class Materiales(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, case_config):
        super().__init__()
        self.case_config = case_config

        # Inicializar 'materials' en case_config si no existe
        self.case_config.setdefault("materials", [])

        # Instanciar JSONManager
        self.json_manager = JSONManager()
        self.section_name = "materials"

        self.init_ui()
        self.load_data()
        # Si no hay materiales, añadimos uno por defecto
        self.ensure_default_material()
        # Ajustar viscosidad a 'constant' si la energía está apagada
        self.enforce_constant_viscosity_if_no_energy()
        self.update_material_list()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Título y descripción
        title_label = QLabel("Materiales")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title_label)

        description_label = QLabel("En esta sección se definen los materiales utilizados en el modelo.")
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        # Tabla de Materiales
        self.material_table = QTableWidget()
        self.material_table.setColumnCount(2)
        self.material_table.setHorizontalHeaderLabels(["Nombre", "Tipo"])
        self.material_table.horizontalHeader().setStretchLastSection(True)
        self.material_table.verticalHeader().setVisible(False)
        layout.addWidget(self.material_table)

        # Botones
        btn_layout = QHBoxLayout()

        self.btn_create_material = QPushButton("Crear Material")
        self.btn_create_material.clicked.connect(self.create_material)
        btn_layout.addWidget(self.btn_create_material)

        self.btn_config_material = QPushButton("Configurar Material")
        self.btn_config_material.clicked.connect(self.configure_material)
        btn_layout.addWidget(self.btn_config_material)

        btn_layout.addStretch()

        self.btn_delete_material = QPushButton("Eliminar Material")
        self.btn_delete_material.clicked.connect(self.delete_material)
        btn_layout.addWidget(self.btn_delete_material)

        layout.addLayout(btn_layout)
        layout.addStretch()
        self.setLayout(layout)

    def load_data(self):
        data = self.json_manager.load_section(self.section_name)
        if data:
            self.case_config["materials"] = data.get("materials", [])

    def save_data(self):
        data = {
            "materials": self.case_config.get("materials", [])
        }
        success, msg = self.json_manager.save_section(self.section_name, data)
        if not success:
            QMessageBox.critical(self, "Error", msg)

    def ensure_default_material(self):
        if not self.case_config["materials"]:
            default_air = {
                "name": "Aire",
                "type": "fluid",
                "properties": {
                    "densityModel": "constant",
                    "densityValue": 1.225
                }
            }
            # Si hay turbulencia
            turbulence_model = self.case_config.get("turbulenceModel", "laminar")
            if turbulence_model.lower() != "laminar":
                default_air["properties"]["viscosityModel"] = "constant"
                default_air["properties"]["viscosityValue"] = 1.8e-5
            # Si energía activa
            if self.case_config.get("energy_active", False):
                default_air["properties"]["cpModel"] = "constant"
                default_air["properties"]["cpValue"] = 1005.0
                default_air["properties"]["conductivityModel"] = "constant"
                default_air["properties"]["conductivityValue"] = 0.025

            self.case_config["materials"].append(default_air)
            self.save_data()

    def enforce_constant_viscosity_if_no_energy(self):
        """
        Si la energía está apagada, forzamos todos los materiales a 'constant' en la viscosidad.
        """
        if not self.case_config.get("energy_active", False):
            for mat in self.case_config["materials"]:
                props = mat.setdefault("properties", {})
                if "viscosityModel" in props:
                    props["viscosityModel"] = "constant"
            self.save_data()

    def update_material_list(self):
        mats = self.case_config["materials"]
        self.material_table.setRowCount(len(mats))

        for i, mat in enumerate(mats):
            name_item = QTableWidgetItem(mat.get("name", ""))
            type_item = QTableWidgetItem(mat.get("type", ""))
            name_item.setFlags(Qt.ItemIsEnabled)
            type_item.setFlags(Qt.ItemIsEnabled)
            self.material_table.setItem(i, 0, name_item)
            self.material_table.setItem(i, 1, type_item)

    def create_material(self):
        text, ok = QInputDialog.getText(self, "Crear Material", "Nombre del nuevo material:")
        if ok and text.strip():
            new_name = text.strip()
            new_mat = {
                "name": new_name,
                "type": "fluid",
                "properties": {
                    "densityModel": "constant",
                    "densityValue": 1.225
                }
            }
            # Checar turbulencia
            turbulence_model = self.case_config.get("turbulenceModel", "laminar")
            if turbulence_model.lower() != "laminar":
                new_mat["properties"]["viscosityModel"] = "constant"
                new_mat["properties"]["viscosityValue"] = 1.8e-5
            # Checar energía
            if self.case_config.get("energy_active", False):
                new_mat["properties"]["cpModel"] = "constant"
                new_mat["properties"]["cpValue"] = 1005.0
                new_mat["properties"]["conductivityModel"] = "constant"
                new_mat["properties"]["conductivityValue"] = 0.025

            self.case_config["materials"].append(new_mat)
            self.save_data()
            self.update_material_list()

            # Abrir el diálogo de configuración directamente
            dlg = ConfigMaterialDialog(case_config=self.case_config, parent=self, select_material=new_name)
            if dlg.exec_() == dlg.Accepted:
                self.update_material_list()
                self.save_data()
                self.data_changed.emit()

    def configure_material(self):
        if not self.case_config["materials"]:
            QMessageBox.information(self, "Info", "No hay materiales definidos.")
            return

        dlg = ConfigMaterialDialog(case_config=self.case_config, parent=self)
        if dlg.exec_() == dlg.Accepted:
            self.update_material_list()
            self.save_data()
            self.data_changed.emit()

    def delete_material(self):
        row = self.material_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un material para eliminar.")
            return
        mat_name = self.material_table.item(row, 0).text()
        self.case_config["materials"] = [
            m for m in self.case_config["materials"] if m.get("name", "") != mat_name
        ]
        self.update_material_list()
        self.save_data()
        self.data_changed.emit()
