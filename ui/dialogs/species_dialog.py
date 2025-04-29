from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QGridLayout, QListWidget,
    QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt

class SpeciesSelectionDialog(QDialog):
    def __init__(self, parent=None, available_species=None, chosen_species=None):
        super().__init__(parent)
        self.setWindowTitle("Selección de especies")

        if available_species is None:
            available_species = ["CH4", "O2", "N2", "CO2", "H2O"]
        if chosen_species is None:
            chosen_species = []

        self.available_species = available_species
        self.chosen_species = chosen_species[:]  # copia para no modificar la lista original

        layout = QVBoxLayout(self)

        label = QLabel("Por favor selecciona las especies que quieres que estén involucradas:")
        layout.addWidget(label)

        grid = QGridLayout()

        self.list_left = QListWidget()
        self.list_right = QListWidget()

        # Agregar las especies disponibles no elegidas a la izquierda
        for sp in self.available_species:
            if sp not in self.chosen_species:
                self.list_left.addItem(sp)

        # Agregar las ya elegidas a la derecha
        for sp in self.chosen_species:
            self.list_right.addItem(sp)

        self.btn_to_right = QPushButton("->")
        self.btn_to_left = QPushButton("<-")

        self.btn_to_right.clicked.connect(self.move_to_right)
        self.btn_to_left.clicked.connect(self.move_to_left)

        grid.addWidget(self.list_left, 0, 0, 2, 1)
        grid.addWidget(self.btn_to_right, 0, 1)
        grid.addWidget(self.btn_to_left, 1, 1)
        grid.addWidget(self.list_right, 0, 2, 2, 1)

        layout.addLayout(grid)

        btn_layout = QHBoxLayout()
        self.btn_accept = QPushButton("Aceptar")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_accept.clicked.connect(self.accept_changes)
        self.btn_cancel.clicked.connect(self.reject_changes)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_accept)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.resize(500, 300)

    def move_to_right(self):
        for item in self.list_left.selectedItems():
            self.list_right.addItem(item.text())
            self.list_left.takeItem(self.list_left.row(item))

    def move_to_left(self):
        for item in self.list_right.selectedItems():
            self.list_left.addItem(item.text())
            self.list_right.takeItem(self.list_right.row(item))

    def accept_changes(self):
        self.chosen_species = []
        for i in range(self.list_right.count()):
            self.chosen_species.append(self.list_right.item(i).text())
        self.accept()

    def reject_changes(self):
        self.reject()
