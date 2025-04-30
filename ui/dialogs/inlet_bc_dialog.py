# ui/dialogs/inlet_bc_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QTabWidget, QWidget,
    QHBoxLayout, QComboBox, QLabel, QPushButton, QDoubleSpinBox
)
from PyQt5.QtCore import Qt
import copy
import os
import json
from ui.widgets.numeric_line_edit import NumericLineEdit
class ScientificDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDecimals(7)
    def textFromValue(self, value):
        s = f"{value:.7f}"
        s = s.rstrip('0').rstrip('.') if '.' in s else s
        parts = s.split('.')
        if len(parts) == 2 and len(parts[1]) > 2:
            return f"{value:.7e}"
        else:
            return s

class InletBCDialog(QDialog):
    def __init__(self, parent=None, turbulenceModel="laminar", chemistryActive=False, chosen_species=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Inlet Boundary Conditions")
        self.turbulenceModel = turbulenceModel
        # Extraer el modelo efectivo
        if isinstance(self.turbulenceModel, dict):
            self.effective_turbulence_model = self.turbulenceModel.get("model", "laminar").lower()
        else:
            self.effective_turbulence_model = self.turbulenceModel.lower()

        # Leer constant.json para actualizar la información de química
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

        default_data = {
            "velocityType": "flowRateInletVelocity",
            "velocityValue": 1.0,
            "velocityInit": 0.0,
            "kType": "turbulentIntensityKineticEnergyInlet",
            "kValue": 0.1,
            "kIntensity": 0.05,
            "epsilonType": "turbulentMixingLengthFrequencyInlet",
            "epsilonValue": 10.0,
            "epsilonMixingLength": 0.1,
            "omegaType": "turbulentMixingLengthFrequencyInlet",
            "omegaValue": 5.0,
            "omegaMixingLength": 0.1,
            "temperature": 300.0,
        }

        if self.chemistryActive:
            for sp in self.chosen_species:
                default_data[f"{sp}_chemType"] = "fixedValue"
                default_data[f"{sp}_chemValue"] = 0.0

        if initial_data is None:
            initial_data = default_data
        else:
            for key, val in default_data.items():
                if key not in initial_data or initial_data[key] is None:
                    initial_data[key] = val

        self.data = copy.deepcopy(initial_data)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # Pestaña Velocidad
        velocity_tab = QWidget()
        v_layout = QFormLayout(velocity_tab)

        self.vel_type_combo = QComboBox()
        self.vel_type_combo.addItems(["flowRateInletVelocity", "inletOutlet", "velocityInlet"])
        self.vel_type_combo.setCurrentText(self.data["velocityType"])
        self.vel_type_combo.currentTextChanged.connect(lambda text: None)
        v_layout.addRow("Tipo de velocidad:", self.vel_type_combo)

        self.vel_value = ScientificDoubleSpinBox()
        self.vel_value.setRange(0, 1e5)
        self.vel_value.setValue(self.data["velocityValue"])
        v_layout.addRow("Flujo/Vel. de entrada (kg/s o m/s):", self.vel_value)

        self.vel_init = ScientificDoubleSpinBox()
        self.vel_init.setRange(-1e5, 1e5)
        self.vel_init.setValue(self.data["velocityInit"])
        self.vel_init.setSuffix(" m/s (init)")
        v_layout.addRow("Valor inicial (m/s):", self.vel_init)

        # Parámetros de Turbulencia
        if self.effective_turbulence_model == "kepsilon":
            self.k_type_combo = QComboBox()
            self.k_type_combo.addItem("turbulentIntensityKineticEnergyInlet")
            self.k_type_combo.setCurrentText(self.data["kType"])
            self.k_value = ScientificDoubleSpinBox()
            self.k_value.setRange(0, 1000)
            self.k_value.setValue(self.data["kValue"])
            self.k_intensity = ScientificDoubleSpinBox()
            self.k_intensity.setRange(0, 1)
            self.k_intensity.setValue(self.data["kIntensity"])
            v_layout.addRow("k (valor):", self.k_value)
            v_layout.addRow("Intensidad de k:", self.k_intensity)

            self.epsilon_type_combo = QComboBox()
            self.epsilon_type_combo.addItem("turbulentMixingLengthFrequencyInlet")
            self.epsilon_type_combo.setCurrentText(self.data["epsilonType"])
            self.epsilon_value = ScientificDoubleSpinBox()
            self.epsilon_value.setRange(0, 1e5)
            self.epsilon_value.setValue(self.data["epsilonValue"])
            self.epsilon_mixingLength = ScientificDoubleSpinBox()
            self.epsilon_mixingLength.setRange(0, 1000)
            self.epsilon_mixingLength.setValue(self.data["epsilonMixingLength"])
            v_layout.addRow("ε (valor):", self.epsilon_value)
            v_layout.addRow("Longitud de mezcla (m):", self.epsilon_mixingLength)

            self.data["omegaType"] = None
            self.data["omegaValue"] = None
            self.data["omegaMixingLength"] = None

        elif self.effective_turbulence_model == "komega":
            self.k_type_combo = QComboBox()
            self.k_type_combo.addItem("turbulentIntensityKineticEnergyInlet")
            self.k_type_combo.setCurrentText(self.data["kType"])
            self.k_value = ScientificDoubleSpinBox()
            self.k_value.setRange(0, 1000)
            self.k_value.setValue(self.data["kValue"])
            self.k_intensity = ScientificDoubleSpinBox()
            self.k_intensity.setRange(0, 1)
            self.k_intensity.setValue(self.data["kIntensity"])
            v_layout.addRow("k (valor):", self.k_value)

            self.omega_type_combo = QComboBox()
            self.omega_type_combo.addItem("turbulentMixingLengthFrequencyInlet")
            self.omega_type_combo.setCurrentText(self.data["omegaType"])
            self.omega_value = ScientificDoubleSpinBox()
            self.omega_value.setRange(0, 1e5)
            self.omega_value.setValue(self.data["omegaValue"])
            self.omega_mixingLength = ScientificDoubleSpinBox()
            self.omega_mixingLength.setRange(0, 1000)
            self.omega_mixingLength.setValue(self.data["omegaMixingLength"])
            v_layout.addRow("ω (valor):", self.omega_value)

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

        tabs.addTab(velocity_tab, "Velocidad")

        # Pestaña Temperatura
        temp_tab = QWidget()
        t_layout = QFormLayout(temp_tab)
        self.temp_spin = ScientificDoubleSpinBox()
        self.temp_spin.setRange(0, 2000)
        self.temp_spin.setValue(self.data["temperature"])
        self.temp_spin.setSuffix(" K")
        t_layout.addRow("Temperatura (K):", self.temp_spin)
        tabs.addTab(temp_tab, "Temperatura")

        # Pestaña Química
        if self.chemistryActive and self.chosen_species:
            chem_tab = QWidget()
            c_layout = QFormLayout(chem_tab)
            self.species_widgets = {}
            self.total_frac_label = QLabel("")
            self.total_frac_label.setAlignment(Qt.AlignRight)
            for sp in self.chosen_species:
                sp_type_combo = QComboBox()
                sp_type_combo.addItem("fixedValue")
                sp_type_combo.setCurrentText(self.data.get(f"{sp}_chemType", "fixedValue"))
                sp_value_spin = ScientificDoubleSpinBox()
                sp_value_spin.setRange(0, 1)
                sp_value_spin.setSingleStep(0.001)
                sp_value_spin.setValue(self.data.get(f"{sp}_chemValue", 0.0))
                sp_value_spin.valueChanged.connect(self.update_total_fraction)
                h_layout = QHBoxLayout()
                h_layout.addWidget(sp_type_combo)
                h_layout.addWidget(sp_value_spin)
                container = QWidget()
                container.setLayout(h_layout)
                c_layout.addRow(f"Fracción molar de {sp} (adim.):", container)
                self.species_widgets[sp] = sp_value_spin
            c_layout.addRow("Total fracción molar:", self.total_frac_label)
            self.update_total_fraction()
            tabs.addTab(chem_tab, "Química")

        layout.addWidget(tabs)

        btn_layout = QHBoxLayout()
        self.btn_accept = QPushButton("Aceptar")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_accept.clicked.connect(self.accept_changes)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_accept)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def update_total_fraction(self):
        total = 0.0
        for sp, spin_box in self.species_widgets.items():
            total += spin_box.value()
        if total > 1.0:
            self.total_frac_label.setText(f"Advertencia: Total ({total:.3f}) > 1.0")
            self.total_frac_label.setStyleSheet("color: red;")
        else:
            self.total_frac_label.setText(f"Total: {total:.3f}")
            self.total_frac_label.setStyleSheet("color: black;")

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
