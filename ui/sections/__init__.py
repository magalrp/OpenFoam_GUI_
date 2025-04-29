from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox, QHBoxLayout,
    QLabel, QComboBox, QCheckBox, QPushButton
)
from PyQt5.QtCore import Qt

class WallBCDialog(QDialog):
    def __init__(self, parent=None, turbulenceModel="laminar", initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Wall Boundary Conditions")
        self.turbulenceModel = turbulenceModel

        default_data = {
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
            "omegaType": "fixedValue",
            "omegaValue": 5
        }

        if initial_data is None:
            initial_data = default_data
        else:
            for key, val in default_data.items():
                if key not in initial_data or initial_data[key] is None:
                    initial_data[key] = val

        self.layout = QVBoxLayout(self)

        # Adiabática
        self.adiabatic_checkbox = QCheckBox("Adiabática")
        self.adiabatic_checkbox.setChecked(initial_data["adiabatic"])
        self.adiabatic_checkbox.stateChanged.connect(self.toggle_adiabatic)

        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0, 2000)
        self.temp_spin.setValue(initial_data["wallTemperature"])
        self.temp_spin.setSuffix(" K")
        self.temp_spin.setVisible(not initial_data["adiabatic"])

        # Sin rozamiento
        self.friction_checkbox = QCheckBox("Sin rozamiento")
        self.friction_checkbox.setChecked(initial_data["noFriction"])

        form = QFormLayout()

        # alpha
        self.alpha_combo = QComboBox()
        self.alpha_combo.addItems(["fixedValue", "alphatWallFunction"])
        self.alpha_combo.setCurrentText(initial_data["alphaType"])
        self.alpha_value = QDoubleSpinBox()
        self.alpha_value.setRange(0, 1e5)
        self.alpha_value.setValue(initial_data["alphaValue"])
        form.addRow("alpha BC:", self.alpha_combo)
        form.addRow("alpha value:", self.alpha_value)

        # nut
        self.nut_combo = QComboBox()
        self.nut_combo.addItems(["fixedValue", "nutkWallFunction"])
        self.nut_combo.setCurrentText(initial_data["nutType"])
        self.nut_value = QDoubleSpinBox()
        self.nut_value.setRange(0, 1e5)
        self.nut_value.setValue(initial_data["nutValue"])
        form.addRow("nut BC:", self.nut_combo)
        form.addRow("nut value:", self.nut_value)

        self.k_combo = None
        self.k_value = None
        self.epsilon_combo = None
        self.epsilon_value = None
        self.omega_combo = None
        self.omega_value = None

        if self.turbulenceModel == "kEpsilon":
            # k
            self.k_combo = QComboBox()
            self.k_combo.addItems(["fixedValue", "kqRWallFunction"])
            self.k_combo.setCurrentText(initial_data["kType"])
            self.k_value = QDoubleSpinBox()
            self.k_value.setRange(0, 1000)
            self.k_value.setValue(initial_data["kValue"])
            form.addRow("k BC:", self.k_combo)
            form.addRow("k value:", self.k_value)

            # epsilon
            self.epsilon_combo = QComboBox()
            self.epsilon_combo.addItems(["fixedValue", "epsilonWallFunction"])
            self.epsilon_combo.setCurrentText(initial_data["epsilonType"])
            self.epsilon_value = QDoubleSpinBox()
            self.epsilon_value.setRange(0, 1000)
            self.epsilon_value.setValue(initial_data["epsilonValue"])
            form.addRow("epsilon BC:", self.epsilon_combo)
            form.addRow("epsilon value:", self.epsilon_value)

        elif self.turbulenceModel == "kOmega":
            # k
            self.k_combo = QComboBox()
            self.k_combo.addItems(["fixedValue", "kqRWallFunction"])
            self.k_combo.setCurrentText(initial_data["kType"])
            self.k_value = QDoubleSpinBox()
            self.k_value.setRange(0, 1000)
            self.k_value.setValue(initial_data["kValue"])
            form.addRow("k BC:", self.k_combo)
            form.addRow("k value:", self.k_value)

            # omega
            self.omega_combo = QComboBox()
            self.omega_combo.addItems(["fixedValue", "omegaWallFunction"])
            self.omega_combo.setCurrentText(initial_data["omegaType"])
            self.omega_value = QDoubleSpinBox()
            self.omega_value.setRange(0, 1e5)
            self.omega_value.setValue(initial_data["omegaValue"])
            form.addRow("omega BC:", self.omega_combo)
            form.addRow("omega value:", self.omega_value)

        # Botones Aceptar/Cancelar
        btn_layout = QHBoxLayout()
        self.btn_accept = QPushButton("Aceptar")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_accept.clicked.connect(self.accept_changes)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_accept)
        btn_layout.addWidget(self.btn_cancel)

        self.layout.addWidget(self.adiabatic_checkbox)
        self.layout.addWidget(self.temp_spin)
        self.layout.addWidget(self.friction_checkbox)
        self.layout.addLayout(form)
        self.layout.addLayout(btn_layout)

        self.bc_data = {}

    def toggle_adiabatic(self, state):
        self.temp_spin.setVisible(state != Qt.Checked)

    def accept_changes(self):
        self.bc_data["adiabatic"] = self.adiabatic_checkbox.isChecked()
        if not self.bc_data["adiabatic"]:
            self.bc_data["wallTemperature"] = self.temp_spin.value()
        else:
            self.bc_data["wallTemperature"] = 300.0

        self.bc_data["noFriction"] = self.friction_checkbox.isChecked()

        self.bc_data["alphaType"] = self.alpha_combo.currentText()
        self.bc_data["alphaValue"] = self.alpha_value.value()

        self.bc_data["nutType"] = self.nut_combo.currentText()
        self.bc_data["nutValue"] = self.nut_value.value()

        if self.turbulenceModel == "kEpsilon":
            self.bc_data["kType"] = self.k_combo.currentText()
            self.bc_data["kValue"] = self.k_value.value()
            self.bc_data["epsilonType"] = self.epsilon_combo.currentText()
            self.bc_data["epsilonValue"] = self.epsilon_value.value()
            self.bc_data["omegaType"] = None
            self.bc_data["omegaValue"] = None
        elif self.turbulenceModel == "kOmega":
            self.bc_data["kType"] = self.k_combo.currentText()
            self.bc_data["kValue"] = self.k_value.value()
            self.bc_data["omegaType"] = self.omega_combo.currentText()
            self.bc_data["omegaValue"] = self.omega_value.value()
            self.bc_data["epsilonType"] = None
            self.bc_data["epsilonValue"] = None
        else:
            self.bc_data["kType"] = None
            self.bc_data["kValue"] = None
            self.bc_data["epsilonType"] = None
            self.bc_data["epsilonValue"] = None
            self.bc_data["omegaType"] = None
            self.bc_data["omegaValue"] = None

        self.accept()
