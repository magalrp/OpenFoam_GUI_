from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QLabel,
    QHBoxLayout, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt

class RadiationOptionsDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Opciones de Radiación")

        # Datos por defecto
        default_data = {
            "radiation_model": "none",  # solo "none" por ahora
            "frequency": 10.0
        }

        if initial_data is None:
            initial_data = default_data
        else:
            for key, val in default_data.items():
                if key not in initial_data or initial_data[key] is None:
                    initial_data[key] = val

        self.radiation_data = initial_data

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Modelo de radiación
        self.radiation_model_combo = QComboBox()
        self.radiation_model_combo.addItem("none")  # solo "none" por ahora
        self.radiation_model_combo.setCurrentText(self.radiation_data["radiation_model"])
        self.radiation_model_combo.currentTextChanged.connect(self.update_radiation_fields)
        form.addRow("Modelo de Radiación:", self.radiation_model_combo)

        # Frecuencia
        self.frequency_spin = QDoubleSpinBox()
        self.frequency_spin.setRange(0, 1e5)
        self.frequency_spin.setValue(self.radiation_data["frequency"])
        self.frequency_spin.setSuffix(" ")
        form.addRow("Frecuencia:", self.frequency_spin)

        layout.addLayout(form)

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

    def update_radiation_fields(self, text):
        # En el futuro, si hay más modelos de radiación, aquí se pueden mostrar/ocultar campos
        pass

    def accept_changes(self):
        self.radiation_data["radiation_model"] = self.radiation_model_combo.currentText()
        self.radiation_data["frequency"] = self.frequency_spin.value()
        self.accept()
