# ui/dialogs/wall_bc_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox, QHBoxLayout,
    QLabel, QComboBox, QCheckBox, QPushButton, QTabWidget, QWidget
)
from PyQt5.QtCore import Qt
import copy

class FormattedDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def textFromValue(self, value):
        if abs(value) >= 0.01 or value == 0:
            return f"{value:.10f}"
        else:
            return f"{value:.2e}"

class WallBCDialog(QDialog):
    def __init__(self, parent=None, turbulenceModel="laminar", chemistryActive=False, chosen_species=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Wall Boundary Conditions")
        self.turbulenceModel = turbulenceModel

        # Extraer el modelo efectivo: si turbulenceModel es dict, se toma el valor de "model" en minúsculas.
        if isinstance(self.turbulenceModel, dict):
            self.effective_turbulence_model = self.turbulenceModel.get("model", "laminar").lower()
        else:
            self.effective_turbulence_model = self.turbulenceModel.lower()

        self.chemistryActive = chemistryActive
        if chosen_species is None:
            chosen_species = []
        self.chosen_species = chosen_species

        # Datos por defecto
        default_data = {
            "type": "Wall",
            "adiabatic": True,
            "wallTemperature": 300.0,
            "noFriction": True,
            "alphaType": "fixedValue",
            "alphaValue": 1.0,
            "nutType": "fixedValue",
            "nutValue": 1e-5,
            "kType": "fixedValue",
            "kValue": 0.1,
            "epsilonType": "fixedValue",
            "epsilonValue": 10,
            "omegaType": "omegaWallFunction" if self.effective_turbulence_model == "komega" else "fixedValue",
            "omegaValue": 5,
            "temperature": 300.0
        }

        # Si la turbulencia es kOmega, se añaden parámetros adicionales
        if self.effective_turbulence_model == "komega":
            default_data["Cmu"] = 0.09
            default_data["kappa"] = 0.41
            default_data["E"] = 9.8
            default_data["omegaValueOption"] = "$internalField"

        # Añadir datos de química si está activa
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

        self.data = copy.deepcopy(initial_data)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # Pestaña Propiedades
        prop_tab = QWidget()
        p_layout = QFormLayout(prop_tab)

        # Adiabática
        self.adiabatic_checkbox = QCheckBox("Adiabática")
        self.adiabatic_checkbox.setChecked(self.data["adiabatic"])
        self.adiabatic_checkbox.stateChanged.connect(lambda state: self.temp_spin.setVisible(state != Qt.Checked))
        p_layout.addRow(self.adiabatic_checkbox)

        self.temp_spin = FormattedDoubleSpinBox()
        self.temp_spin.setRange(0, 2000)
        self.temp_spin.setDecimals(10)
        self.temp_spin.setValue(self.data["wallTemperature"])
        self.temp_spin.setSuffix(" K")
        self.temp_spin.setVisible(not self.data["adiabatic"])
        p_layout.addRow("Temperatura de la pared:", self.temp_spin)

        # Sin rozamiento
        self.friction_checkbox = QCheckBox("Sin rozamiento")
        self.friction_checkbox.setChecked(self.data["noFriction"])
        p_layout.addRow(self.friction_checkbox)

        # alpha
        self.alpha_combo = QComboBox()
        self.alpha_combo.addItems(["fixedValue", "alphatWallFunction"])
        self.alpha_combo.setCurrentText(self.data["alphaType"])
        # Si se requiere lógica para cambiar la visibilidad, se puede agregar aquí.
        self.alpha_value = FormattedDoubleSpinBox()
        self.alpha_value.setRange(0, 1e5)
        self.alpha_value.setDecimals(10)
        self.alpha_value.setValue(self.data["alphaValue"])
        p_layout.addRow("alpha BC:", self.alpha_combo)
        p_layout.addRow("alpha value:", self.alpha_value)

        # nut
        self.nut_combo = QComboBox()
        self.nut_combo.addItems(["fixedValue", "nutkWallFunction"])
        self.nut_combo.setCurrentText(self.data["nutType"])
        self.nut_value = FormattedDoubleSpinBox()
        self.nut_value.setRange(0, 1e5)
        self.nut_value.setDecimals(10)
        self.nut_value.setValue(self.data["nutValue"])
        p_layout.addRow("nut BC:", self.nut_combo)
        p_layout.addRow("nut value:", self.nut_value)

        # Parámetros de turbulencia
        if self.effective_turbulence_model == "kepsilon":
            # k
            self.k_combo = QComboBox()
            self.k_combo.addItems(["fixedValue", "kqRWallFunction"])
            self.k_combo.setCurrentText(self.data["kType"])
            self.k_value = FormattedDoubleSpinBox()
            self.k_value.setRange(0, 1000)
            self.k_value.setDecimals(10)
            self.k_value.setValue(self.data["kValue"])
            p_layout.addRow("k BC:", self.k_combo)
            p_layout.addRow("k value:", self.k_value)

            # epsilon
            self.epsilon_combo = QComboBox()
            self.epsilon_combo.addItems(["fixedValue", "epsilonWallFunction"])
            self.epsilon_combo.setCurrentText(self.data["epsilonType"])
            self.epsilon_value = FormattedDoubleSpinBox()
            self.epsilon_value.setRange(0, 1000)
            self.epsilon_value.setDecimals(10)
            self.epsilon_value.setValue(self.data["epsilonValue"])
            p_layout.addRow("epsilon BC:", self.epsilon_combo)
            p_layout.addRow("epsilon value:", self.epsilon_value)

            # Para kEpsilon no se usan parámetros de omega.
            self.data["omegaType"] = None
            self.data["omegaValue"] = None
            self.data["omegaMixingLength"] = None

        elif self.effective_turbulence_model == "komega":
            # k
            self.k_combo = QComboBox()
            self.k_combo.addItems(["fixedValue", "kqRWallFunction"])
            self.k_combo.setCurrentText(self.data["kType"])
            self.k_value = FormattedDoubleSpinBox()
            self.k_value.setRange(0, 1000)
            self.k_value.setDecimals(10)
            self.k_value.setValue(self.data["kValue"])
            p_layout.addRow("k BC:", self.k_combo)
            p_layout.addRow("k value:", self.k_value)

            # omega
            self.omega_combo = QComboBox()
            self.omega_combo.addItems(["fixedValue", "omegaWallFunction"])
            self.omega_combo.setCurrentText(self.data["omegaType"])
            self.omega_value = FormattedDoubleSpinBox()
            self.omega_value.setRange(0, 1e5)
            self.omega_value.setDecimals(10)
            self.omega_value.setValue(self.data["omegaValue"])
            p_layout.addRow("omega BC:", self.omega_combo)
            p_layout.addRow("omega value:", self.omega_value)

            # Valores adicionales para omegaWallFunction
            self.cmu_spin = FormattedDoubleSpinBox()
            self.cmu_spin.setRange(0, 10)
            self.cmu_spin.setDecimals(10)
            self.cmu_spin.setValue(self.data.get("Cmu", 0.09))
            self.cmu_spin.setVisible(False)
            p_layout.addRow("Cmu:", self.cmu_spin)

            self.kappa_spin = FormattedDoubleSpinBox()
            self.kappa_spin.setRange(0, 10)
            self.kappa_spin.setDecimals(10)
            self.kappa_spin.setValue(self.data.get("kappa", 0.41))
            self.kappa_spin.setVisible(False)
            p_layout.addRow("kappa:", self.kappa_spin)

            self.e_spin = FormattedDoubleSpinBox()
            self.e_spin.setRange(0, 100)
            self.e_spin.setDecimals(10)
            self.e_spin.setValue(self.data.get("E", 9.8))
            self.e_spin.setVisible(False)
            p_layout.addRow("E:", self.e_spin)

            self.omega_value_combo = QComboBox()
            self.omega_value_combo.addItems(["$internalField"])
            self.omega_value_combo.setCurrentText(self.data.get("omegaValueOption", "$internalField"))
            self.omega_value_combo.setVisible(False)
            p_layout.addRow("value option:", self.omega_value_combo)

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
            self.data["Cmu"] = None
            self.data["kappa"] = None
            self.data["E"] = None
            self.data["omegaValueOption"] = None

        tabs.addTab(prop_tab, "Propiedades")

        # Pestaña de Temperatura General
        temp_gen_tab = QWidget()
        tg_layout = QFormLayout(temp_gen_tab)
        self.temp_spin_general = FormattedDoubleSpinBox()
        self.temp_spin_general.setRange(0, 2000)
        self.temp_spin_general.setDecimals(10)
        self.temp_spin_general.setValue(self.data["temperature"])
        self.temp_spin_general.setSuffix(" K")
        tg_layout.addRow("Temperatura general:", self.temp_spin_general)
        tabs.addTab(temp_gen_tab, "Temperatura General")

        # Pestaña Química
        if self.chemistryActive and self.chosen_species:
            chem_tab = QWidget()
            c_layout = QFormLayout(chem_tab)
            self.species_widgets = {}
            for sp in self.chosen_species:
                sp_type_label = QLabel("inletOutlet (fijo)")
                sp_value_spin = FormattedDoubleSpinBox()
                sp_value_spin.setRange(0, 1e5)
                sp_value_spin.setDecimals(10)
                sp_value_spin.setValue(self.data.get(f"{sp}_chemValue", 0.0))
                h_layout = QHBoxLayout()
                h_layout.addWidget(sp_type_label)
                h_layout.addWidget(sp_value_spin)
                container = QWidget()
                container.setLayout(h_layout)
                c_layout.addRow(f"Fracción molar de {sp} (adim.):", container)
                self.species_widgets[sp] = sp_value_spin
            c_layout.addRow("Total fracción molar:", QLabel(""))  # Se puede agregar lógica para total.
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

        self.setLayout(layout)
        self.adjustSize()

        if self.effective_turbulence_model == "komega":
            self.update_omega_visibility(self.omega_combo.currentText())

    def update_omega_visibility(self, text):
        if self.effective_turbulence_model != "komega":
            return
        if text == "omegaWallFunction":
            self.omega_value.setVisible(False)
            self.cmu_spin.setVisible(True)
            self.kappa_spin.setVisible(True)
            self.e_spin.setVisible(True)
            self.omega_value_combo.setVisible(True)
        else:
            self.omega_value.setVisible(True)
            self.cmu_spin.setVisible(False)
            self.kappa_spin.setVisible(False)
            self.e_spin.setVisible(False)
            self.omega_value_combo.setVisible(False)

    def accept_changes(self):
        self.data["velocityType"] = self.vel_type_combo.currentText()
        self.data["velocityValue"] = self.vel_value.value()
        self.data["velocityInit"] = self.vel_init.value()

        if self.data["velocityType"] in ("flowRateInletVelocity", "inletOutlet", "velocityInlet"):
            self.data["type"] = "Inlet"
        else:
            self.data["type"] = "Inlet"

        if self.effective_turbulence_model == "kepsilon":
            self.data["kType"] = self.k_combo.currentText()
            self.data["kValue"] = self.k_value.value()
            self.data["kIntensity"] = self.k_intensity.value()
            self.data["epsilonType"] = self.epsilon_combo.currentText()
            self.data["epsilonValue"] = self.epsilon_value.value()
            self.data["epsilonMixingLength"] = self.epsilon_mixingLength.value()
            self.data["omegaType"] = None
            self.data["omegaValue"] = None
            self.data["omegaMixingLength"] = None

        elif self.effective_turbulence_model == "komega":
            self.data["kType"] = self.k_combo.currentText()
            self.data["kValue"] = self.k_value.value()
            self.data["kIntensity"] = self.k_intensity.value()
            self.data["omegaType"] = self.omega_combo.currentText()
            if self.omega_combo.currentText() == "omegaWallFunction":
                self.data["omegaValue"] = None
                self.data["Cmu"] = self.cmu_spin.value()
                self.data["kappa"] = self.kappa_spin.value()
                self.data["E"] = self.e_spin.value()
                self.data["omegaValueOption"] = self.omega_value_combo.currentText()
            else:
                self.data["omegaValue"] = self.omega_value.value()
                self.data["Cmu"] = None
                self.data["kappa"] = None
                self.data["E"] = None
                self.data["omegaValueOption"] = None
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
            self.data["Cmu"] = None
            self.data["kappa"] = None
            self.data["E"] = None
            self.data["omegaValueOption"] = None

        self.data["temperature"] = self.temp_spin_general.value()

        if self.chemistryActive and self.chosen_species:
            for sp, spin_box in self.species_widgets.items():
                self.data[f"{sp}_chemType"] = "fixedValue"
                self.data[f"{sp}_chemValue"] = spin_box.value()

        print(f"WallBCDialog: Actualizando {self.data}")
        self.accept()

    def get_bc_data(self):
        return self.data
