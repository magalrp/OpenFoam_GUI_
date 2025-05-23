# ui/dialogs/injection_dialogs/dialog_opt_disperse_fase.py
"""
Diálogo para configurar las opciones de particleTrackProperties para la fase discreta.

Se muestran los siguientes parámetros básicos por defecto:
  - cloudName (nombre de la nube de partículas; valor por defecto "genericCloud")
  - sampleFrequency (valor por defecto 1)
  - maxPositions (valor por defecto 1e6)

Se incluye un checkbox "Opciones avanzadas" que, al activarse, muestra controles adicionales:
  - setFormat (desplegable: vtk, csv)
  - fields (campo de texto para especificar los campos a exportar; si se deja vacío, se exportan todos)
  - maxTracks (valor entero, -1 para sin límite)
"""

import os
import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QCheckBox, QPushButton, QSpinBox, QGroupBox
)
from PyQt5.QtCore import Qt

# IMPORT NECESARIO PARA QUE NumericLineEdit EXISTA
from ui.widgets.numeric_line_edit import NumericLineEdit


class OptDisperseFaseDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Particle Tracking")

        # Valores por defecto
        defaults = {
            "cloudName":       "genericCloud",
            "sampleFrequency": 1,
            "maxPositions":    1e6,
            "setFormat":       "vtk",
            "fields":          "",
            "maxTracks":       -1
        }
        initial_data = initial_data or {}
        for key, val in defaults.items():
            if key not in initial_data or initial_data[key] is None:
                initial_data[key] = val
        self.data = initial_data

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # cloudName
        self.cloud_name_edit = NumericLineEdit()
        self.cloud_name_edit.setText(str(self.data["cloudName"]))
        form.addRow("Nombre de la nube (cloudName):", self.cloud_name_edit)

        # sampleFrequency
        self.sample_freq_edit = QSpinBox()
        self.sample_freq_edit.setRange(1, 10000)
        self.sample_freq_edit.setValue(int(self.data["sampleFrequency"]))
        form.addRow("Frecuencia de muestreo (sampleFrequency):", self.sample_freq_edit)

        # maxPositions
        self.max_positions_edit = NumericLineEdit()
        self.max_positions_edit.setText(f"{self.data['maxPositions']:.0f}")
        form.addRow("Máximo de posiciones (maxPositions):", self.max_positions_edit)

        layout.addLayout(form)

        # Opciones avanzadas
        self.advanced_checkbox = QCheckBox("Opciones avanzadas")
        self.advanced_checkbox.stateChanged.connect(self.toggle_advanced_options)
        layout.addWidget(self.advanced_checkbox)

        self.advanced_widget = QGroupBox("Opciones Avanzadas")
        adv_layout = QFormLayout()

        # setFormat
        self.format_combo = QComboBox()
        self.format_combo.addItems(["vtk", "csv"])
        self.format_combo.setCurrentText(self.data.get("setFormat", "vtk"))
        adv_layout.addRow("Formato (setFormat):", self.format_combo)

        # fields
        self.fields_edit = NumericLineEdit()
        self.fields_edit.setText(self.data.get("fields", ""))
        adv_layout.addRow("Campos (fields):", self.fields_edit)

        # maxTracks
        self.max_tracks_edit = QSpinBox()
        self.max_tracks_edit.setRange(-1, 1000000)
        self.max_tracks_edit.setValue(int(self.data.get("maxTracks", -1)))
        adv_layout.addRow("Máximo de trayectorias (maxTracks):", self.max_tracks_edit)

        self.advanced_widget.setLayout(adv_layout)
        self.advanced_widget.setVisible(False)
        layout.addWidget(self.advanced_widget)

        # Botones
        btn_layout = QHBoxLayout()
        btn_accept = QPushButton("Aceptar")
        btn_cancel = QPushButton("Cancelar")
        btn_accept.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_accept)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def toggle_advanced_options(self, state):
        self.advanced_widget.setVisible(state == Qt.Checked)

    def get_tracking_data(self):
        data = {
            "cloudName":       self.cloud_name_edit.text().strip(),
            "sampleFrequency": self.sample_freq_edit.value(),
            "maxPositions":    float(self.max_positions_edit.text().strip()),
        }
        if self.advanced_checkbox.isChecked():
            data["setFormat"]  = self.format_combo.currentText()
            data["fields"]     = self.fields_edit.text().strip()
            data["maxTracks"]  = self.max_tracks_edit.value()
        else:
            data["setFormat"]  = "vtk"
            data["fields"]     = ""
            data["maxTracks"]  = -1
        return data


if __name__ == "__main__":
    import sys
    dlg = OptDisperseFaseDialog()
    if dlg.exec_() == QDialog.Accepted:
        print(dlg.get_tracking_data())
    sys.exit()
