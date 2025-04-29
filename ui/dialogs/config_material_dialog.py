# ui/dialogs/config_material_dialog.py
"""
Este archivo pertenece a la ruta: ui/dialogs/config_material_dialog.py

Se soluciona el error al cargar un material con 'sutherland' y 'viscosityValue=None'
pasando un valor por defecto (p. ej. 1.8e-5) a setValue, evitando el TypeError.
"""

import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QFormLayout, QLineEdit, QDoubleSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt

class ConfigMaterialDialog(QDialog):
    def __init__(self, case_config, parent=None, select_material=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Material")
        self.case_config = case_config

        self.materials = self.case_config.get("materials", [])
        self.turbulenceActive = (self.case_config.get("turbulenceModel", "laminar").lower() != "laminar")
        self.energyActive = self.case_config.get("energy_active", False)

        self.selected_index = 0
        if select_material:
            for i, mat in enumerate(self.materials):
                if mat["name"] == select_material:
                    self.selected_index = i
                    break

        self._old_viscosity_model = None

        main_layout = QVBoxLayout(self)
        form = QFormLayout()

        # 1. Selección de material
        self.combo_mat = QComboBox()
        for mat in self.materials:
            self.combo_mat.addItem(mat["name"])
        self.combo_mat.setCurrentIndex(self.selected_index)
        self.combo_mat.currentIndexChanged.connect(self.on_material_changed)
        form.addRow("Seleccionar Material:", self.combo_mat)

        # 2. Nombre del material
        self.line_name = QLineEdit()
        form.addRow("Nombre del material:", self.line_name)

        # Densidad
        density_layout = QHBoxLayout()
        self.label_density = QLabel("Densidad (kg/m3):")
        density_layout.addWidget(self.label_density)

        self.combo_density_model = QComboBox()
        self.combo_density_model.addItems(["constant", "idealGas"])
        self.combo_density_model.currentTextChanged.connect(self._on_density_model_changed)
        density_layout.addWidget(self.combo_density_model)

        self.spin_density_value = QDoubleSpinBox()
        self.spin_density_value.setDecimals(5)
        self.spin_density_value.setRange(0, 1e5)
        density_layout.addWidget(self.spin_density_value)

        form.addRow(density_layout)

        # Viscosidad (solo si turbulencia)
        self.visc_layout = QHBoxLayout()
        self.label_visc = QLabel("Viscosidad dinámica (kg/m·s):")
        self.visc_layout.addWidget(self.label_visc)

        self.combo_visc_model = QComboBox()
        self.combo_visc_model.addItems(["constant", "sutherland"])
        self.combo_visc_model.currentTextChanged.connect(self._on_viscosity_model_changed)
        self.visc_layout.addWidget(self.combo_visc_model)

        self.spin_visc_value = QDoubleSpinBox()
        self.spin_visc_value.setRange(1e-12, 1e12)
        self.spin_visc_value.setDecimals(8)
        self.visc_layout.addWidget(self.spin_visc_value)

        if not self.turbulenceActive:
            self.label_visc.hide()
            self.combo_visc_model.hide()
            self.spin_visc_value.hide()

        form.addRow(self.visc_layout)

        # Cp + Conductividad (solo si energía)
        self.cp_layout = QHBoxLayout()
        self.label_cp = QLabel("Cp (J/kg·K):")
        self.cp_layout.addWidget(self.label_cp)

        self.combo_cp_model = QComboBox()
        self.combo_cp_model.addItems(["constant", "polynomial", "janaf"])
        self.cp_layout.addWidget(self.combo_cp_model)

        self.spin_cp_value = QDoubleSpinBox()
        self.spin_cp_value.setRange(0, 1e6)
        self.cp_layout.addWidget(self.spin_cp_value)

        if not self.energyActive:
            self.label_cp.hide()
            self.combo_cp_model.hide()
            self.spin_cp_value.hide()

        form.addRow(self.cp_layout)

        self.cond_layout = QHBoxLayout()
        self.label_cond = QLabel("Conductividad (W/m·K):")
        self.cond_layout.addWidget(self.label_cond)

        self.combo_cond_model = QComboBox()
        self.combo_cond_model.addItems(["constant", "polynomial"])
        self.cond_layout.addWidget(self.combo_cond_model)

        self.spin_cond_value = QDoubleSpinBox()
        self.spin_cond_value.setRange(0, 1e5)
        self.cond_layout.addWidget(self.spin_cond_value)

        if not self.energyActive:
            self.label_cond.hide()
            self.combo_cond_model.hide()
            self.spin_cond_value.hide()

        form.addRow(self.cond_layout)
        main_layout.addLayout(form)

        # Botones Aceptar/Cancelar
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("Aceptar")
        self.btn_cancel = QPushButton("Cancelar")
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        main_layout.addLayout(btn_layout)

        self.btn_ok.clicked.connect(self.accept_changes)
        self.btn_cancel.clicked.connect(self.reject)

        self.setLayout(main_layout)

        # Cargar datos del material seleccionado
        self.on_material_changed(self.selected_index)

    def on_material_changed(self, idx):
        if idx < 0 or idx >= len(self.materials):
            return
        mat = self.materials[idx]
        props = mat.setdefault("properties", {})

        self.line_name.setText(mat.get("name", ""))

        # Densidad
        dmodel = props.get("densityModel", "constant")
        dval = props.get("densityValue", 1.225)
        self.combo_density_model.setCurrentText(dmodel)
        self.spin_density_value.setValue(dval if dval is not None else 1.225)
        self._on_density_model_changed(dmodel)

        # Viscosidad
        if self.turbulenceActive:
            vmodel = props.get("viscosityModel", "constant")
            vval = props.get("viscosityValue", 1.8e-5)
            if vval is None:
                vval = 1.8e-5  # fallback
            self.combo_visc_model.setCurrentText(vmodel)
            self.spin_visc_value.setValue(vval)
            self._old_viscosity_model = vmodel

        # Cp y Conductividad
        if self.energyActive:
            cpmodel = props.get("cpModel", "constant")
            cpval = props.get("cpValue", 1005.0)
            self.combo_cp_model.setCurrentText(cpmodel)
            self.spin_cp_value.setValue(cpval if cpval is not None else 1005.0)

            condmodel = props.get("conductivityModel", "constant")
            condval = props.get("conductivityValue", 0.025)
            self.combo_cond_model.setCurrentText(condmodel)
            self.spin_cond_value.setValue(condval if condval is not None else 0.025)

        self.selected_index = idx

    def _on_density_model_changed(self, new_model):
        if new_model == "idealGas":
            self.spin_density_value.hide()
        else:
            self.spin_density_value.show()

    def _on_viscosity_model_changed(self, new_model):
        if not self.turbulenceActive:
            return

        # Solo mostrar aviso si se pasa de constant a sutherland
        if self._old_viscosity_model == "constant" and new_model == "sutherland":
            QMessageBox.information(
                self,
                "Sutherland activado",
                "Se ha seleccionado 'sutherland'. Se activará la ecuación de energía."
            )
            self.case_config["energy_active"] = True

        self._old_viscosity_model = new_model

        if new_model == "constant":
            self.spin_visc_value.show()
        else:
            self.spin_visc_value.hide()

    def accept_changes(self):
        idx = self.combo_mat.currentIndex()
        if idx < 0 or idx >= len(self.materials):
            QMessageBox.warning(self, "Error", "No hay material válido seleccionado.")
            return

        mat = self.materials[idx]
        new_name = self.line_name.text().strip()
        mat["name"] = new_name if new_name else "Material_Sin_Nombre"

        props = mat.setdefault("properties", {})
        # Densidad
        dmodel = self.combo_density_model.currentText()
        props["densityModel"] = dmodel
        if dmodel == "constant":
            props["densityValue"] = self.spin_density_value.value()
        else:
            props["densityValue"] = None

        # Viscosidad
        if self.turbulenceActive:
            vmodel = self.combo_visc_model.currentText()
            props["viscosityModel"] = vmodel
            if vmodel == "constant":
                props["viscosityValue"] = self.spin_visc_value.value()
            else:
                props["viscosityValue"] = None

        # Cp + Conductividad
        if self.case_config.get("energy_active", False):
            cpmodel = self.combo_cp_model.currentText()
            if cpmodel == "constant":
                props["cpModel"] = cpmodel
                props["cpValue"] = self.spin_cp_value.value()
            else:
                props["cpModel"] = cpmodel
                props["cpValue"] = None

            condmodel = self.combo_cond_model.currentText()
            if condmodel == "constant":
                props["conductivityModel"] = condmodel
                props["conductivityValue"] = self.spin_cond_value.value()
            else:
                props["conductivityModel"] = condmodel
                props["conductivityValue"] = None
        else:
            props["cpModel"] = None
            props["cpValue"] = None
            props["conductivityModel"] = None
            props["conductivityValue"] = None

        self.accept()
