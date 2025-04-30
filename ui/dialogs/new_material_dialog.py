from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QHBoxLayout, QPushButton
)
from PyQt5.QtCore import Qt
from ui.widgets.numeric_line_edit import NumericLineEdit
class NewMaterialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Material")

        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.name_edit = NumericLineEdit()
        form.addRow("Nombre del material:", self.name_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["CH4", "N2", "O2", "CO2", "H2O"])
        form.addRow("Material:", self.type_combo)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.btn_accept = QPushButton("Aceptar")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_accept.clicked.connect(self.accept_changes)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_accept)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

        self.mat_name = None
        self.mat_type = None

    def accept_changes(self):
        self.mat_name = self.name_edit.text().strip()
        self.mat_type = self.type_combo.currentText()

        if not self.mat_name:
            # Nombre vacío no permitido
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "El nombre del material no puede estar vacío.")
            return

        self.accept()

