from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QLabel,
    QHBoxLayout, QPushButton, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from ui.widgets.numeric_line_edit import NumericLineEdit
class CombustionOptionsDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Opciones de Combustión")

        # Para permitir que la ventana se ajuste al contenido
        # (en particular, al cambiar el texto descriptivo).
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # -------------------------------
        # DATOS POR DEFECTO Y MODELOS
        # -------------------------------
        default_data = {
            "combustion_model": "PaSR",  # Por defecto
            "Cmix": 1.0,                 # Parámetro para PaSR
            "A": 4.0,                    # Constante A para EddyDissipation
            "B": 0.5,                    # Constante B para EddyDissipation
            "ZFen": 0.2,                 # Exclusivo de EDC
            "tauRes": 0.01,              # Exclusivo de EDC
            "reactionRateFactor": 1.0    # Exclusivo de FiniteRate
        }

        # Explicación breve de cada modelo
        self.model_explanations = {
            "PaSR": (
                "Partial Stirred Reactor (PaSR). Útil en turbulencia media-alta, "
                "considera un reactor mezclado parcialmente con factor Cmix."
            ),
            "EddyDissipation": (
                "Eddy Dissipation Model. Usa el concepto de disipación de vórtices para "
                "controlar la velocidad de reacción; requiere constantes A y B."
            ),
            "EDC": (
                "Eddy Dissipation Concept (EDC). Modelo más avanzado que el Eddy Dissipation, "
                "puede requerir parámetros como fracciones de mezcla (ZFen) y tiempos característicos (tauRes)."
            ),
            "FiniteRate": (
                "Finite Rate Chemistry. Usa ecuaciones cinéticas detalladas (Arrhenius). "
                "Se puede ajustar con un factor multiplicativo de la velocidad de reacción."
            )
        }

        # Explicación de las variables para el botón de ayuda
        self.model_help_vars = {
            "PaSR": (
                "• Cmix: Coeficiente de mezcla parcial. Define el nivel de mezclado "
                "entre la fase reactiva y los flujos entrantes."
            ),
            "EddyDissipation": (
                "• A: Constante empírica asociada a la tasa de disipación.\n"
                "• B: Constante adicional para el término de la reacción."
            ),
            "EDC": (
                "• ZFen: Fracción de mezcla fina.\n"
                "• tauRes: Tiempo de residencia en las estructuras turbulentas."
            ),
            "FiniteRate": (
                "• reactionRateFactor: Factor multiplicador de la velocidad de reacción "
                "basada en ecuaciones cinéticas (Arrhenius)."
            )
        }

        if initial_data is None:
            initial_data = default_data
        else:
            for key, val in default_data.items():
                if key not in initial_data or initial_data[key] is None:
                    initial_data[key] = val

        self.combustion_data = initial_data

        # -------------------------------
        # LAYOUT PRINCIPAL
        # -------------------------------
        main_layout = QVBoxLayout(self)

        # 1) Barra superior con botón de ayuda (?)
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        self.btn_help = QPushButton("?")
        self.btn_help.setFixedSize(30, 30)
        self.btn_help.clicked.connect(self.show_help_info)
        top_layout.addWidget(self.btn_help)
        main_layout.addLayout(top_layout)

        # 2) Formulario central
        form = QFormLayout()

        # Combobox del modelo
        self.combustion_model_combo = QComboBox()
        self.combustion_model_combo.addItems(["PaSR", "EddyDissipation", "EDC", "FiniteRate"])
        self.combustion_model_combo.setCurrentText(self.combustion_data["combustion_model"])
        self.combustion_model_combo.currentTextChanged.connect(self.update_combustion_fields)
        form.addRow("Modelo de Combustión:", self.combustion_model_combo)

        # Etiqueta de descripción
        self.explanation_label = QLabel()
        self.explanation_label.setWordWrap(True)
        form.addRow("Descripción:", self.explanation_label)

        # -------------------------------
        # CAMPOS PARA CADA MODELO
        # -------------------------------
        # PaSR
        self.label_cmix = QLabel("Cmix:")
        self.spin_cmix = QDoubleSpinBox()
        self.spin_cmix.setRange(0, 1e5)
        self.spin_cmix.setValue(self.combustion_data["Cmix"])

        # EddyDissipation
        self.label_A = QLabel("Constante A:")
        self.spin_A = QDoubleSpinBox()
        self.spin_A.setRange(0, 1e5)
        self.spin_A.setValue(self.combustion_data["A"])

        self.label_B = QLabel("Constante B:")
        self.spin_B = QDoubleSpinBox()
        self.spin_B.setRange(0, 1e5)
        self.spin_B.setValue(self.combustion_data["B"])

        # EDC
        self.label_zfen = QLabel("ZFen:")
        self.spin_zfen = QDoubleSpinBox()
        self.spin_zfen.setRange(0, 1.0)
        self.spin_zfen.setDecimals(4)
        self.spin_zfen.setValue(self.combustion_data["ZFen"])

        self.label_tauRes = QLabel("tauRes (s):")
        self.spin_tauRes = QDoubleSpinBox()
        self.spin_tauRes.setRange(0, 1e5)
        self.spin_tauRes.setValue(self.combustion_data["tauRes"])

        # FiniteRate
        self.label_rrf = QLabel("Factor de velocidad de reacción:")
        self.spin_rrf = QDoubleSpinBox()
        self.spin_rrf.setRange(0, 1e5)
        self.spin_rrf.setValue(self.combustion_data["reactionRateFactor"])

        # Añadirlos al layout, inicialmente ocultos
        form.addRow(self.label_cmix, self.spin_cmix)
        form.addRow(self.label_A, self.spin_A)
        form.addRow(self.label_B, self.spin_B)
        form.addRow(self.label_zfen, self.spin_zfen)
        form.addRow(self.label_tauRes, self.spin_tauRes)
        form.addRow(self.label_rrf, self.spin_rrf)

        main_layout.addLayout(form)

        # 3) Botones Aceptar/Cancelar
        btn_layout = QHBoxLayout()
        self.btn_accept = QPushButton("Aceptar")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_accept.clicked.connect(self.accept_changes)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_accept)
        btn_layout.addWidget(self.btn_cancel)
        main_layout.addLayout(btn_layout)

        # Ajustar campos según el modelo actual
        self.update_combustion_fields(self.combustion_model_combo.currentText())

    # --------------------------------------------------------------------
    # MOSTRAR / OCULTAR CAMPOS SEGÚN EL MODELO
    # --------------------------------------------------------------------
    def update_combustion_fields(self, text):
        """
        Muestra/oculta campos según el modelo y actualiza la descripción.
        Ajusta el tamaño de la ventana a la longitud del texto.
        """
        # Actualizar la descripción principal
        if text in self.model_explanations:
            self.explanation_label.setText(self.model_explanations[text])
        else:
            self.explanation_label.setText("")

        # Ocultar todos los campos primero
        self.label_cmix.hide()
        self.spin_cmix.hide()
        self.label_A.hide()
        self.spin_A.hide()
        self.label_B.hide()
        self.spin_B.hide()
        self.label_zfen.hide()
        self.spin_zfen.hide()
        self.label_tauRes.hide()
        self.spin_tauRes.hide()
        self.label_rrf.hide()
        self.spin_rrf.hide()

        # Mostrar solo los necesarios
        if text == "PaSR":
            self.label_cmix.show()
            self.spin_cmix.show()
        elif text == "EddyDissipation":
            self.label_A.show()
            self.spin_A.show()
            self.label_B.show()
            self.spin_B.show()
        elif text == "EDC":
            self.label_zfen.show()
            self.spin_zfen.show()
            self.label_tauRes.show()
            self.spin_tauRes.show()
        elif text == "FiniteRate":
            self.label_rrf.show()
            self.spin_rrf.show()

        # Ajusta el tamaño de la ventana
        self.adjustSize()
        self.resize(self.minimumSizeHint())

    # --------------------------------------------------------------------
    # BOTÓN DE AYUDA (?)
    # --------------------------------------------------------------------
    def show_help_info(self):
        """
        Muestra un cuadro de diálogo con información adicional sobre
        el modelo y sus variables.
        """
        model = self.combustion_model_combo.currentText()
        desc = self.model_explanations.get(model, "")
        vars_expl = self.model_help_vars.get(model, "")

        help_text = (
            f"<b>Descripción general de {model}:</b><br>{desc}<br><br>"
            f"<b>Parámetros para {model}:</b><br>{vars_expl.replace('\n', '<br>')}"
        )

        # Mostramos un QMessageBox
        QMessageBox.information(
            self,
            "Ayuda - Modelo de Combustión",
            help_text
        )

    # --------------------------------------------------------------------
    # ACEPTAR CAMBIOS
    # --------------------------------------------------------------------
    def accept_changes(self):
        selected_model = self.combustion_model_combo.currentText()
        self.combustion_data["combustion_model"] = selected_model

        # Guardar solo los valores relevantes según el modelo
        if selected_model == "PaSR":
            self.combustion_data["Cmix"] = self.spin_cmix.value()
            self.combustion_data["A"] = None
            self.combustion_data["B"] = None
            self.combustion_data["ZFen"] = None
            self.combustion_data["tauRes"] = None
            self.combustion_data["reactionRateFactor"] = None

        elif selected_model == "EddyDissipation":
            self.combustion_data["A"] = self.spin_A.value()
            self.combustion_data["B"] = self.spin_B.value()
            self.combustion_data["Cmix"] = None
            self.combustion_data["ZFen"] = None
            self.combustion_data["tauRes"] = None
            self.combustion_data["reactionRateFactor"] = None

        elif selected_model == "EDC":
            self.combustion_data["ZFen"] = self.spin_zfen.value()
            self.combustion_data["tauRes"] = self.spin_tauRes.value()
            self.combustion_data["Cmix"] = None
            self.combustion_data["A"] = None
            self.combustion_data["B"] = None
            self.combustion_data["reactionRateFactor"] = None

        elif selected_model == "FiniteRate":
            self.combustion_data["reactionRateFactor"] = self.spin_rrf.value()
            self.combustion_data["Cmix"] = None
            self.combustion_data["A"] = None
            self.combustion_data["B"] = None
            self.combustion_data["ZFen"] = None
            self.combustion_data["tauRes"] = None

        self.accept()
