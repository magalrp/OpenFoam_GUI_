import os
import json

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QPushButton,
    QFormLayout
)
from PyQt5.QtCore import Qt

class ConfGravDialog(QDialog):
    """
    Diálogo para configurar el vector de gravedad (x, y, z).
    Por defecto (0, 0, -1) si no existe en constant.json.
    """
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Gravedad")

        # Datos por defecto
        default_data = {
            "gravity_vector": [0.0, 0.0, -1.0]  # Eje Z hacia -1
        }

        if initial_data is None:
            initial_data = {}

        # Fusionar
        if "gravity_vector" not in initial_data:
            initial_data["gravity_vector"] = default_data["gravity_vector"]

        self.grav_data = initial_data

        main_layout = QVBoxLayout(self)

        info_label = QLabel("Configure el vector de gravedad (x, y, z).")
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        form = QFormLayout()

        self.spin_x = QDoubleSpinBox()
        self.spin_y = QDoubleSpinBox()
        self.spin_z = QDoubleSpinBox()

        # Rango amplio
        self.spin_x.setRange(-1e5, 1e5)
        self.spin_y.setRange(-1e5, 1e5)
        self.spin_z.setRange(-1e5, 1e5)

        vec = self.grav_data["gravity_vector"]  # e.g. [0, 0, -1]
        self.spin_x.setValue(vec[0])
        self.spin_y.setValue(vec[1])
        self.spin_z.setValue(vec[2])

        form.addRow("Componente X:", self.spin_x)
        form.addRow("Componente Y:", self.spin_y)
        form.addRow("Componente Z:", self.spin_z)

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

    def accept_changes(self):
        new_x = self.spin_x.value()
        new_y = self.spin_y.value()
        new_z = self.spin_z.value()

        self.grav_data["gravity_vector"] = [new_x, new_y, new_z]
        self.accept()

    @property
    def data(self):
        return self.grav_data
