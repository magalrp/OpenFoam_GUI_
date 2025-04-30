# ui/dialogs/load_material_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt

from core.materials_library import get_material_properties
from ui.widgets.numeric_line_edit import NumericLineEdit
class LoadMaterialsDialog(QDialog):
    def __init__(self, available_material_types, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Materiales")
        self.setGeometry(300, 300, 400, 300)

        self.selected_materials = []

        # Layout principal
        layout = QVBoxLayout(self)

        # Etiqueta
        label = QLabel("Selecciona los materiales que deseas cargar:")
        layout.addWidget(label)

        # Lista de materiales
        self.material_list = QListWidget()
        self.material_list.setSelectionMode(QListWidget.MultiSelection)
        for mat_type in available_material_types:
            display_text = f"{mat_type}"
            item = QListWidgetItem(display_text)
            # Recuperar propiedades del material
            properties = get_material_properties(mat_type)
            if properties:
                # Crear un diccionario de material
                material = {
                    "name": mat_type,  # Asignar el nombre como el tipo
                    "type": mat_type,
                    "properties": properties
                }
                item.setData(Qt.UserRole, material)  # Almacenar el diccionario completo
                self.material_list.addItem(item)
            else:
                QMessageBox.warning(self, "Error", f"Material inválido en la biblioteca: {mat_type}")
        layout.addWidget(self.material_list)

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_accept = QPushButton("Cargar")
        self.btn_accept.clicked.connect(self.accept_selection)
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_accept)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def accept_selection(self):
        # Obtener los materiales seleccionados
        selected_items = self.material_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Advertencia", "No has seleccionado ningún material.")
            return
        self.selected_materials = [item.data(Qt.UserRole) for item in selected_items]
        self.accept()
