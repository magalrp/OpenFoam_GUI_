# ui/sections/modelo.py
"""
Este archivo pertenece a la ruta: ui/sections/modelo.py

Se ha añadido la lógica para que, cuando se abra/active la sección de Modelos,
se relea el archivo constant.json para ver si 'energy_active' (u otros campos)
ha cambiado externamente, y se actualice el combo de Energía en consecuencia.

Además, se ha actualizado la selección del modelo de turbulencia: primero se elige
la categoría (Laminar, RAS, DNS o LES) y, si se selecciona otra que no sea Laminar,
aparece en horizontal un segundo desplegable con los modelos específicos correspondientes.

Se ha añadido además una nueva sección de configuración de radiación. Si la radiación está activada,
aparecerá un grupo de configuración donde se podrá elegir entre tres modelos de radiación:
"viewFactor", "fvDOM" y "P1". Según el modelo seleccionado, se mostrarán los parámetros relevantes
(con una breve descripción) y se almacenarán en case_config["radiation_options"].

Finalmente, se conserva la sección de Especies (Combustión) para configurar las opciones de química.

Al abandonar la sección (hideEvent), se actualiza automáticamente el archivo constant.json
con la información actual de case_config.
"""

import os
import json

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QMessageBox, QGroupBox, QLineEdit, QTabWidget, QFormLayout, QCheckBox, QDialog
)
from PyQt5.QtCore import Qt

# Diálogos importados
from ui.dialogs.radiation_options_dialog import RadiationOptionsDialog
from ui.dialogs.especies_config_dialog import EspeciesConfigDialog
from ui.dialogs.conf_grav import ConfGravDialog

class Modelo(QWidget):
    def __init__(self, case_config):
        super().__init__()
        self.case_config = case_config
        # Al iniciar, se lee constant.json desde el directorio temp (usando os.getcwd())
        self._read_constant_json()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # TÍTULO Y DESCRIPCIÓN
        title = QLabel("Modelos")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        description = QLabel("En esta sección deben definirse los modelos físicos que se van a considerar durante el estudio.")
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)

        # 1. GRAVEDAD
        gravity_layout = QHBoxLayout()
        gravity_label = QLabel("Gravedad:")
        gravity_layout.addWidget(gravity_label)
        self.gravity_combo = QComboBox()
        self.gravity_combo.setFixedWidth(160)
        self.gravity_combo.addItems(["Desactivada", "Activada"])
        if self.case_config.get("gravity_active", False):
            self.gravity_combo.setCurrentText("Activada")
        else:
            self.gravity_combo.setCurrentText("Desactivada")
        self.gravity_combo.currentTextChanged.connect(self.update_gravity_state)
        gravity_layout.addWidget(self.gravity_combo)
        self.btn_gravity_config = QPushButton("Configurar Gravedad")
        self.btn_gravity_config.clicked.connect(self.open_gravity_config)
        self.btn_gravity_config.setVisible(self.case_config.get("gravity_active", False))
        gravity_layout.addWidget(self.btn_gravity_config)
        layout.addLayout(gravity_layout)

        # 2. ENERGÍA
        energy_layout = QHBoxLayout()
        energy_label = QLabel("Energía:")
        energy_layout.addWidget(energy_label)
        self.energy_combo = QComboBox()
        self.energy_combo.setFixedWidth(160)
        self.energy_combo.addItems(["Desactivada", "Activada"])
        if self.case_config.get("energy_active", False):
            self.energy_combo.setCurrentText("Activada")
        else:
            self.energy_combo.setCurrentText("Desactivada")
        self.energy_combo.currentTextChanged.connect(self.update_energy_state)
        energy_layout.addWidget(self.energy_combo)
        layout.addLayout(energy_layout)

        # 3. TURBULENCIA
        turb_layout = QVBoxLayout()
        turb_header_layout = QHBoxLayout()
        turb_label = QLabel("Turbulencia:")
        turb_header_layout.addWidget(turb_label)
        turb_header_layout.addStretch()
        self.turb_category_combo = QComboBox()
        self.turb_category_combo.setFixedWidth(120)
        self.turb_category_combo.addItems(["Laminar", "RAS", "DNS", "LES"])
        current_model = self.case_config.get("turbulenceModel", "Laminar")
        current_category = "Laminar"
        current_specific = ""
        if isinstance(current_model, dict):
            current_category = current_model.get("category", "Laminar")
            current_specific = current_model.get("model", "")
        else:
            if current_model.lower() == "laminar":
                current_category = "Laminar"
            else:
                current_category = "RAS"
                current_specific = current_model
        self.turb_category_combo.setCurrentText(current_category)
        self.turb_category_combo.currentTextChanged.connect(self.update_turbulence_specific_options)
        turb_header_layout.addWidget(self.turb_category_combo)
        self.turb_specific_combo = QComboBox()
        self.turb_specific_combo.setFixedWidth(200)
        self.populate_turb_specific_combo(current_category, current_specific)
        self.turb_specific_combo.setVisible(current_category != "Laminar")
        self.turb_specific_combo.currentTextChanged.connect(self.update_turbulence_model_combo)
        turb_header_layout.addWidget(self.turb_specific_combo)
        turb_layout.addLayout(turb_header_layout)
        self.turb_desc_label = QLabel("")
        self.turb_desc_label.setStyleSheet("font-style: italic; color: gray;")
        self.turb_desc_label.setWordWrap(True)
        turb_layout.addWidget(self.turb_desc_label)
        layout.addLayout(turb_layout)
        self._show_turbulence_description()

        # 4. RADIACIÓN
        rad_layout = QHBoxLayout()
        rad_label = QLabel("Radiación:")
        rad_layout.addWidget(rad_label)
        self.radiation_combo = QComboBox()
        self.radiation_combo.setFixedWidth(160)
        self.radiation_combo.addItems(["Desactivada", "Activada"])
        if self.case_config.get("radiation_active", False):
            self.radiation_combo.setCurrentText("Activada")
        else:
            self.radiation_combo.setCurrentText("Desactivada")
        self.radiation_combo.currentTextChanged.connect(self.update_radiation_state)
        rad_layout.addWidget(self.radiation_combo)
        self.btn_radiation = QPushButton("Configurar Radiación")
        self.btn_radiation.clicked.connect(self.open_radiation_options_dialog)
        self.btn_radiation.setVisible(self.case_config.get("radiation_active", False))
        rad_layout.addWidget(self.btn_radiation)
        layout.addLayout(rad_layout)

        # Sección avanzada de radiación
        self.radiation_config_box = QGroupBox("Configuración de Radiación")
        self.radiation_config_box.setVisible(self.case_config.get("radiation_active", False))
        rad_conf_layout = QVBoxLayout()
        model_rad_layout = QHBoxLayout()
        model_rad_label = QLabel("Modelo de Radiación:")
        self.rad_model_combo = QComboBox()
        self.rad_model_combo.addItems(["viewFactor", "fvDOM", "P1"])
        rad_options = self.case_config.get("radiation_options", {})
        current_rad_model = rad_options.get("radiationModel", "viewFactor")
        self.rad_model_combo.setCurrentText(current_rad_model)
        self.rad_model_combo.currentTextChanged.connect(self.update_radiation_model_options)
        model_rad_layout.addWidget(model_rad_label)
        model_rad_layout.addWidget(self.rad_model_combo)
        rad_conf_layout.addLayout(model_rad_layout)
        self.rad_desc_label = QLabel("")
        self.rad_desc_label.setStyleSheet("font-style: italic; color: gray;")
        self.rad_desc_label.setWordWrap(True)
        rad_conf_layout.addWidget(self.rad_desc_label)
        self.viewFactor_widget = QGroupBox("Parámetros viewFactor")
        vf_layout = QHBoxLayout()
        vf_layout.addWidget(QLabel("nTheta:"))
        self.vf_nTheta = QComboBox()
        self.vf_nTheta.addItems([str(x) for x in range(4, 21)])
        vf_layout.addWidget(self.vf_nTheta)
        vf_layout.addWidget(QLabel("nPhi:"))
        self.vf_nPhi = QComboBox()
        self.vf_nPhi.addItems([str(x) for x in range(4, 21)])
        vf_layout.addWidget(self.vf_nPhi)
        self.viewFactor_widget.setLayout(vf_layout)
        self.viewFactor_widget.setVisible(False)
        rad_conf_layout.addWidget(self.viewFactor_widget)
        self.fvDOM_widget = QGroupBox("Parámetros fvDOM")
        fv_layout = QHBoxLayout()
        fv_layout.addWidget(QLabel("nTheta:"))
        self.fv_nTheta = QComboBox()
        self.fv_nTheta.addItems([str(x) for x in range(4, 21)])
        fv_layout.addWidget(self.fv_nTheta)
        fv_layout.addWidget(QLabel("nPhi:"))
        self.fv_nPhi = QComboBox()
        self.fv_nPhi.addItems([str(x) for x in range(4, 21)])
        fv_layout.addWidget(self.fv_nPhi)
        fv_layout.addWidget(QLabel("phiRefValue:"))
        self.fv_phiRefValue = QLineEdit("0.0")
        fv_layout.addWidget(self.fv_phiRefValue)
        self.fvDOM_widget.setLayout(fv_layout)
        self.fvDOM_widget.setVisible(False)
        rad_conf_layout.addWidget(self.fvDOM_widget)
        self.p1_widget = QGroupBox("Parámetros P1")
        p1_layout = QHBoxLayout()
        p1_layout.addWidget(QLabel("Absorption Coefficient:"))
        self.p1_absorption = QLineEdit("0.0")
        p1_layout.addWidget(self.p1_absorption)
        self.p1_widget.setLayout(p1_layout)
        self.p1_widget.setVisible(False)
        rad_conf_layout.addWidget(self.p1_widget)
        self.radiation_config_box.setLayout(rad_conf_layout)
        layout.addWidget(self.radiation_config_box)
        self.radiation_combo.currentTextChanged.connect(self.toggle_radiation_config_box)

        # 5. MULTI-FÍSICA
        multiphase_layout = QHBoxLayout()
        multiphase_label = QLabel("Multi-física:")
        multiphase_layout.addWidget(multiphase_label)
        self.multiphase_combo = QComboBox()
        self.multiphase_combo.setFixedWidth(160)
        self.multiphase_combo.addItems(["Desactivada", "Activada"])
        if self.case_config.get("multiPhaseActive", False):
            self.multiphase_combo.setCurrentText("Activada")
        else:
            self.multiphase_combo.setCurrentText("Desactivada")
        self.multiphase_combo.currentTextChanged.connect(self.update_multiphase_state)
        multiphase_layout.addWidget(self.multiphase_combo)
        layout.addLayout(multiphase_layout)

        # 6. ESPECIES (Combustión)
        especies_layout = QHBoxLayout()
        especies_label = QLabel("Especies:")
        especies_layout.addWidget(especies_label)
        self.especies_combo = QComboBox()
        self.especies_combo.setFixedWidth(160)
        self.especies_combo.addItems(["Desactivada", "Activada"])
        if self.case_config.get("especiesActive", False):
            self.especies_combo.setCurrentText("Activada")
        else:
            self.especies_combo.setCurrentText("Desactivada")
        self.especies_combo.currentTextChanged.connect(self.update_especies_state)
        especies_layout.addWidget(self.especies_combo)
        self.btn_especies_config = QPushButton("Configuración")
        self.btn_especies_config.clicked.connect(self.open_especies_config_dialog)
        self.btn_especies_config.setVisible(self.case_config.get("especiesActive", False))
        especies_layout.addWidget(self.btn_especies_config)
        layout.addLayout(especies_layout)

        layout.addStretch()
        self.setLayout(layout)
        self.update_radiation_model_options(self.rad_model_combo.currentText())

    def toggle_radiation_config_box(self, text):
        active = (text == "Activada")
        self.radiation_config_box.setVisible(active)

    def update_radiation_model_options(self, model):
        desc = ""
        self.viewFactor_widget.setVisible(False)
        self.fvDOM_widget.setVisible(False)
        self.p1_widget.setVisible(False)
        if model == "viewFactor":
            desc = ("Modelo viewFactor: utiliza factores de visión para calcular el intercambio radiativo. "
                    "Requiere definir nTheta y nPhi.")
            self.viewFactor_widget.setVisible(True)
        elif model == "fvDOM":
            desc = ("Modelo fvDOM: método de órdenes discretos para radiación. "
                    "Requiere definir nTheta, nPhi y phiRefValue.")
            self.fvDOM_widget.setVisible(True)
        elif model == "P1":
            desc = ("Modelo P1: aproximación de primer orden para radiación, adecuado para medios opacos. "
                    "Requiere definir el coeficiente de absorción.")
            self.p1_widget.setVisible(True)
        self.rad_desc_label.setText(desc)
        rad_options = self.case_config.get("radiation_options", {})
        rad_options["radiationModel"] = model
        self.case_config["radiation_options"] = rad_options

    def update_gravity_state(self, text):
        active = (text == "Activada")
        self.case_config["gravity_active"] = active
        self.btn_gravity_config.setVisible(active)
        if active and "gravity_vector" not in self.case_config:
            self.case_config["gravity_vector"] = [0.0, 0.0, -1.0]

    def update_energy_state(self, text):
        self.case_config["energy_active"] = (text == "Activada")

    def update_turbulence_model_combo(self, new_text):
        specific_model = self.turb_specific_combo.currentText() if self.turb_specific_combo.isVisible() else "Laminar"
        self.case_config["turbulenceModel"] = {"category": self.turb_category_combo.currentText(), "model": specific_model}
        self._show_turbulence_description()

    def update_turbulence_specific_options(self, category):
        self.populate_turb_specific_combo(category, "")
        self.turb_specific_combo.setVisible(category != "Laminar")
        specific_model = self.turb_specific_combo.currentText() if self.turb_specific_combo.isVisible() else "Laminar"
        self.case_config["turbulenceModel"] = {"category": category, "model": specific_model}
        self._show_turbulence_description()

    def populate_turb_specific_combo(self, category, current_specific):
        self.turb_specific_combo.clear()
        if category == "Laminar":
            return
        elif category == "RAS":
            models = ["kEpsilon", "kOmega", "kOmegaSST", "SpalartAllmaras", "RealizablekEpsilon", "RNGkEpsilon"]
        elif category == "DNS":
            models = ["DNS"]
        elif category == "LES":
            models = ["Smagorinsky", "dynSmagorinsky", "oneEqEddy", "dynamicKEqn", "WALE"]
        else:
            models = []
        self.turb_specific_combo.addItems(models)
        if current_specific and current_specific in models:
            self.turb_specific_combo.setCurrentText(current_specific)
        else:
            self.turb_specific_combo.setCurrentIndex(0)

    def _show_turbulence_description(self):
        turbulence_info = self.case_config.get("turbulenceModel", "Laminar")
        if isinstance(turbulence_info, dict):
            category = turbulence_info.get("category", "Laminar")
            model = turbulence_info.get("model", "Laminar")
        else:
            if turbulence_info.lower() == "laminar":
                category = "Laminar"
                model = "Laminar"
            else:
                category = "RAS"
                model = turbulence_info
        desc = ""
        if category == "Laminar":
            desc = "Flujo sin turbulencia, aplicable a bajos números de Reynolds."
        elif category == "RAS":
            desc = f"Modelos RANS: {model}. Se recomienda revisar los parámetros específicos en la documentación de OpenFOAM."
        elif category == "DNS":
            desc = "Direct Numerical Simulation (DNS): Resuelve todas las escalas de turbulencia, muy costoso."
        elif category == "LES":
            desc = f"Large Eddy Simulation (LES): {model}. Para LES se recomienda configurar parámetros adicionales (por ejemplo, coeficiente de Smagorinsky)."
        self.turb_desc_label.setText(desc)

    def update_radiation_state(self, text):
        active = (text == "Activada")
        self.case_config["radiation_active"] = active
        self.btn_radiation.setVisible(active)
        self.radiation_config_box.setVisible(active)

    def update_multiphase_state(self, text):
        active = (text == "Activada")
        self.case_config["multiPhaseActive"] = active
        self.case_config["phase"] = "multiPhase" if active else "singlePhase"

    def update_especies_state(self, text):
        active = (text == "Activada")
        self.case_config["especiesActive"] = active
        self.btn_especies_config.setVisible(active)

    def open_gravity_config(self):
        dlg = ConfGravDialog(parent=self, initial_data={"gravity_vector": self.case_config.get("gravity_vector", [0.0, 0.0, -1.0])})
        if dlg.exec_() == QDialog.Accepted:
            self.case_config["gravity_vector"] = dlg.data["gravity_vector"]

    def open_radiation_options_dialog(self):
        dlg = RadiationOptionsDialog(parent=self, initial_data=self.case_config.get("radiation_options", {}))
        if dlg.exec_() == QDialog.Accepted:
            self.case_config["radiation_options"] = dlg.radiation_data

    def open_especies_config_dialog(self):
        # Ahora se usa self.case_config en lugar de self.data
        dlg = EspeciesConfigDialog(parent=self, initial_data=self.case_config.get("especies_options", {}))
        if dlg.exec_() == QDialog.Accepted:
            self.case_config["especies_options"] = dlg.data

    def _read_constant_json(self):
        # Se utiliza os.getcwd() para obtener la ruta del directorio de trabajo (donde se ejecuta main.py)
        constant_path = os.path.join(os.getcwd(), "temp", "constant.json")
        if os.path.exists(constant_path):
            try:
                with open(constant_path, "r") as f:
                    data = json.load(f)
                # Actualizar case_config con lo leído
                self.case_config.update(data)
            except Exception as e:
                print(f"Error al leer constant.json: {e}")

    def _write_constant_json(self):
        data_to_save = {
            "gravity_active": self.case_config.get("gravity_active", False),
            "gravity_vector": self.case_config.get("gravity_vector", [0.0, 0.0, -1.0]),
            "energy_active": self.case_config.get("energy_active", False),
            "turbulenceModel": self.case_config.get("turbulenceModel", {"category": "Laminar", "model": "Laminar"}),
            "radiation_active": self.case_config.get("radiation_active", False),
            "radiation_options": self.case_config.get("radiation_options", {}),
            "multiPhaseActive": self.case_config.get("multiPhaseActive", False),
            "especiesActive": self.case_config.get("especiesActive", False),
            "phase": self.case_config.get("phase", "singlePhase"),
            "especies_options": self.case_config.get("especies_options", {}),
            "futureExtension": self.case_config.get("futureExtension", None)
        }
        constant_path = os.path.join(os.getcwd(), "temp", "constant.json")
        try:
            with open(constant_path, "w") as f:
                json.dump(data_to_save, f, indent=4)
        except Exception as e:
            print(f"Error al escribir constant.json: {e}")

    def hideEvent(self, event):
        self._write_constant_json()
        super().hideEvent(event)

    def accept_changes(self):
        # Actualizar Modelo
        checked_id = self.modelo_buttongroup.checkedId()
        if checked_id == 1:
            self.case_config["modelo"] = "transporteEspecies"
        elif checked_id == 2:
            self.case_config["modelo"] = "combustionSinPremezcla"
        elif checked_id == 3:
            self.case_config["modelo"] = "combustionPremezclada"
        else:
            self.case_config["modelo"] = "None"

        # Actualizar ActiveSpecies
        active_species = []
        for i in range(self.list_active.count()):
            active_species.append(self.list_active.item(i).text())
        self.case_config["activeSpecies"] = active_species

        # Las reacciones ya se encuentran en self.case_config["reactions"]

        # Combustion parameters
        model = self.combo_combustion_model.currentText()
        self.case_config["combustionModel"] = model
        cp = self.case_config.get("combustionParams", {})
        cp["Cmix"] = self.spin_Cmix.value()
        cp["A"] = self.spin_A.value()
        cp["B"] = self.spin_B.value()
        cp["ZFen"] = self.spin_ZFen.value()
        cp["tauRes"] = self.spin_tauRes.value()
        cp["reactionRateFactor"] = self.spin_rrf.value()
        if model != "PaSR":
            cp["Cmix"] = None
        if model != "EddyDissipation":
            cp["A"] = None
            cp["B"] = None
        if model != "EDC":
            cp["ZFen"] = None
            cp["tauRes"] = None
        if model != "FiniteRate":
            cp["reactionRateFactor"] = None
        self.case_config["combustionParams"] = cp

        # Solver química
        solver = self.solver_combo.currentText()
        self.case_config["chemSolver"] = solver
        sp = self.case_config.get("chemSolverParams", {})
        sp["initial_time"] = self.spin_init_time.value()
        sp["ode_solver"] = self.ode_solver_combo.currentText()
        sp["eps"] = self.spin_eps.value()
        if solver != "ODE":
            sp["initial_time"] = None
            sp["ode_solver"] = None
            sp["eps"] = None
        self.case_config["chemSolverParams"] = sp

        print(f"EspeciesConfigDialog: Actualizando {self.case_config}")
        self.accept()

    def get_bc_data(self):
        return self.case_config
