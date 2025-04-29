# ui/sections/controls.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout,
    QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from core.json_manager import JSONManager

class Controls(QWidget):
    """
    Sección ‘Controls’ para configurar el archivo fvSolution
    según solver, turbulencia, especies y caso.
    Agrupado en secciones y con scroll.
    """
    data_changed = pyqtSignal()

    def __init__(self, case_config):
        super().__init__()
        self.case_config = case_config
        self.json = JSONManager()

        # Cargar o inicializar fvSolution
        stored = self.json.load_section("fvSolution") or {}
        self.case_config.setdefault("fvSolution", {})
        self.case_config["fvSolution"].update(stored)

        # Layout con scroll
        outer_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer_layout.addWidget(scroll)
        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)

        # Título
        title = QLabel("Controls")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight:bold; font-size:16px;")
        layout.addWidget(title)

        # Descripción
        desc = QLabel(
            "Configura solvers, tolerancias, correctores y factores\n"
            "de relajación para fvSolution según tu configuración."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Determinar ecuaciones a incluir
        eqns = ["rho.*", "p_rgh", "U"]
        tur_active = case_config["solverSettings"].get("turbulenceActive", False)
        tur_model  = case_config["solverSettings"].get("turbulenceModel", "")
        if tur_active:
            if "kEpsilon" in tur_model or "k-epsilon" in tur_model:
                eqns += ["k", "epsilon"]
            elif "kOmega" in tur_model or "k-omega" in tur_model:
                eqns += ["k", "omega"]
        chem_active = case_config.get("chemistryActive", False)
        species = case_config.get("chosen_species", []) if chem_active else []

        # Grupo Solvers
        self.gb_solvers = QGroupBox("Solvers")
        form_s = QFormLayout(self.gb_solvers)
        solver_opts   = ["diagonal", "GAMG", "smoothSolver", "PBiCGStab"]
        smoother_opts = ["DICGaussSeidel", "GaussSeidel", "symGaussSeidel"]
        self.eqn_widgets = {}

        for eqn in eqns:
            w = {}
            w["solver"] = QComboBox()
            w["solver"].addItems(solver_opts)
            w["solver"].setCurrentText(
                self.case_config["fvSolution"]
                    .get("solvers", {}).get(eqn, {}).get("solver",
                        "GAMG" if eqn.startswith("p_") else "smoothSolver")
            )
            form_s.addRow(f"{eqn} solver:", w["solver"])

            w["smoother"] = QComboBox()
            w["smoother"].addItems(smoother_opts)
            w["smoother"].setCurrentText(
                self.case_config["fvSolution"]
                    .get("solvers", {}).get(eqn, {}).get("smoother", "DICGaussSeidel")
            )
            form_s.addRow(f"{eqn} smoother:", w["smoother"])

            sb_tol = QDoubleSpinBox(); sb_tol.setDecimals(6); sb_tol.setRange(0,1)
            sb_tol.setValue(
                self.case_config["fvSolution"]
                    .get("solvers", {}).get(eqn, {}).get("tolerance", 1e-6)
            )
            w["tolerance"] = sb_tol
            form_s.addRow(f"{eqn} tolerance:", sb_tol)

            sb_rtol = QDoubleSpinBox(); sb_rtol.setDecimals(4); sb_rtol.setRange(0,1)
            sb_rtol.setValue(
                self.case_config["fvSolution"]
                    .get("solvers", {}).get(eqn, {}).get("relTol", 0.0)
            )
            w["relTol"] = sb_rtol
            form_s.addRow(f"{eqn} relTol:", sb_rtol)

            self.eqn_widgets[eqn] = w

        layout.addWidget(self.gb_solvers)

        # Grupo Physical Models
        gb_phys = QGroupBox("Physical Models")
        phys_layout = QVBoxLayout(gb_phys)

        # potentialFlow
        sub_pot = QGroupBox("potentialFlow")
        form_p = QFormLayout(sub_pot)
        self.nNonOrth = QSpinBox(); self.nNonOrth.setRange(0,50)
        self.nNonOrth.setValue(
            self.case_config["fvSolution"]
                .get("potentialFlow", {}).get("nNonOrthogonalCorrectors", 5)
        )
        form_p.addRow("nNonOrth. Correctors:", self.nNonOrth)
        phys_layout.addWidget(sub_pot)

        # PIMPLE
        self.gb_pimple = QGroupBox("PIMPLE")
        form_pi = QFormLayout(self.gb_pimple)
        self.nOuter = QSpinBox(); self.nOuter.setRange(0,10)
        self.nOuter.setValue(
            self.case_config["fvSolution"]
                .get("PIMPLE", {}).get("nOuterCorrectors", 1)
        )
        form_pi.addRow("nOuterCorrectors:", self.nOuter)

        self.nCorr = QSpinBox(); self.nCorr.setRange(0,10)
        self.nCorr.setValue(
            self.case_config["fvSolution"]
                .get("PIMPLE", {}).get("nCorrectors", 3)
        )
        form_pi.addRow("nCorrectors:", self.nCorr)

        self.nNonOrthP = QSpinBox(); self.nNonOrthP.setRange(0,50)
        self.nNonOrthP.setValue(
            self.case_config["fvSolution"]
                .get("PIMPLE", {}).get("nNonOrthogonalCorrectors", 0)
        )
        form_pi.addRow("nNonOrth. Correctors:", self.nNonOrthP)

        self.momentumPred = QCheckBox()
        self.momentumPred.setChecked(
            self.case_config["fvSolution"]
                .get("PIMPLE", {}).get("momentumPredictor", True)
        )
        form_pi.addRow("momentumPredictor:", self.momentumPred)

        self.pMax = QDoubleSpinBox(); self.pMax.setDecimals(2); self.pMax.setRange(0,10)
        self.pMax.setValue(
            self.case_config["fvSolution"]
                .get("PIMPLE", {}).get("pMaxFactor", 1.5)
        )
        form_pi.addRow("pMaxFactor:", self.pMax)

        self.pMin = QDoubleSpinBox(); self.pMin.setDecimals(2); self.pMin.setRange(0,10)
        self.pMin.setValue(
            self.case_config["fvSolution"]
                .get("PIMPLE", {}).get("pMinFactor", 0.9)
        )
        form_pi.addRow("pMinFactor:", self.pMin)

        phys_layout.addWidget(self.gb_pimple)
        layout.addWidget(gb_phys)

        # Grupo Species Transport
        if species:
            gb_sp = QGroupBox("Species Transport")
            form_sp = QFormLayout(gb_sp)
            self.sp_widgets = {}
            for sp in species:
                combo = QComboBox()
                combo.addItems(["PBiCGStab","diagonal"])
                combo.setCurrentText(
                    self.case_config["fvSolution"]
                        .get("solvers", {}).get(sp, {}).get("solver", "PBiCGStab")
                )
                form_sp.addRow(f"{sp} solver:", combo)
                tol = QDoubleSpinBox(); tol.setDecimals(8); tol.setRange(0,1)
                tol.setValue(
                    self.case_config["fvSolution"]
                        .get("solvers", {}).get(sp, {}).get("tolerance", 1e-8)
                )
                form_sp.addRow(f"{sp} tolerance:", tol)
                self.sp_widgets[sp] = (combo, tol)
            layout.addWidget(gb_sp)

        # Grupo Relaxation Factors
        gb_relax = QGroupBox("Relaxation Factors")
        form_r = QFormLayout(gb_relax)
        self.relax_widgets = {}
        for eqn in eqns + species:
            sb = QDoubleSpinBox(); sb.setDecimals(2); sb.setRange(0,1)
            sb.setValue(
                self.case_config["fvSolution"]
                    .get("relaxationFactors", {})
                    .get("equations", {})
                    .get(eqn, 0.7)
            )
            form_r.addRow(f"{eqn}:", sb)
            self.relax_widgets[eqn] = sb
        layout.addWidget(gb_relax)

        layout.addStretch()

        # Conectar señales
        for w in self.eqn_widgets.values():
            w["solver"].currentTextChanged.connect(self._on_changed)
            w["smoother"].currentTextChanged.connect(self._on_changed)
            w["tolerance"].valueChanged.connect(self._on_changed)
            w["relTol"].valueChanged.connect(self._on_changed)
        self.nNonOrth.valueChanged.connect(self._on_changed)
        for w in (self.nOuter, self.nCorr, self.nNonOrthP,
                  self.momentumPred, self.pMax, self.pMin):
            (w.valueChanged if hasattr(w, 'valueChanged') else w.stateChanged).connect(self._on_changed)
        if species:
            for combo, tol in self.sp_widgets.values():
                combo.currentTextChanged.connect(self._on_changed)
                tol.valueChanged.connect(self._on_changed)
        for sb in self.relax_widgets.values():
            sb.valueChanged.connect(self._on_changed)

        # Mostrar/ocultar PIMPLE según solver
        self._update_pimple_visibility()

    def _update_pimple_visibility(self):
        sol = self.case_config["solverSettings"].get("solver", "")
        self.gb_pimple.setVisible(sol == "pimpleFoam")

    def _on_changed(self, *_):
        solvers = {}
        for eqn, w in self.eqn_widgets.items():
            solvers[eqn] = {
                "solver":   w["solver"].currentText(),
                "smoother": w["smoother"].currentText(),
                "tolerance":w["tolerance"].value(),
                "relTol":   w["relTol"].value()
            }
        if hasattr(self, 'sp_widgets'):
            for sp, (combo, tol) in self.sp_widgets.items():
                solvers[sp] = {
                    "solver": combo.currentText(),
                    "tolerance": tol.value()
                }
        fvSol = {
            "solvers": solvers,
            "potentialFlow": {
                "nNonOrthogonalCorrectors": self.nNonOrth.value()
            },
            "PIMPLE": {
                "nOuterCorrectors":         self.nOuter.value(),
                "nCorrectors":              self.nCorr.value(),
                "nNonOrthogonalCorrectors": self.nNonOrthP.value(),
                "momentumPredictor":        self.momentumPred.isChecked(),
                "pMaxFactor":               self.pMax.value(),
                "pMinFactor":               self.pMin.value()
            },
            "relaxationFactors": {
                "equations": {
                    eqn: sb.value() for eqn, sb in self.relax_widgets.items()
                }
            }
        }
        self.case_config["fvSolution"] = fvSol
        self.json.save_section("fvSolution", fvSol)
        self.data_changed.emit()
