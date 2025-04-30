from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QListWidget, QLabel
)
from PyQt5.QtCore import Qt
from ui.widgets.numeric_line_edit import NumericLineEdit
class ReactionsSelectionDialog(QDialog):
    def __init__(self, parent=None, available_species=None, reactants=None, products=None, inert_species=None):
        super().__init__(parent)
        self.setWindowTitle("Selección de Reacciones")
        self.resize(800, 600)

        # Inicializar datos
        if available_species is None:
            available_species = []
        if reactants is None:
            reactants = []
        if products is None:
            products = []
        if inert_species is None:
            inert_species = []

        self.available_species = available_species.copy()
        self.reactants = reactants.copy()
        self.products = products.copy()
        self.inert_species = inert_species.copy()

        # Layout principal
        main_layout = QVBoxLayout(self)

        # a. Texto inicial
        info_text = ("En este apartado deben seleccionarse qué especies son reactivos, "
                     "cuáles son reactantes y qué especie es inerte de entre las especies "
                     "que se han seleccionado en el apartado Especies.")
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        # b. Parte inferior dividida en tres secciones
        bottom_layout = QHBoxLayout()

        # I. Ventana izquierda: Especies activas
        self.list_species = QListWidget()
        self.list_species.addItems(self.available_species)
        self.list_species.setSelectionMode(QListWidget.SingleSelection)
        species_layout = QVBoxLayout()
        species_label = QLabel("Especies Activas")
        species_label.setAlignment(Qt.AlignCenter)
        species_layout.addWidget(species_label)
        species_layout.addWidget(self.list_species)
        bottom_layout.addLayout(species_layout)

        # II. Parte central: Flechas para añadir/quitar reactivos, reactantes e inertes
        arrow_layout = QVBoxLayout()
        arrow_layout.setAlignment(Qt.AlignCenter)

        # Botón Añadir Reactivo
        self.btn_add_reactive = QPushButton("Añadir Reactivo →")
        self.btn_add_reactive.setFixedSize(150, 30)
        self.btn_add_reactive.clicked.connect(self.add_reactive)
        arrow_layout.addWidget(self.btn_add_reactive)

        # Botón Quitar Reactivo
        self.btn_remove_reactive = QPushButton("← Quitar Reactivo")
        self.btn_remove_reactive.setFixedSize(150, 30)
        self.btn_remove_reactive.clicked.connect(self.remove_reactive)
        arrow_layout.addWidget(self.btn_remove_reactive)

        # Botón Añadir Reactante
        self.btn_add_reactant = QPushButton("Añadir Reactante →")
        self.btn_add_reactant.setFixedSize(150, 30)
        self.btn_add_reactant.clicked.connect(self.add_reactant)
        arrow_layout.addWidget(self.btn_add_reactant)

        # Botón Quitar Reactante
        self.btn_remove_reactant = QPushButton("← Quitar Reactante")
        self.btn_remove_reactant.setFixedSize(150, 30)
        self.btn_remove_reactant.clicked.connect(self.remove_reactant)
        arrow_layout.addWidget(self.btn_remove_reactant)

        # Botón Añadir Especie Inerte
        self.btn_add_inert = QPushButton("Añadir Especie Inerte →")
        self.btn_add_inert.setFixedSize(150, 30)
        self.btn_add_inert.clicked.connect(self.add_inert)
        arrow_layout.addWidget(self.btn_add_inert)

        # Botón Quitar Especie Inerte
        self.btn_remove_inert = QPushButton("← Quitar Especie Inerte")
        self.btn_remove_inert.setFixedSize(150, 30)
        self.btn_remove_inert.clicked.connect(self.remove_inert)
        arrow_layout.addWidget(self.btn_remove_inert)

        bottom_layout.addLayout(arrow_layout)

        # III. Parte derecha: Reactivos, Reactantes y Especies Inertes
        reactants_products_inert_layout = QVBoxLayout()

        # Reactivos
        self.list_reactants = QListWidget()
        self.list_reactants.addItems(self.reactants)
        self.list_reactants.setSelectionMode(QListWidget.SingleSelection)
        reactants_layout = QVBoxLayout()
        reactants_label = QLabel("Reactivos")
        reactants_label.setAlignment(Qt.AlignCenter)
        reactants_layout.addWidget(reactants_label)
        reactants_layout.addWidget(self.list_reactants)
        reactants_products_inert_layout.addLayout(reactants_layout)

        # Reactantes
        self.list_reactants_output = QListWidget()
        self.list_reactants_output.addItems(self.products)
        self.list_reactants_output.setSelectionMode(QListWidget.SingleSelection)
        reactants_output_layout = QVBoxLayout()
        reactants_output_label = QLabel("Reactantes")
        reactants_output_label.setAlignment(Qt.AlignCenter)
        reactants_output_layout.addWidget(reactants_output_label)
        reactants_output_layout.addWidget(self.list_reactants_output)
        reactants_products_inert_layout.addLayout(reactants_output_layout)

        # Especies Inertes
        self.list_inert = QListWidget()
        self.list_inert.addItems(self.inert_species)
        self.list_inert.setSelectionMode(QListWidget.SingleSelection)
        inert_layout = QVBoxLayout()
        inert_label = QLabel("Especies Inertes")
        inert_label.setAlignment(Qt.AlignCenter)
        inert_layout.addWidget(inert_label)
        inert_layout.addWidget(self.list_inert)
        reactants_products_inert_layout.addLayout(inert_layout)

        bottom_layout.addLayout(reactants_products_inert_layout)

        main_layout.addLayout(bottom_layout)

        # Botones Aceptar/Cancelar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_accept = QPushButton("Aceptar")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_accept.clicked.connect(self.accept_changes)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_accept)
        btn_layout.addWidget(self.btn_cancel)
        main_layout.addLayout(btn_layout)

    def add_reactive(self):
        selected_item = self.list_species.currentItem()
        if selected_item:
            species = selected_item.text()
            if species not in [self.list_reactants.item(i).text() for i in range(self.list_reactants.count())]:
                self.list_reactants.addItem(species)
                self.list_species.takeItem(self.list_species.row(selected_item))
            else:
                QMessageBox.information(self, "Información", f"La especie '{species}' ya está en Reactivos.")

    def remove_reactive(self):
        selected_item = self.list_reactants.currentItem()
        if selected_item:
            species = selected_item.text()
            self.list_reactants.takeItem(self.list_reactants.row(selected_item))
            self.list_species.addItem(species)

    def add_reactant(self):
        selected_item = self.list_species.currentItem()
        if selected_item:
            species = selected_item.text()
            if species not in [self.list_reactants_output.item(i).text() for i in range(self.list_reactants_output.count())]:
                self.list_reactants_output.addItem(species)
                self.list_species.takeItem(self.list_species.row(selected_item))
            else:
                QMessageBox.information(self, "Información", f"La especie '{species}' ya está en Reactantes.")

    def remove_reactant(self):
        selected_item = self.list_reactants_output.currentItem()
        if selected_item:
            species = selected_item.text()
            self.list_reactants_output.takeItem(self.list_reactants_output.row(selected_item))
            self.list_species.addItem(species)

    def add_inert(self):
        selected_item = self.list_species.currentItem()
        if selected_item:
            species = selected_item.text()
            if species not in [self.list_inert.item(i).text() for i in range(self.list_inert.count())]:
                self.list_inert.addItem(species)
                self.list_species.takeItem(self.list_species.row(selected_item))
            else:
                QMessageBox.information(self, "Información", f"La especie '{species}' ya está en Especies Inertes.")

    def remove_inert(self):
        selected_item = self.list_inert.currentItem()
        if selected_item:
            species = selected_item.text()
            self.list_inert.takeItem(self.list_inert.row(selected_item))
            self.list_species.addItem(species)

    def accept_changes(self):
        # Obtener reactivos seleccionados
        reactants = [self.list_reactants.item(i).text() for i in range(self.list_reactants.count())]

        # Obtener reactantes seleccionados
        products = [self.list_reactants_output.item(i).text() for i in range(self.list_reactants_output.count())]

        # Obtener especies inertes seleccionadas
        inert_species = [self.list_inert.item(i).text() for i in range(self.list_inert.count())]

        # Validar que al menos un reactivo y un reactante estén seleccionados
        if not reactants:
            QMessageBox.warning(self, "Advertencia", "Debes seleccionar al menos un reactivo.")
            return
        if not products:
            QMessageBox.warning(self, "Advertencia", "Debes seleccionar al menos un reactante.")
            return

        # Actualizar las listas en el diálogo principal
        self.reactants = reactants
        self.products = products
        self.inert_species = inert_species

        self.accept()
