# ui/dialogs/inletOutlet_bc_dialog.py

import os
import json
import copy

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QTabWidget, QWidget,
    QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import Qt

class InletOutletBCDialog(QDialog):
    def __init__(self, parent=None, turbulenceModel="laminar", chemistryActive=False, chosen_species=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("InletOutlet Boundary Conditions")
        self.turbulenceModel = turbulenceModel

        # Convertir turbulenceModel a string efectivo
        if isinstance(self.turbulenceModel, dict):
            self.effective_turbulence_model = self.turbulenceModel.get("model", "laminar").lower()
        else:
            self.effective_turbulence_model = self.turbulenceModel.lower()

        # --- Leer constant.json para actualizar la información de química ---
        constant_path = os.path.join("temp", "constant.json")
        if os.path.exists(constant_path):
            try:
                with open(constant_path, "r") as f:
                    constant_data = json.load(f)
                if constant_data.get("especiesActive", False):
                    self.chemistryActive = True
                    especies_options = constant_data.get("especies_options", {})
                    self.chosen_species = especies_options.get("activeSpecies", [])
                else:
                    self.chemistryActive = False
                    self.chosen_species = []
            except Exception as e:
                print(f"Error al leer constant.json: {e}")
                self.chemistryActive = chemistryActive
                self.chosen_species = chosen_species if chosen_species is not None else []
        else:
            self.chemistryActive = chemistryActive
            self.chosen_species = chosen_species if chosen_species is not None else []

        # Datos por defecto para outlet.
        default_data = {
            "type": "inletOutlet",  # Se fija como outlet mediante inletOutlet.
            "pressureValue": 0.0,   # en Pa
            "kType": "inletOutlet",
            "kValue": 0.1,
            "epsilonType": "inletOutlet",
            "epsilonValue": 10.0,
            "omegaType": "inletOutlet",
            "omegaValue": 5.0,
            "temperature": 300.0
        }

        if self.chemistryActive and self.chosen_species:
            for sp in self.chosen_species:
                default_data[f"{sp}_chemType"] = "inletOutlet"
                default_data[f"{sp}_chemValue"] = 0.0

        if initial_data is None:
            initial_data = default_data
        else:
            for key, val in default_data.items():
                if key not in initial_data or initial_data[key] is None:
                    initial_data[key] = val

        # Crear copia profunda
        self.data = copy.deepcopy(initial_data)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # Pestaña Presión y Turbulencia
        pressure_tab = QWidget()
        p_layout = QFormLayout(pressure_tab)

        # Presión
        self.pressure_value = QDoubleSpinBox()
        self.pressure_value.setRange(-1e5, 1e7)
        self.pressure_value.setValue(self.data["pressureValue"])
        self.pressure_value.setSuffix(" Pa")
        p_layout.addRow("Presión:", self.pressure_value)

        # Parámetros de turbulencia según el modelo
        if self.effective_turbulence_model == "kepsilon":
            k_label = QLabel("k:")
            k_type_label = QLabel("inletOutlet (fijo)")
            self.k_value = QDoubleSpinBox()
            self.k_value.setRange(0, 1000)
            self.k_value.setValue(self.data["kValue"])
            p_layout.addRow(k_label)
            p_layout.addRow("k Tipo:", k_type_label)
            p_layout.addRow("k Valor:", self.k_value)

            epsilon_label = QLabel("ε:")
            epsilon_type_label = QLabel("inletOutlet (fijo)")
            self.epsilon_value = QDoubleSpinBox()
            self.epsilon_value.setRange(0, 1e5)
            self.epsilon_value.setValue(self.data["epsilonValue"])
            p_layout.addRow(epsilon_label)
            p_layout.addRow("ε Tipo:", epsilon_type_label)
            p_layout.addRow("ε Valor:", self.epsilon_value)

            # No se usan omega para kEpsilon
            self.data["omegaType"] = None
            self.data["omegaValue"] = None
            self.data["omegaMixingLength"] = None

        elif self.effective_turbulence_model == "komega":
            k_label = QLabel("k:")
            k_type_label = QLabel("inletOutlet (fijo)")
            self.k_value = QDoubleSpinBox()
            self.k_value.setRange(0, 1000)
            self.k_value.setValue(self.data["kValue"])
            p_layout.addRow(k_label)
            p_layout.addRow("k Tipo:", k_type_label)
            p_layout.addRow("k Valor:", self.k_value)

            omega_label = QLabel("ω:")
            omega_type_label = QLabel("inletOutlet (fijo)")
            self.omega_value = QDoubleSpinBox()
            self.omega_value.setRange(0, 1e5)
            self.omega_value.setValue(self.data["omegaValue"])
            p_layout.addRow(omega_label)
            p_layout.addRow("ω Tipo:", omega_type_label)
            p_layout.addRow("ω Valor:", self.omega_value)

            self.data["epsilonType"] = None
            self.data["epsilonValue"] = None
            self.data["epsilonMixingLength"] = None

        else:
            # Para laminar o modelos no implementados, no se muestran parámetros de turbulencia.
            self.data["kType"] = None
            self.data["kValue"] = None
            self.data["epsilonType"] = None
            self.data["epsilonValue"] = None
            self.data["epsilonMixingLength"] = None
            self.data["omegaType"] = None
            self.data["omegaValue"] = None
            self.data["omegaMixingLength"] = None

        tabs.addTab(pressure_tab, "Presión")

        # Pestaña Temperatura
        temp_tab = QWidget()
        t_layout = QFormLayout(temp_tab)
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0, 2000)
        self.temp_spin.setValue(self.data["temperature"])
        self.temp_spin.setSuffix(" K")
        t_layout.addRow("Temperatura:", self.temp_spin)
        tabs.addTab(temp_tab, "Temperatura")

        # Pestaña Química
        if self.chemistryActive and self.chosen_species:
            chem_tab = QWidget()
            c_layout = QFormLayout(chem_tab)
            self.species_widgets = {}
            for sp in self.chosen_species:
                sp_type_label = QLabel("inletOutlet (fijo)")
                sp_value_spin = QDoubleSpinBox()
                sp_value_spin.setRange(0, 1e5)
                sp_value_spin.setValue(self.data.get(f"{sp}_chemValue", 0.0))
                h_layout = QHBoxLayout()
                h_layout.addWidget(sp_type_label)
                h_layout.addWidget(sp_value_spin)
                container = QWidget()
                container.setLayout(h_layout)
                c_layout.addRow(f"Fracción molar de {sp}:", container)
                self.species_widgets[sp] = sp_value_spin
            tabs.addTab(chem_tab, "Química")

        layout.addWidget(tabs)

        # Botones Aceptar/Cancelar
        btn_layout = QHBoxLayout()
        self.btn_accept = QPushButton("Aceptar")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_accept.clicked.connect(self.accept_changes)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_accept)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def update_velocity_suffix(self, text):
        pass

    def accept_changes(self):
        self.data["velocityType"] = self.vel_type_combo.currentText()
        self.data["velocityValue"] = self.vel_value.value()
        self.data["velocityInit"] = self.vel_init.value()

        if self.data["velocityType"] in ("flowRateInletVelocity", "inletOutlet", "velocityInlet"):
            self.data["type"] = "Inlet"
        else:
            self.data["type"] = "Inlet"

        if self.effective_turbulence_model == "kepsilon":
            self.data["kType"] = self.k_type_combo.currentText()
            self.data["kValue"] = self.k_value.value()
            self.data["kIntensity"] = self.k_intensity.value()
            self.data["epsilonType"] = self.epsilon_type_combo.currentText()
            self.data["epsilonValue"] = self.epsilon_value.value()
            self.data["epsilonMixingLength"] = self.epsilon_mixingLength.value()
            self.data["omegaType"] = None
            self.data["omegaValue"] = None
            self.data["omegaMixingLength"] = None
        elif self.effective_turbulence_model == "komega":
            self.data["kType"] = self.k_type_combo.currentText()
            self.data["kValue"] = self.k_value.value()
            self.data["kIntensity"] = self.k_intensity.value()
            self.data["omegaType"] = self.omega_type_combo.currentText()
            self.data["omegaValue"] = self.omega_value.value()
            self.data["omegaMixingLength"] = self.omega_mixingLength.value()
            self.data["epsilonType"] = None
            self.data["epsilonValue"] = None
            self.data["epsilonMixingLength"] = None
        else:
            self.data["kType"] = None
            self.data["kValue"] = None
            self.data["kIntensity"] = None
            self.data["epsilonType"] = None
            self.data["epsilonValue"] = None
            self.data["epsilonMixingLength"] = None
            self.data["omegaType"] = None
            self.data["omegaValue"] = None
            self.data["omegaMixingLength"] = None

        self.data["temperature"] = self.temp_spin.value()

        if self.chemistryActive and self.chosen_species:
            for sp, spin_box in self.species_widgets.items():
                self.data[f"{sp}_chemType"] = "fixedValue"
                self.data[f"{sp}_chemValue"] = spin_box.value()

        print(f"InletBCDialog: Actualizando {self.data}")
        self.accept()

    def get_bc_data(self):
        return self.data
