# ui/dialogs/injection_dialogs/type_selection_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt


class TypeSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Tipo de Inyector")

        self.selected_type = None

        layout = QVBoxLayout(self)

        label = QLabel("Seleccione el tipo de inyector que desea añadir:")
        layout.addWidget(label)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["patchInjection", "coneNozzleInjection"])
        layout.addWidget(self.type_combo)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Aceptar")
        btn_cancel = QPushButton("Cancelar")
        btn_ok.clicked.connect(self.accept_selection)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def accept_selection(self):
        self.selected_type = self.type_combo.currentText()
        self.accept()
