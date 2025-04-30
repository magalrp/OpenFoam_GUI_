# ui/dialogs/wall_bc_dialog.py

import os
import json
import copy
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QGroupBox,
    QFormLayout, QLabel, QComboBox, QCheckBox,
    QDialogButtonBox
)
from PyQt5.QtCore import Qt
from ui.widgets.numeric_line_edit import NumericLineEdit


class WallBCDialog(QDialog):
    """
    Diálogo para configurar condiciones de contorno de pared.
    Tres pestañas:
      1. Fricción & Turbulencia
      2. Temperatura
      3. Especies (si aplica)
    Sólo aparecen los parámetros del modelo de turbulencia elegido.
    Al aceptar, guarda en temp/boundary_conditions.json.
    """

    def __init__(self, parent=None,
                 turbulenceModel="laminar",
                 chemistryActive=False,
                 chosen_species=None,
                 initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Wall Boundary Conditions")
        self.resize(500, 450)

        # 1) Determinar modelo de turbulencia preferido
        if turbulenceModel:
            self.effective_turbulence_model = (
                turbulenceModel.get("model", "laminar").lower()
                if isinstance(turbulenceModel, dict)
                else turbulenceModel.lower()
            )
        else:
            const_path = os.path.join("temp", "constant.json")
            if os.path.exists(const_path):
                with open(const_path, "r") as f:
                    const = json.load(f)
                self.effective_turbulence_model = (
                    const.get("solverSettings", {})
                         .get("turbulenceModel", "laminar")
                         .lower()
                )
            else:
                self.effective_turbulence_model = "laminar"

        # 2) Química
        self.chemistryActive = chemistryActive
        self.chosen_species = chosen_species or []

        # 3) Valores por defecto
        default = {
            "name":                 (initial_data or {}).get("name", ""),
            "slipType":             "noSlip",
            "slipVelocity":         0.0,
            "useWallFunctions":     (self.effective_turbulence_model != "laminar"),
            "kType":                "fixedValue",
            "kValue":               0.1,
            "kIntensity":           0.0,
            "epsilonType":          "fixedValue",
            "epsilonValue":         10.0,
            "epsilonMixingLength":  0.0,
            "omegaType":            "fixedValue",
            "omegaValue":           5.0,
            "Cmu":                  0.09,
            "kappa":                0.41,
            "E":                    9.8,
            "thermalType":          "fixedValue",
            "wallTemperature":      300.0
        }
        if self.chemistryActive:
            for sp in self.chosen_species:
                default[f"{sp}_chemType"]  = "fixedValue"
                default[f"{sp}_chemValue"] = 0.0

        # 4) Merge con initial_data
        data = copy.deepcopy(initial_data or {})
        for k, v in default.items():
            if k not in data or data[k] is None:
                data[k] = v
        self.data = data

        # 5) Construir y cargar UI
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # === Pestaña 1: Fricción & Turbulencia ===
        tab1 = QWidget()
        v1 = QVBoxLayout(tab1)

        # Deslizamiento de pared
        slip_g = QGroupBox("Deslizamiento de pared")
        f_slip = QFormLayout()
        self.slipType = QComboBox()
        self.slipType.addItems(["noSlip", "slip", "movingWallVelocity"])
        self.slipType.currentTextChanged.connect(self._onSlipChanged)
        f_slip.addRow("Tipo:", self.slipType)
        self.slipVel = NumericLineEdit()
        self.slipVel.setToolTip("Sólo para movingWallVelocity")
        f_slip.addRow("Velocidad [m/s]:", self.slipVel)
        slip_g.setLayout(f_slip)
        v1.addWidget(slip_g)

        # Funciones de pared según modelo
        model = self.effective_turbulence_model
        if model != "laminar":
            title = "Funciones de pared (k-ε)" if model == "kepsilon" else "Funciones de pared (k-ω)"
            turb_g = QGroupBox(title)
            f_t = QFormLayout()

            self.useWF = QCheckBox("Activar funciones de pared")
            self.useWF.stateChanged.connect(self._onUseWFChanged)
            f_t.addRow(self.useWF)

            # k
            self.kType  = QComboBox(); self.kType.addItems(["fixedValue", "kqRWallFunction"])
            self.kValue = NumericLineEdit()
            f_t.addRow("k Tipo:",  self.kType)
            f_t.addRow("k Valor:", self.kValue)

            # Intensidad k
            self.kInt   = NumericLineEdit()
            f_t.addRow("k Intensidad:", self.kInt)

            if model == "kepsilon":
                # ε
                self.epsType  = QComboBox(); self.epsType.addItems(["fixedValue", "epsilonWallFunction"])
                self.epsValue = NumericLineEdit()
                f_t.addRow("ε Tipo:",   self.epsType)
                f_t.addRow("ε Valor:",  self.epsValue)
                # ε mixing length
                self.epsMix   = NumericLineEdit()
                f_t.addRow("ε Long. mezcla:", self.epsMix)
            else:  # komega
                # ω
                self.omegaType  = QComboBox(); self.omegaType.addItems(["fixedValue", "omegaWallFunction"])
                self.omegaType.currentTextChanged.connect(self._onOmegaTypeChanged)
                self.omegaValue = NumericLineEdit()
                f_t.addRow("ω Tipo:",   self.omegaType)
                f_t.addRow("ω Valor:",  self.omegaValue)
                # extras ωWallFunction
                self.cmu    = NumericLineEdit(); f_t.addRow("Cmu:",   self.cmu)
                self.kappa  = NumericLineEdit(); f_t.addRow("kappa:", self.kappa)
                self.E      = NumericLineEdit(); f_t.addRow("E:",     self.E)

            turb_g.setLayout(f_t)
            v1.addWidget(turb_g)
            self.turb_g = turb_g
        else:
            self.turb_g = None

        tabs.addTab(tab1, "Fricción & Turbulencia")

        # === Pestaña 2: Temperatura ===
        tab2 = QWidget()
        f2 = QFormLayout(tab2)
        self.thermalType = QComboBox()
        self.thermalType.addItems([
            "fixedValue", "zeroGradient",
            "externalWallHeatFluxTemperature"
        ])
        self.thermalType.currentTextChanged.connect(self._onThermalChanged)
        f2.addRow("Tipo térmico:", self.thermalType)
        self.tempEdit = NumericLineEdit()
        f2.addRow("Temperatura [K]:", self.tempEdit)
        tabs.addTab(tab2, "Temperatura")

        # === Pestaña 3: Especies ===
        if self.chemistryActive:
            tab3 = QWidget()
            f3 = QFormLayout(tab3)
            self.specEdits = {}
            for sp in self.chosen_species:
                f3.addRow(f"{sp} tipo:", QLabel("fixedValue"))
                e = NumericLineEdit()
                f3.addRow(f"{sp} valor:", e)
                self.specEdits[sp] = e
            tabs.addTab(tab3, "Especies")

        # Botones Aceptar/Cancelar
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._onAccept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        # Inicializar visibilidades
        self._onSlipChanged(self.data["slipType"])
        if self.turb_g:
            wf = self.data["useWallFunctions"]
            self.useWF.setChecked(wf)
            self._onUseWFChanged(wf)
            self._onOmegaTypeChanged(self.data["omegaType"])
        self._onThermalChanged(self.data["thermalType"])

    def _load_data(self):
        d = self.data
        self.slipType.setCurrentText(d["slipType"])
        self.slipVel.setText(str(d["slipVelocity"]))
        if self.turb_g:
            self.kType.setCurrentText(d["kType"])
            self.kValue.setText(str(d["kValue"]))
            self.kInt.setText(str(d["kIntensity"]))
            if self.effective_turbulence_model == "kepsilon":
                self.epsType.setCurrentText(d["epsilonType"])
                self.epsValue.setText(str(d["epsilonValue"]))
                self.epsMix.setText(str(d["epsilonMixingLength"]))
            else:
                self.omegaType.setCurrentText(d["omegaType"])
                self.omegaValue.setText(str(d["omegaValue"]))
                self.cmu.setText(str(d["Cmu"]))
                self.kappa.setText(str(d["kappa"]))
                self.E.setText(str(d["E"]))
        self.thermalType.setCurrentText(d["thermalType"])
        self.tempEdit.setText(str(d["wallTemperature"]))
        if self.chemistryActive:
            for sp, w in self.specEdits.items():
                w.setText(str(d.get(f"{sp}_chemValue", "")))

    def _onSlipChanged(self, text):
        self.slipVel.setEnabled(text == "movingWallVelocity")

    def _onUseWFChanged(self, state):
        if not self.turb_g:
            return
        on = bool(state) and self.effective_turbulence_model != "laminar"
        self.turb_g.setVisible(on)
        # habilitar solo los campos que existen
        for w in self.turb_g.findChildren((QComboBox, NumericLineEdit, QCheckBox)):
            if w is not self.useWF:
                w.setEnabled(on)

    def _onThermalChanged(self, text):
        self.tempEdit.setEnabled(text == "fixedValue")

    def _onOmegaTypeChanged(self, text):
        if self.effective_turbulence_model != "komega":
            return
        show_base = text in ("fixedValue", "omegaWallFunction")
        self.omegaValue.setVisible(show_base)
        show_extras = (text == "omegaWallFunction")
        for w in (self.cmu, self.kappa, self.E):
            w.setVisible(show_extras)

    def _onAccept(self):
        d = self.data
        d.update({
            "slipType":             self.slipType.currentText(),
            "slipVelocity":         float(self.slipVel.text()),
            "useWallFunctions":     (self.turb_g and self.useWF.isChecked()),
            "kType":                self.kType.currentText() if self.turb_g else None,
            "kValue":               float(self.kValue.text()) if self.turb_g else None,
            "kIntensity":           float(self.kInt.text()) if self.turb_g else None,
            "epsilonType":          self.epsType.currentText()
                                     if self.effective_turbulence_model=="kepsilon" else None,
            "epsilonValue":         float(self.epsValue.text())
                                     if self.effective_turbulence_model=="kepsilon" else None,
            "epsilonMixingLength":  float(self.epsMix.text())
                                     if self.effective_turbulence_model=="kepsilon" else None,
            "omegaType":            self.omegaType.currentText()
                                     if self.effective_turbulence_model=="komega" else None,
            "omegaValue":           float(self.omegaValue.text())
                                     if self.effective_turbulence_model=="komega" else None,
            "Cmu":                  float(self.cmu.text())
                                     if (self.effective_turbulence_model=="komega"
                                         and self.omegaType.currentText()=="omegaWallFunction") else None,
            "kappa":                float(self.kappa.text())
                                     if (self.effective_turbulence_model=="komega"
                                         and self.omegaType.currentText()=="omegaWallFunction") else None,
            "E":                    float(self.E.text())
                                     if (self.effective_turbulence_model=="komega"
                                         and self.omegaType.currentText()=="omegaWallFunction") else None,
            "thermalType":          self.thermalType.currentText(),
            "wallTemperature":      float(self.tempEdit.text())
        })
        if self.chemistryActive:
            for sp, w in self.specEdits.items():
                d[f"{sp}_chemType"]  = "fixedValue"
                d[f"{sp}_chemValue"] = float(w.text())

        # Guardar en temp/boundary_conditions.json
        bc_path = os.path.join("temp", "boundary_conditions.json")
        all_bc = {}
        if os.path.exists(bc_path):
            with open(bc_path, "r") as f:
                all_bc = json.load(f)
        name = d.get("name")
        if name:
            all_bc[name] = d
            with open(bc_path, "w") as f:
                json.dump(all_bc, f, indent=2)

        super().accept()

    def get_bc_data(self):
        return self.data
