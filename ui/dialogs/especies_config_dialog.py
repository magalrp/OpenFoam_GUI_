# ui/dialogs/especies_config_dialog.py
import os
import json

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QButtonGroup,
    QListWidget, QPushButton, QGroupBox, QFormLayout, QComboBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QTextEdit, QSpacerItem,
    QSizePolicy
)
from PyQt5.QtCore import Qt

# Clase para mostrar números con hasta 10 decimales y notación científica si excede 3 decimales
class ScientificDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDecimals(10)
    def textFromValue(self, value):
        # Se formatea con 10 decimales; si la parte decimal (sin ceros finales) tiene más de 3 dígitos, se muestra en notación científica.
        s = f"{value:.10f}"
        s = s.rstrip('0').rstrip('.') if '.' in s else s
        parts = s.split('.')
        if len(parts) == 2 and len(parts[1]) > 3:
            return f"{value:.10e}"
        else:
            return s
    def valueFromText(self, text):
        # Permite interpretar correctamente notación científica
        try:
            return float(text)
        except ValueError:
            return 0.0

class EspeciesConfigDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Especies")

        # Datos por defecto
        default_data = {
            "modelo": "None",  # Opciones: None, transporteEspecies, combustionSinPremezcla, combustionPremezclada
            "activeSpecies": [],
            "reactions": {},
            "combustionModel": "PaSR",
            "combustionParams": {
                "Cmix": 1.0,
                "A": 4.0,
                "B": 0.5,
                "ZFen": 0.2,
                "tauRes": 0.01,
                "reactionRateFactor": 1.0
            },
            "chemSolver": "ODE",  # ODE, chemkin, laminarChemistry, etc.
            "chemSolverParams": {
                "initial_time": 0.001,
                "ode_solver": "seulex",
                "eps": 1.0
            }
        }

        if initial_data is None:
            initial_data = {}
        # Fusionar datos por defecto con los iniciales
        for k, v in default_data.items():
            if k not in initial_data:
                initial_data[k] = v
            else:
                if isinstance(v, dict):
                    for subk, subv in v.items():
                        if subk not in initial_data[k]:
                            initial_data[k][subk] = subv

        self.data = initial_data

        main_layout = QVBoxLayout(self)

        # ---------------------------------------------------------------------
        # 1. Sección "Modelo" (radio buttons)
        # ---------------------------------------------------------------------
        self.modelo_group = QGroupBox("Modelo")
        self.modelo_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        modelo_layout = QVBoxLayout()

        self.modelo_buttongroup = QButtonGroup(self)
        self.radio_none = QRadioButton("None")
        self.radio_transporte = QRadioButton("Transporte de Especies")
        self.radio_comb_sin = QRadioButton("Combustión sin premezcla")
        self.radio_comb_pre = QRadioButton("Combustión premezclada")

        modelo_layout.addWidget(self.radio_none)
        modelo_layout.addWidget(self.radio_transporte)
        modelo_layout.addWidget(self.radio_comb_sin)
        modelo_layout.addWidget(self.radio_comb_pre)

        self.modelo_buttongroup.addButton(self.radio_none, 0)
        self.modelo_buttongroup.addButton(self.radio_transporte, 1)
        self.modelo_buttongroup.addButton(self.radio_comb_sin, 2)
        self.modelo_buttongroup.addButton(self.radio_comb_pre, 3)

        if self.data["modelo"] == "transporteEspecies":
            self.radio_transporte.setChecked(True)
        elif self.data["modelo"] == "combustionSinPremezcla":
            self.radio_comb_sin.setChecked(True)
        elif self.data["modelo"] == "combustionPremezclada":
            self.radio_comb_pre.setChecked(True)
        else:
            self.radio_none.setChecked(True)

        self.modelo_group.setLayout(modelo_layout)
        main_layout.addWidget(self.modelo_group)

        # ---------------------------------------------------------------------
        # 2. Sección "Propiedades de la mezcla"
        # ---------------------------------------------------------------------
        self.props_group = QGroupBox("Propiedades de la mezcla")
        self.props_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        props_layout = QHBoxLayout()

        # Listas de especies
        left_layout = QVBoxLayout()
        left_label = QLabel("Especies inactivas")
        self.list_inactive = QListWidget()
        left_layout.addWidget(left_label)
        left_layout.addWidget(self.list_inactive)

        center_layout = QVBoxLayout()
        center_layout.setSpacing(20)
        center_layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.btn_activate = QPushButton("->")
        self.btn_deactivate = QPushButton("<-")
        center_layout.addWidget(self.btn_activate, alignment=Qt.AlignCenter)
        center_layout.addWidget(self.btn_deactivate, alignment=Qt.AlignCenter)
        center_layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        right_layout = QVBoxLayout()
        right_label = QLabel("Especies activas")
        self.list_active = QListWidget()
        right_layout.addWidget(right_label)
        right_layout.addWidget(self.list_active)

        props_layout.addLayout(left_layout)
        props_layout.addLayout(center_layout)
        props_layout.addLayout(right_layout)
        self.props_group.setLayout(props_layout)
        main_layout.addWidget(self.props_group)

        # Botón "Aceptar" para refrescar reacciones
        props_accept_btn = QPushButton("Aceptar")
        props_accept_btn.clicked.connect(self._refresh_reactions_section)
        main_layout.addWidget(props_accept_btn, alignment=Qt.AlignRight)

        # Cargar biblioteca de especies y llenar listas
        self._load_species_library()
        self._fill_species_lists()

        self.btn_activate.clicked.connect(self.activate_species)
        self.btn_deactivate.clicked.connect(self.deactivate_species)

        # ---------------------------------------------------------------------
        # 3. Sección Reacciones
        # ---------------------------------------------------------------------
        self.react_group = QGroupBox("Reacciones")
        self.react_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        react_layout = QVBoxLayout()
        self.reactions_table = QTableWidget()
        self.reactions_table.setColumnCount(2)
        self.reactions_table.setHorizontalHeaderLabels(["Especie", "Rol"])
        self.reactions_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.reactions_table.horizontalHeader().setStretchLastSection(True)
        self.reactions_table.verticalHeader().setVisible(False)
        self.reactions_table.setMinimumHeight(90)
        react_layout.addWidget(self.reactions_table)
        self.react_group.setLayout(react_layout)
        main_layout.addWidget(self.react_group)
        self._fill_reactions_table()

        # ---------------------------------------------------------------------
        # 4. Sección Interacción Turbulencia-Química
        # ---------------------------------------------------------------------
        self.combust_group = QGroupBox("Interacción Turbulencia-Química")
        self.combust_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        combust_layout = QVBoxLayout()

        self.combo_combustion_model = QComboBox()
        self.combo_combustion_model.addItems(["PaSR", "EddyDissipation", "EDC", "FiniteRate"])
        self.combo_combustion_model.setCurrentText(self.data["combustionModel"])
        self.combo_combustion_model.currentTextChanged.connect(self._on_combustion_model_changed)
        combust_layout.addWidget(self.combo_combustion_model)

        self.combust_desc = QTextEdit()
        self.combust_desc.setReadOnly(True)
        self.combust_desc.setFixedHeight(80)
        combust_layout.addWidget(self.combust_desc)

        self.combust_form = QFormLayout()
        self.label_Cmix = QLabel("Cmix:")
        self.spin_Cmix = ScientificDoubleSpinBox()
        self.spin_Cmix.setRange(0, 1e5)
        self.spin_Cmix.setValue(self.data["combustionParams"].get("Cmix", 1.0) or 1.0)
        self.label_A = QLabel("Constante A:")
        self.spin_A = ScientificDoubleSpinBox()
        self.spin_A.setRange(0, 1e5)
        self.spin_A.setValue(self.data["combustionParams"].get("A", 4.0) or 4.0)
        self.label_B = QLabel("Constante B:")
        self.spin_B = ScientificDoubleSpinBox()
        self.spin_B.setRange(0, 1e5)
        self.spin_B.setValue(self.data["combustionParams"].get("B", 0.5) or 0.5)
        self.label_ZFen = QLabel("ZFen:")
        self.spin_ZFen = ScientificDoubleSpinBox()
        self.spin_ZFen.setRange(0, 1.0)
        self.spin_ZFen.setValue(self.data["combustionParams"].get("ZFen", 0.2) or 0.2)
        self.label_tauRes = QLabel("tauRes:")
        self.spin_tauRes = ScientificDoubleSpinBox()
        self.spin_tauRes.setRange(0, 1e10)
        self.spin_tauRes.setValue(self.data["combustionParams"].get("tauRes", 0.01) or 0.01)
        self.label_rrf = QLabel("Factor vel. reacción:")
        self.spin_rrf = ScientificDoubleSpinBox()
        self.spin_rrf.setRange(0, 1e5)
        self.spin_rrf.setValue(self.data["combustionParams"].get("reactionRateFactor", 1.0) or 1.0)
        self.combust_form.addRow(self.label_Cmix, self.spin_Cmix)
        self.combust_form.addRow(self.label_A, self.spin_A)
        self.combust_form.addRow(self.label_B, self.spin_B)
        self.combust_form.addRow(self.label_ZFen, self.spin_ZFen)
        self.combust_form.addRow(self.label_tauRes, self.spin_tauRes)
        self.combust_form.addRow(self.label_rrf, self.spin_rrf)
        combust_layout.addLayout(self.combust_form)
        self.combust_group.setLayout(combust_layout)
        main_layout.addWidget(self.combust_group)

        self.combustion_explanations = {
            "PaSR": (
                "PaSR (Partial Stirred Reactor)\n"
                "Se usa en turbulencia media/alta, define un factor de mezcla (Cmix). "
                "Casos típicos: reactores turbulentos, llamas difusivas.\n"
                "Parámetro:\n"
                " - Cmix"
            ),
            "EddyDissipation": (
                "Eddy Dissipation Model\n"
                "Se basa en la disipación de vórtices con dos constantes A y B.\n"
                "Casos representativos: grandes quemadores industriales con alto Re.\n"
                "Parámetros:\n"
                " - A, B"
            ),
            "EDC": (
                "Eddy Dissipation Concept\n"
                "Amplía el Eddy Dissipation considerando la microescala de turbulencia.\n"
                "Parámetros:\n"
                " - ZFen (fracción de mezcla fina)\n"
                " - tauRes (tiempo de residencia)"
            ),
            "FiniteRate": (
                "Finite Rate Chemistry\n"
                "Asume cinética detallada y un factor multiplicador.\n"
                "Parámetro:\n"
                " - reactionRateFactor"
            )
        }
        self._on_combustion_model_changed(self.combo_combustion_model.currentText())

        # ---------------------------------------------------------------------
        # 5. Sección Solver Química
        # ---------------------------------------------------------------------
        self.solver_group = QGroupBox("Solver Química")
        self.solver_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        solver_layout = QVBoxLayout()
        self.solver_combo = QComboBox()
        self.solver_options = {
            "ODE": (
                "Resuelve las ecuaciones químicas usando métodos ODE.\n"
                "Típico para reacciones rápidas. Ejemplo: seulex, CVode, RADAU."
            ),
            "chemkin": (
                "Integra con archivos Chemkin para cinética compleja.\n"
                "Requiere archivos .inp y .dat con reacciones y propiedades."
            ),
            "laminarChemistry": (
                "Simplificación de reacciones laminares.\n"
                "Útil para baja reactividad o escalas de tiempo lentas."
            )
        }
        for key in self.solver_options.keys():
            self.solver_combo.addItem(key)
        self.solver_combo.setCurrentText(self.data["chemSolver"])
        self.solver_combo.currentTextChanged.connect(self._on_solver_changed)
        solver_layout.addWidget(self.solver_combo)
        self.solver_desc = QTextEdit()
        self.solver_desc.setReadOnly(True)
        self.solver_desc.setFixedHeight(80)
        solver_layout.addWidget(self.solver_desc)
        self.solver_form = QFormLayout()
        self.label_init_time = QLabel("Tiempo químico inicial:")
        init_time = self.data["chemSolverParams"].get("initial_time")
        if init_time is None:
            init_time = 0.001
        self.spin_init_time = ScientificDoubleSpinBox()
        self.spin_init_time.setRange(0, 1e10)
        self.spin_init_time.setValue(init_time)
        self.label_ode_solver = QLabel("ODE Solver:")
        self.ode_solver_combo = QComboBox()
        self.ode_solver_combo.addItems(["seulex", "CVode", "RADAU", "RK45"])
        ode_solver_val = self.data["chemSolverParams"].get("ode_solver")
        if ode_solver_val is None:
            ode_solver_val = "seulex"
        self.ode_solver_combo.setCurrentText(ode_solver_val)
        self.label_eps = QLabel("eps:")
        eps_val = self.data["chemSolverParams"].get("eps")
        if eps_val is None:
            eps_val = 1.0
        self.spin_eps = ScientificDoubleSpinBox()
        self.spin_eps.setRange(0, 1e10)
        self.spin_eps.setValue(eps_val)
        self.solver_form.addRow(self.label_init_time, self.spin_init_time)
        self.solver_form.addRow(self.label_ode_solver, self.ode_solver_combo)
        self.solver_form.addRow(self.label_eps, self.spin_eps)
        solver_layout.addLayout(self.solver_form)
        self.solver_group.setLayout(solver_layout)
        main_layout.addWidget(self.solver_group)
        self.solver_combo.currentTextChanged.connect(self._on_solver_changed)
        self._on_solver_changed(self.solver_combo.currentText())

        # ---------------------------------------------------------------------
        # Botones Aceptar / Cancelar finales
        # ---------------------------------------------------------------------
        bottom_btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Aceptar")
        btn_cancel = QPushButton("Cancelar")
        bottom_btn_layout.addStretch()
        bottom_btn_layout.addWidget(btn_ok)
        bottom_btn_layout.addWidget(btn_cancel)
        main_layout.addLayout(bottom_btn_layout)
        btn_ok.clicked.connect(self.accept_changes)
        btn_cancel.clicked.connect(self.reject)

        self.setLayout(main_layout)

    def _load_species_library(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        core_dir = os.path.join(script_dir, "..", "..", "core")
        species_file = os.path.join(core_dir, "libreria_especies.json")
        try:
            with open(species_file, "r") as f:
                self.all_species = json.load(f)
        except Exception:
            self.all_species = ["N2", "O2", "CO2", "H2O", "CH4"]

    def _fill_species_lists(self):
        self.list_inactive.clear()
        self.list_active.clear()
        active_set = set(self.data.get("activeSpecies", []))
        for sp in self.all_species:
            if sp in active_set:
                self.list_active.addItem(sp)
            else:
                self.list_inactive.addItem(sp)

    def activate_species(self):
        item = self.list_inactive.currentItem()
        if item:
            sp = item.text()
            self.list_inactive.takeItem(self.list_inactive.row(item))
            self.list_active.addItem(sp)
            if sp not in self.data.get("activeSpecies", []):
                self.data.setdefault("activeSpecies", []).append(sp)

    def deactivate_species(self):
        item = self.list_active.currentItem()
        if item:
            sp = item.text()
            self.list_active.takeItem(self.list_active.row(item))
            self.list_inactive.addItem(sp)
            if sp in self.data.get("activeSpecies", []):
                self.data["activeSpecies"].remove(sp)

    def _refresh_reactions_section(self):
        self.data["activeSpecies"] = []
        for i in range(self.list_active.count()):
            self.data["activeSpecies"].append(self.list_active.item(i).text())
        self._fill_reactions_table()

    def _fill_reactions_table(self):
        actives = self.data.get("activeSpecies", [])
        self.reactions_table.setRowCount(len(actives))
        for i, sp in enumerate(actives):
            item_sp = QTableWidgetItem(sp)
            item_sp.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.reactions_table.setItem(i, 0, item_sp)
            combo = QComboBox()
            combo.addItems(["reactant", "product", "inert"])
            current_role = self.data.get("reactions", {}).get(sp, "inert")
            combo.setCurrentText(current_role)
            combo.currentTextChanged.connect(lambda val, species=sp: self._update_reaction_role(species, val))
            self.reactions_table.setCellWidget(i, 1, combo)

    def _update_reaction_role(self, species, role):
        self.data.setdefault("reactions", {})[species] = role

    def _on_solver_changed(self, solver_name):
        self.data["chemSolver"] = solver_name
        desc = self.solver_options.get(solver_name, "")
        self.solver_desc.setPlainText(desc)
        self.label_init_time.hide()
        self.spin_init_time.hide()
        self.label_ode_solver.hide()
        self.ode_solver_combo.hide()
        self.label_eps.hide()
        self.spin_eps.hide()
        if solver_name == "ODE":
            self.label_init_time.show()
            self.spin_init_time.show()
            self.label_ode_solver.show()
            self.ode_solver_combo.show()
            self.label_eps.show()
            self.spin_eps.show()

    def _on_solver_changed_wrapper(self):
        self._on_solver_changed(self.solver_combo.currentText())

    def _on_combustion_model_changed(self, new_model):
        self.data["combustionModel"] = new_model
        self.combust_desc.setPlainText(self.combustion_explanations.get(new_model, ""))
        self.label_Cmix.hide();  self.spin_Cmix.hide()
        self.label_A.hide();     self.spin_A.hide()
        self.label_B.hide();     self.spin_B.hide()
        self.label_ZFen.hide();  self.spin_ZFen.hide()
        self.label_tauRes.hide(); self.spin_tauRes.hide()
        self.label_rrf.hide();   self.spin_rrf.hide()
        if new_model == "PaSR":
            self.label_Cmix.show()
            self.spin_Cmix.show()
        elif new_model == "EddyDissipation":
            self.label_A.show()
            self.spin_A.show()
            self.label_B.show()
            self.spin_B.show()
        elif new_model == "EDC":
            self.label_ZFen.show()
            self.spin_ZFen.show()
            self.label_tauRes.show()
            self.spin_tauRes.show()
        elif new_model == "FiniteRate":
            self.label_rrf.show()
            self.spin_rrf.show()

    def open_especies_config_dialog(self):
        from PyQt5.QtWidgets import QDialog
        dlg = EspeciesConfigDialog(parent=self, initial_data=self.data.get("especies_options", {}))
        if dlg.exec_() == QDialog.Accepted:
            self.data["especies_options"] = dlg.data

    def _read_constant_json(self):
        constant_path = os.path.join(os.getcwd(), "temp", "constant.json")
        if os.path.exists(constant_path):
            try:
                with open(constant_path, "r") as f:
                    data = json.load(f)
                for key, val in data.items():
                    self.data[key] = val
            except Exception:
                pass

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
        # Modelo
        checked_id = self.modelo_buttongroup.checkedId()
        if checked_id == 1:
            self.data["modelo"] = "transporteEspecies"
        elif checked_id == 2:
            self.data["modelo"] = "combustionSinPremezcla"
        elif checked_id == 3:
            self.data["modelo"] = "combustionPremezclada"
        else:
            self.data["modelo"] = "None"

        # Actualizar activeSpecies
        self.data["activeSpecies"] = []
        for i in range(self.list_active.count()):
            self.data["activeSpecies"].append(self.list_active.item(i).text())

        # Las reacciones se almacenan en self.data["reactions"] (ya se actualizan con los cambios en la tabla)

        # Combustion Model y parámetros
        model = self.combo_combustion_model.currentText()
        self.data["combustionModel"] = model
        cp = self.data["combustionParams"]
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

        # Solver Química
        solver = self.solver_combo.currentText()
        self.data["chemSolver"] = solver
        sp = self.data["chemSolverParams"]
        sp["initial_time"] = self.spin_init_time.value()
        sp["ode_solver"] = self.ode_solver_combo.currentText()
        sp["eps"] = self.spin_eps.value()
        if solver != "ODE":
            sp["initial_time"] = None
            sp["ode_solver"] = None
            sp["eps"] = None

        print(f"EspeciesConfigDialog: Actualizando {self.data}")
        self.accept()

    def get_bc_data(self):
        return self.data

    def _load_species_library(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        core_dir = os.path.join(script_dir, "..", "..", "core")
        species_file = os.path.join(core_dir, "libreria_especies.json")
        try:
            with open(species_file, "r") as f:
                self.all_species = json.load(f)
        except Exception:
            self.all_species = ["N2", "O2", "CO2", "H2O", "CH4"]

    def _fill_species_lists(self):
        self.list_inactive.clear()
        self.list_active.clear()
        active_set = set(self.data.get("activeSpecies", []))
        for sp in self.all_species:
            if sp in active_set:
                self.list_active.addItem(sp)
            else:
                self.list_inactive.addItem(sp)

    def activate_species(self):
        item = self.list_inactive.currentItem()
        if item:
            sp = item.text()
            self.list_inactive.takeItem(self.list_inactive.row(item))
            self.list_active.addItem(sp)
            if sp not in self.data.get("activeSpecies", []):
                self.data.setdefault("activeSpecies", []).append(sp)

    def deactivate_species(self):
        item = self.list_active.currentItem()
        if item:
            sp = item.text()
            self.list_active.takeItem(self.list_active.row(item))
            self.list_inactive.addItem(sp)
            if sp in self.data.get("activeSpecies", []):
                self.data["activeSpecies"].remove(sp)

    def _refresh_reactions_section(self):
        self.data["activeSpecies"] = []
        for i in range(self.list_active.count()):
            self.data["activeSpecies"].append(self.list_active.item(i).text())
        self._fill_reactions_table()

    def _fill_reactions_table(self):
        actives = self.data.get("activeSpecies", [])
        self.reactions_table.setRowCount(len(actives))
        for i, sp in enumerate(actives):
            item_sp = QTableWidgetItem(sp)
            item_sp.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.reactions_table.setItem(i, 0, item_sp)
            combo = QComboBox()
            combo.addItems(["reactant", "product", "inert"])
            current_role = self.data.get("reactions", {}).get(sp, "inert")
            combo.setCurrentText(current_role)
            combo.currentTextChanged.connect(lambda val, species=sp: self._update_reaction_role(species, val))
            self.reactions_table.setCellWidget(i, 1, combo)

    def _update_reaction_role(self, species, role):
        self.data.setdefault("reactions", {})[species] = role

    def _on_solver_changed(self, solver_name):
        self.data["chemSolver"] = solver_name
        desc = self.solver_options.get(solver_name, "")
        self.solver_desc.setPlainText(desc)
        self.label_init_time.hide()
        self.spin_init_time.hide()
        self.label_ode_solver.hide()
        self.ode_solver_combo.hide()
        self.label_eps.hide()
        self.spin_eps.hide()
        if solver_name == "ODE":
            self.label_init_time.show()
            self.spin_init_time.show()
            self.label_ode_solver.show()
            self.ode_solver_combo.show()
            self.label_eps.show()
            self.spin_eps.show()

    def _on_solver_changed_wrapper(self):
        self._on_solver_changed(self.solver_combo.currentText())

    def _on_combustion_model_changed(self, new_model):
        self.data["combustionModel"] = new_model
        self.combust_desc.setPlainText(self.combustion_explanations.get(new_model, ""))
        self.label_Cmix.hide();  self.spin_Cmix.hide()
        self.label_A.hide();     self.spin_A.hide()
        self.label_B.hide();     self.spin_B.hide()
        self.label_ZFen.hide();  self.spin_ZFen.hide()
        self.label_tauRes.hide();self.spin_tauRes.hide()
        self.label_rrf.hide();   self.spin_rrf.hide()
        if new_model == "PaSR":
            self.label_Cmix.show()
            self.spin_Cmix.show()
        elif new_model == "EddyDissipation":
            self.label_A.show()
            self.spin_A.show()
            self.label_B.show()
            self.spin_B.show()
        elif new_model == "EDC":
            self.label_ZFen.show()
            self.spin_ZFen.show()
            self.label_tauRes.show()
            self.spin_tauRes.show()
        elif new_model == "FiniteRate":
            self.label_rrf.show()
            self.spin_rrf.show()

    def open_especies_config_dialog(self):
        from PyQt5.QtWidgets import QDialog
        dlg = EspeciesConfigDialog(parent=self, initial_data=self.data.get("especies_options", {}))
        if dlg.exec_() == QDialog.Accepted:
            self.data["especies_options"] = dlg.data

    def _read_constant_json(self):
        constant_path = os.path.join(os.getcwd(), "temp", "constant.json")
        if os.path.exists(constant_path):
            try:
                with open(constant_path, "r") as f:
                    data = json.load(f)
                for key, val in data.items():
                    self.data[key] = val
            except Exception:
                pass

    def hideEvent(self, event):
        # Si se requiere guardar cambios adicionales, se pueden volcar en self.data aquí
        super().hideEvent(event)

    def accept_changes(self):
        # Actualizar Modelo
        checked_id = self.modelo_buttongroup.checkedId()
        if checked_id == 1:
            self.data["modelo"] = "transporteEspecies"
        elif checked_id == 2:
            self.data["modelo"] = "combustionSinPremezcla"
        elif checked_id == 3:
            self.data["modelo"] = "combustionPremezclada"
        else:
            self.data["modelo"] = "None"
        # Actualizar ActiveSpecies
        self.data["activeSpecies"] = []
        for i in range(self.list_active.count()):
            self.data["activeSpecies"].append(self.list_active.item(i).text())
        # Combustion parameters
        model = self.combo_combustion_model.currentText()
        self.data["combustionModel"] = model
        cp = self.data["combustionParams"]
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
        # Solver química
        solver = self.solver_combo.currentText()
        self.data["chemSolver"] = solver
        sp = self.data["chemSolverParams"]
        sp["initial_time"] = self.spin_init_time.value()
        sp["ode_solver"] = self.ode_solver_combo.currentText()
        sp["eps"] = self.spin_eps.value()
        if solver != "ODE":
            sp["initial_time"] = None
            sp["ode_solver"] = None
            sp["eps"] = None

        print(f"EspeciesConfigDialog: Actualizando {self.data}")
        self.accept()

    def get_bc_data(self):
        return self.data

    def _load_species_library(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        core_dir = os.path.join(script_dir, "..", "..", "core")
        species_file = os.path.join(core_dir, "libreria_especies.json")
        try:
            with open(species_file, "r") as f:
                self.all_species = json.load(f)
        except Exception:
            self.all_species = ["N2", "O2", "CO2", "H2O", "CH4"]

    def _fill_species_lists(self):
        self.list_inactive.clear()
        self.list_active.clear()
        active_set = set(self.data.get("activeSpecies", []))
        for sp in self.all_species:
            if sp in active_set:
                self.list_active.addItem(sp)
            else:
                self.list_inactive.addItem(sp)

    def activate_species(self):
        item = self.list_inactive.currentItem()
        if item:
            sp = item.text()
            self.list_inactive.takeItem(self.list_inactive.row(item))
            self.list_active.addItem(sp)
            if sp not in self.data.get("activeSpecies", []):
                self.data.setdefault("activeSpecies", []).append(sp)

    def deactivate_species(self):
        item = self.list_active.currentItem()
        if item:
            sp = item.text()
            self.list_active.takeItem(self.list_active.row(item))
            self.list_inactive.addItem(sp)
            if sp in self.data.get("activeSpecies", []):
                self.data["activeSpecies"].remove(sp)

    def _refresh_reactions_section(self):
        self.data["activeSpecies"] = []
        for i in range(self.list_active.count()):
            self.data["activeSpecies"].append(self.list_active.item(i).text())
        self._fill_reactions_table()

    def _fill_reactions_table(self):
        actives = self.data.get("activeSpecies", [])
        self.reactions_table.setRowCount(len(actives))
        for i, sp in enumerate(actives):
            item_sp = QTableWidgetItem(sp)
            item_sp.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.reactions_table.setItem(i, 0, item_sp)
            combo = QComboBox()
            combo.addItems(["reactant", "product", "inert"])
            current_role = self.data.get("reactions", {}).get(sp, "inert")
            combo.setCurrentText(current_role)
            combo.currentTextChanged.connect(lambda val, species=sp: self._update_reaction_role(species, val))
            self.reactions_table.setCellWidget(i, 1, combo)

    def _update_reaction_role(self, species, role):
        self.data.setdefault("reactions", {})[species] = role

    def _on_solver_changed(self, solver_name):
        self.data["chemSolver"] = solver_name
        desc = self.solver_options.get(solver_name, "")
        self.solver_desc.setPlainText(desc)
        self.label_init_time.hide()
        self.spin_init_time.hide()
        self.label_ode_solver.hide()
        self.ode_solver_combo.hide()
        self.label_eps.hide()
        self.spin_eps.hide()
        if solver_name == "ODE":
            self.label_init_time.show()
            self.spin_init_time.show()
            self.label_ode_solver.show()
            self.ode_solver_combo.show()
            self.label_eps.show()
            self.spin_eps.show()

    def _on_solver_changed_wrapper(self):
        self._on_solver_changed(self.solver_combo.currentText())

    def _on_combustion_model_changed(self, new_model):
        self.data["combustionModel"] = new_model
        self.combust_desc.setPlainText(self.combustion_explanations.get(new_model, ""))
        self.label_Cmix.hide();  self.spin_Cmix.hide()
        self.label_A.hide();     self.spin_A.hide()
        self.label_B.hide();     self.spin_B.hide()
        self.label_ZFen.hide();  self.spin_ZFen.hide()
        self.label_tauRes.hide(); self.spin_tauRes.hide()
        self.label_rrf.hide();   self.spin_rrf.hide()
        if new_model == "PaSR":
            self.label_Cmix.show()
            self.spin_Cmix.show()
        elif new_model == "EddyDissipation":
            self.label_A.show()
            self.spin_A.show()
            self.label_B.show()
            self.spin_B.show()
        elif new_model == "EDC":
            self.label_ZFen.show()
            self.spin_ZFen.show()
            self.label_tauRes.show()
            self.spin_tauRes.show()
        elif new_model == "FiniteRate":
            self.label_rrf.show()
            self.spin_rrf.show()

    def open_especies_config_dialog(self):
        from PyQt5.QtWidgets import QDialog
        dlg = EspeciesConfigDialog(parent=self, initial_data=self.data.get("especies_options", {}))
        if dlg.exec_() == QDialog.Accepted:
            self.data["especies_options"] = dlg.data

    def _read_constant_json(self):
        constant_path = os.path.join(os.getcwd(), "temp", "constant.json")
        if os.path.exists(constant_path):
            try:
                with open(constant_path, "r") as f:
                    data = json.load(f)
                for key, val in data.items():
                    self.data[key] = val
            except Exception:
                pass

    def hideEvent(self, event):
        super().hideEvent(event)

    def accept_changes(self):
        # Actualizar el modelo seleccionado
        checked_id = self.modelo_buttongroup.checkedId()
        if checked_id == 1:
            self.data["modelo"] = "transporteEspecies"
        elif checked_id == 2:
            self.data["modelo"] = "combustionSinPremezcla"
        elif checked_id == 3:
            self.data["modelo"] = "combustionPremezclada"
        else:
            self.data["modelo"] = "None"

        # Actualizar activeSpecies
        self.data["activeSpecies"] = []
        for i in range(self.list_active.count()):
            self.data["activeSpecies"].append(self.list_active.item(i).text())

        # Las reacciones ya se encuentran en self.data["reactions"]

        # Combustion parameters
        model = self.combo_combustion_model.currentText()
        self.data["combustionModel"] = model
        cp = self.data["combustionParams"]
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

        # Solver Química
        solver = self.solver_combo.currentText()
        self.data["chemSolver"] = solver
        sp = self.data["chemSolverParams"]
        sp["initial_time"] = self.spin_init_time.value()
        sp["ode_solver"] = self.ode_solver_combo.currentText()
        sp["eps"] = self.spin_eps.value()
        if solver != "ODE":
            sp["initial_time"] = None
            sp["ode_solver"] = None
            sp["eps"] = None

        print(f"EspeciesConfigDialog: Actualizando {self.data}")
        self.accept()

    def get_bc_data(self):
        return self.data
