from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QLabel,
    QHBoxLayout, QPushButton
)
from PyQt5.QtCore import Qt

class MyDoubleSpinBox(QDoubleSpinBox):
    """
    SpinBox que permite hasta 7 decimales pero sin mostrar ceros de más.
    Si el usuario escribe 1.5, se mostrará '1.5' en lugar de '1.5000000'.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Permitimos hasta 7 decimales y un rango amplio
        self.setDecimals(7)
        self.setRange(0, 1e10)
        self.setSingleStep(0.0000001)

    def textFromValue(self, value: float) -> str:
        """
        Devuelve el texto con hasta 7 decimales,
        eliminando ceros finales innecesarios.
        """
        text = f"{value:.7f}"   # hasta 7 decimales
        text = text.rstrip('0').rstrip('.')  # quita ceros y punto sobrantes
        return text

class ChemicalOptionsDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Opciones Químicas")

        # Valor por defecto ajustado para combustion tipo Arrhenius de metano
        default_data = {
            "solver": "ode",         # Actualmente solo "ode"
            "initial_time": 0.001,   # Escala de tiempo típica (en s)
            "ode_solver": "seulex",  # Actualmente solo "seulex"
            "eps": 1.0               # Sin unidades
        }

        if initial_data is None:
            initial_data = default_data
        else:
            # Completar valores que no estén o sean None
            for k, v in default_data.items():
                if k not in initial_data or initial_data[k] is None:
                    initial_data[k] = v

        self.options_data = initial_data

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Solver
        self.solver_combo = QComboBox()
        self.solver_combo.addItem("ode")
        self.solver_combo.setCurrentText(self.options_data["solver"])
        self.solver_combo.currentTextChanged.connect(self.update_ode_fields)
        form.addRow("Solver:", self.solver_combo)

        # Tiempo inicial químico (usamos MyDoubleSpinBox)
        self.initial_time_spin = MyDoubleSpinBox()
        self.initial_time_spin.setValue(self.options_data["initial_time"])
        form.addRow("Tiempo inicial químico:", self.initial_time_spin)

        # ODE Solver y eps (también con MyDoubleSpinBox para eps)
        self.ode_solver_combo = QComboBox()
        self.ode_solver_combo.addItem("seulex")
        self.ode_solver_combo.setCurrentText(self.options_data["ode_solver"])

        self.eps_spin = MyDoubleSpinBox()
        self.eps_spin.setValue(self.options_data["eps"])

        # En este ejemplo solo existe "ode", por lo que mostramos los campos de ODE.
        if self.options_data["solver"] == "ode":
            form.addRow("ODE Solver:", self.ode_solver_combo)
            form.addRow("eps:", self.eps_spin)

        layout.addLayout(form)

        # Botones Aceptar y Cancelar
        btn_layout = QHBoxLayout()
        self.btn_accept = QPushButton("Aceptar")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_accept.clicked.connect(self.accept_changes)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_accept)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def update_ode_fields(self, text):
        """
        Si más solvers aparecen en el futuro, aquí
        podríamos ocultar/mostrar campos específicos.
        """
        pass

    def accept_changes(self):
        self.options_data["solver"] = self.solver_combo.currentText()
        self.options_data["initial_time"] = self.initial_time_spin.value()

        if self.options_data["solver"] == "ode":
            self.options_data["ode_solver"] = self.ode_solver_combo.currentText()
            self.options_data["eps"] = self.eps_spin.value()
        else:
            self.options_data["ode_solver"] = None
            self.options_data["eps"] = None

        self.accept()
