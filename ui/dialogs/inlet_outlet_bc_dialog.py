# ui/dialogs/inletOutlet_bc_dialog.py

import os
import json
import copy

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QTabWidget, QWidget,
    QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QComboBox
)
from PyQt5.QtCore import Qt
from ui.widgets.numeric_line_edit import NumericLineEdit
class InletOutletBCDialog(QDialog):
    def __init__(self, parent=None, turbulenceModel="laminar",
                 chemistryActive=False, chosen_species=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("InletOutlet Boundary Conditions")

        # Determinar si es inlet u outlet a partir de los datos iniciales
        self.bc_type = (initial_data.get("type", "inlet").lower()
                        if initial_data else "inlet")

        # Procesar modelo de turbulencia
        if isinstance(turbulenceModel, dict):
            self.effective_turbulence_model = turbulenceModel.get("model", "laminar").lower()
        else:
            self.effective_turbulence_model = turbulenceModel.lower()

        # Leer configuración de química si existe
        constant_path = os.path.join("temp", "constant.json")
        if os.path.exists(constant_path):
            try:
                with open(constant_path, "r") as f:
                    cd = json.load(f)
                self.chemistryActive = cd.get("especiesActive", False)
                self.chosen_species = cd.get("especies_options", {}).get("activeSpecies", [])
            except Exception:
                self.chemistryActive = chemistryActive
                self.chosen_species = chosen_species or []
        else:
            self.chemistryActive = chemistryActive
            self.chosen_species = chosen_species or []

        # Valores por defecto
        default_data = {
            "type": self.bc_type,
            "pressureValue":    0.0,
            "temperature":      300.0,
            "velocityType":     "inletOutlet",
            "velocityValue":    0.0,
            "velocityInit":     0.0,
            "kType":            "inletOutlet",
            "kValue":           0.1,
            "kIntensity":       0.0,
            "epsilonType":      "inletOutlet",
            "epsilonValue":     10.0,
            "epsilonMixingLength": 0.0,
            "omegaType":        "inletOutlet",
            "omegaValue":       5.0,
            "omegaMixingLength": 0.0
        }
        # Añadir valores químicos si procede
        if self.chemistryActive and self.chosen_species:
            for sp in self.chosen_species:
                default_data[f"{sp}_chemType"] = "inletOutlet"
                default_data[f"{sp}_chemValue"] = 0.0

        # Mezclar con initial_data
        data = copy.deepcopy(initial_data or {})
        for k, v in default_data.items():
            if k not in data or data[k] is None:
                data[k] = v
        self.data = data

        # Construir la interfaz
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # --- Pestaña Presión y Turbulencia ---
        pt_tab = QWidget()
        pt_layout = QFormLayout(pt_tab)

        # Presión
        self.pressure_spin = QDoubleSpinBox()
        self.pressure_spin.setRange(-1e5, 1e7)
        self.pressure_spin.setValue(self.data["pressureValue"])
        self.pressure_spin.setSuffix(" Pa")
        pt_layout.addRow("Presión:", self.pressure_spin)

        # Turbulencia según modelo
        if self.effective_turbulence_model == "kepsilon":
            # k
            self.k_type_label = QLabel(self.data["kType"])
            self.k_value      = QDoubleSpinBox()
            self.k_value.setRange(0, 1e3)
            self.k_value.setValue(self.data["kValue"])
            pt_layout.addRow("k Tipo:", self.k_type_label)
            pt_layout.addRow("k Valor:", self.k_value)

            # Intensidad de k
            self.k_intensity = QDoubleSpinBox()
            self.k_intensity.setRange(0, 1e2)
            self.k_intensity.setValue(self.data["kIntensity"])
            pt_layout.addRow("k Intensidad:", self.k_intensity)

            # ε
            self.epsilon_type_label = QLabel(self.data["epsilonType"])
            self.epsilon_value      = QDoubleSpinBox()
            self.epsilon_value.setRange(0, 1e5)
            self.epsilon_value.setValue(self.data["epsilonValue"])
            pt_layout.addRow("ε Tipo:", self.epsilon_type_label)
            pt_layout.addRow("ε Valor:", self.epsilon_value)

            # Longitud de mezcla de ε
            self.epsilon_mixingLength = QDoubleSpinBox()
            self.epsilon_mixingLength.setRange(0, 1e3)
            self.epsilon_mixingLength.setValue(self.data["epsilonMixingLength"])
            pt_layout.addRow("ε Long. mezcla:", self.epsilon_mixingLength)

        elif self.effective_turbulence_model == "komega":
            # k
            self.k_type_label = QLabel(self.data["kType"])
            self.k_value      = QDoubleSpinBox()
            self.k_value.setRange(0, 1e3)
            self.k_value.setValue(self.data["kValue"])
            pt_layout.addRow("k Tipo:", self.k_type_label)
            pt_layout.addRow("k Valor:", self.k_value)

            # Intensidad de k
            self.k_intensity = QDoubleSpinBox()
            self.k_intensity.setRange(0, 1e2)
            self.k_intensity.setValue(self.data["kIntensity"])
            pt_layout.addRow("k Intensidad:", self.k_intensity)

            # ω
            self.omega_type_label = QLabel(self.data["omegaType"])
            self.omega_value      = QDoubleSpinBox()
            self.omega_value.setRange(0, 1e5)
            self.omega_value.setValue(self.data["omegaValue"])
            pt_layout.addRow("ω Tipo:", self.omega_type_label)
            pt_layout.addRow("ω Valor:", self.omega_value)

            # Longitud de mezcla de ω
            self.omega_mixingLength = QDoubleSpinBox()
            self.omega_mixingLength.setRange(0, 1e3)
            self.omega_mixingLength.setValue(self.data["omegaMixingLength"])
            pt_layout.addRow("ω Long. mezcla:", self.omega_mixingLength)

        # Si es laminar u otro, no añadimos más filas

        tabs.addTab(pt_tab, "Presión")

        # --- Pestaña Temperatura ---
        temp_tab = QWidget()
        t_layout = QFormLayout(temp_tab)
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0, 2000)
        self.temp_spin.setValue(self.data["temperature"])
        self.temp_spin.setSuffix(" K")
        t_layout.addRow("Temperatura:", self.temp_spin)
        tabs.addTab(temp_tab, "Temperatura")

        # --- Pestaña Velocidad (solo para inlet) ---
        if self.bc_type == "inlet":
            vel_tab = QWidget()
            v_layout = QFormLayout(vel_tab)

            self.vel_type_combo = QComboBox()
            self.vel_type_combo.addItems([
                "flowRateInletVelocity",
                "inletOutlet",
                "velocityInlet"
            ])
            self.vel_type_combo.setCurrentText(self.data["velocityType"])
            v_layout.addRow("Tipo de velocidad:", self.vel_type_combo)

            self.vel_value = QDoubleSpinBox()
            self.vel_value.setRange(0, 1e5)
            self.vel_value.setValue(self.data["velocityValue"])
            self.vel_value.setSuffix(" m/s")
            v_layout.addRow("Valor de velocidad:", self.vel_value)

            self.vel_init = QDoubleSpinBox()
            self.vel_init.setRange(0, 1e5)
            self.vel_init.setValue(self.data["velocityInit"])
            self.vel_init.setSuffix(" m/s")
            v_layout.addRow("Velocidad inicial:", self.vel_init)

            tabs.addTab(vel_tab, "Velocidad")

        # --- Pestaña Química ---
        if self.chemistryActive and self.chosen_species:
            chem_tab = QWidget()
            c_layout = QFormLayout(chem_tab)
            self.species_widgets = {}
            for sp in self.chosen_species:
                lbl   = QLabel("inletOutlet (fijo)")
                spin  = QDoubleSpinBox()
                spin.setRange(0, 1e5)
                spin.setValue(self.data.get(f"{sp}_chemValue", 0.0))
                row   = QHBoxLayout()
                row.addWidget(lbl)
                row.addWidget(spin)
                container = QWidget()
                container.setLayout(row)
                c_layout.addRow(f"Fracción molar {sp}:", container)
                self.species_widgets[sp] = spin
            tabs.addTab(chem_tab, "Química")

        # Montar controles
        layout.addWidget(tabs)
        btns = QHBoxLayout()
        btn_accept = QPushButton("Aceptar")
        btn_cancel = QPushButton("Cancelar")
        btn_accept.clicked.connect(self.accept_changes)
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_accept)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def accept_changes(self):
        # Presión
        self.data["pressureValue"] = self.pressure_spin.value()

        # Turbulencia
        if self.effective_turbulence_model == "kepsilon":
            self.data["kType"]               = self.k_type_label.text()
            self.data["kValue"]              = self.k_value.value()
            self.data["kIntensity"]          = self.k_intensity.value()
            self.data["epsilonType"]         = self.epsilon_type_label.text()
            self.data["epsilonValue"]        = self.epsilon_value.value()
            self.data["epsilonMixingLength"] = self.epsilon_mixingLength.value()
            # Limpiar ω
            self.data["omegaType"]           = None
            self.data["omegaValue"]          = None
            self.data["omegaMixingLength"]   = None

        elif self.effective_turbulence_model == "komega":
            self.data["kType"]               = self.k_type_label.text()
            self.data["kValue"]              = self.k_value.value()
            self.data["kIntensity"]          = self.k_intensity.value()
            self.data["omegaType"]           = self.omega_type_label.text()
            self.data["omegaValue"]          = self.omega_value.value()
            self.data["omegaMixingLength"]   = self.omega_mixingLength.value()
            # Limpiar ε
            self.data["epsilonType"]         = None
            self.data["epsilonValue"]        = None
            self.data["epsilonMixingLength"] = None

        else:
            # Laminar u otros: limpiar todo
            for fld in ("kType","kValue","kIntensity",
                        "epsilonType","epsilonValue","epsilonMixingLength",
                        "omegaType","omegaValue","omegaMixingLength"):
                self.data[fld] = None

        # Temperatura
        self.data["temperature"] = self.temp_spin.value()

        # Velocidad (solo inlet)
        if self.bc_type == "inlet":
            self.data["velocityType"]  = self.vel_type_combo.currentText()
            self.data["velocityValue"] = self.vel_value.value()
            self.data["velocityInit"]  = self.vel_init.value()

        # Química
        if self.chemistryActive and hasattr(self, "species_widgets"):
            for sp, spin in self.species_widgets.items():
                self.data[f"{sp}_chemType"]  = "fixedValue"
                self.data[f"{sp}_chemValue"] = spin.value()

        self.accept()

    def get_bc_data(self):
        return self.data
