# ui/sections/run_calculation.py

import os
import json
import shutil
import subprocess
import logging

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox,
    QFormLayout, QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox,
    QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QLocale

from core.json_manager import JSONManager
from ui.conf.conf_bc import generate_boundary_conditions
from ui.conf.bc.conf_alphat import generate_alphat_file
from ui.conf.conf_constant import generate_constant_files
from ui.conf.constant.conf_reactingCloudproperties import generate_reactingCloudProperties
from ui.conf.constant.conf_combustionProperties import generate_combustionProperties


class RunCalculation(QWidget):
    """
    Sección unificada:
     - Configura controlDict
     - Inicializa carpeta 0, constant, alphat y reactingCloudProperties si procede
     - Genera combustionProperties + librería CHEMKIN
     - Permite lanzar el solver en paralelo
    """
    data_changed = pyqtSignal()

    def __init__(self, case_config):
        super().__init__()
        self.case_config = case_config
        self.root_dir = os.getcwd()
        self.setLocale(QLocale(QLocale.C))

        # Cargar controlDict previo
        jm = JSONManager()
        persisted = jm.load_section("controlDict") or {}
        self.case_config.setdefault("solverSettings", {})
        self.case_config.setdefault("controlDict", {})
        for k, v in persisted.items():
            if k in ("solver", "simulationType"):
                self.case_config["solverSettings"][k] = v
            else:
                # Si existe en JSON pero es None, lo guardamos igual
                self.case_config["controlDict"][k] = v

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Run · Inicialización · Paralelo")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight:bold; font-size:16px;")
        layout.addWidget(title)

        # --- controlDict ---
        form = QFormLayout()

        # Solver
        self.solver_combo = QComboBox()
        self.solvers = ["icoFoam", "simpleFoam", "pisoFoam", "pimpleFoam", "reactingParcelFoam"]
        self.solver_combo.addItems(self.solvers)
        self.solver_combo.setCurrentText(
            self.case_config["solverSettings"].get("solver", self.solvers[0])
        )
        form.addRow("Solver:", self.solver_combo)

        # Simulation Type
        self.sim_combo = QComboBox()
        self.modes = ["Estacionario", "Transitorio"]
        self.sim_combo.addItems(self.modes)
        self.sim_combo.setCurrentText(
            self.case_config["solverSettings"].get("simulationType", self.modes[0])
        )
        form.addRow("Simulation Type:", self.sim_combo)

        # Time control
        self.start_time = QDoubleSpinBox()
        self._config_spin(self.start_time, 0.0, 1e6, 6, "startTime", 0.0)
        form.addRow("Start Time:", self.start_time)

        self.end_time = QDoubleSpinBox()
        self._config_spin(self.end_time, 0.0, 1e6, 6, "endTime", 0.0)
        form.addRow("End Time:", self.end_time)

        self.deltaT = QDoubleSpinBox()
        self._config_spin(self.deltaT, 1e-6, 1e6, 6, "deltaT", 0.001)
        form.addRow("Δt:", self.deltaT)

        self.adapt_dt = QCheckBox()
        self.adapt_dt.setChecked(self.case_config["controlDict"].get("adjustTimeStep", False))
        form.addRow("Adjust Δt:", self.adapt_dt)

        self.maxCo = QDoubleSpinBox()
        self._config_spin(self.maxCo, 0.0, 10.0, 6, "maxCo", 1.0)
        form.addRow("Max Courant:", self.maxCo)

        self.maxDeltaT = QDoubleSpinBox()
        self._config_spin(self.maxDeltaT, 1e-6, 1e6, 6, "maxDeltaT", 0.0)
        form.addRow("Max Δt:", self.maxDeltaT)

        layout.addLayout(form)

        # --- PIMPLE/PISO Controls ---
        self.pimple_group = QGroupBox("PIMPLE / PISO Controls")
        pform = QFormLayout(self.pimple_group)

        outer = self.case_config["controlDict"].get("nOuterCorrectors")
        if outer is None:
            outer = 2
        self.nOuterCorrectors = QSpinBox()
        self.nOuterCorrectors.setRange(1, 100)
        self.nOuterCorrectors.setValue(outer)
        pform.addRow("Outer Correctors:", self.nOuterCorrectors)

        inner = self.case_config["controlDict"].get("nInnerIterations")
        if inner is None:
            inner = 1
        self.nInnerIterations = QSpinBox()
        self.nInnerIterations.setRange(1, 100)
        self.nInnerIterations.setValue(inner)
        pform.addRow("Inner Iterations:", self.nInnerIterations)

        layout.addWidget(self.pimple_group)

        # --- Output Control ---
        oform = QFormLayout()
        self.write_control = QComboBox()
        self.write_control.addItems(["timeStep", "runTime", "clockTime"])
        self.write_control.setCurrentText(
            self.case_config["controlDict"].get("writeControl", "timeStep")
        )
        oform.addRow("Write Control:", self.write_control)

        self.write_interval = QDoubleSpinBox()
        self._config_spin(self.write_interval, 0.0, 1e6, 6, "writeInterval", 1.0)
        oform.addRow("Write Interval:", self.write_interval)

        self.write_format = QComboBox()
        self.write_format.addItems(["ascii", "binary", "compressed"])
        self.write_format.setCurrentText(
            self.case_config["controlDict"].get("writeFormat", "ascii")
        )
        oform.addRow("Write Format:", self.write_format)

        self.write_precision = QSpinBox()
        self.write_precision.setRange(0, 16)
        self.write_precision.setValue(
            self.case_config["controlDict"].get("writePrecision", 6)
        )
        oform.addRow("Write Precision:", self.write_precision)

        self.write_compression = QCheckBox()
        self.write_compression.setChecked(
            self.case_config["controlDict"].get("writeCompression", False)
        )
        oform.addRow("Write Compression:", self.write_compression)

        layout.addLayout(oform)

        # Conexiones para auto-guardar
        self._connect_control_dict_signals()
        self._update_visibility(self.sim_combo.currentText())
        self._update_pimple(self.solver_combo.currentText())

        # --- Botón de Inicialización ---
        init_btn = QPushButton("Inicializar Caso")
        init_btn.clicked.connect(self._on_initialize)
        layout.addWidget(init_btn)

        # --- Sección Paralelización ---
        par_group = QGroupBox("Cálculo en Paralelo")
        parform = QFormLayout(par_group)

        self.nproc_spin = QSpinBox()
        self.nproc_spin.setRange(1, 1024)
        self.nproc_spin.setValue(4)
        parform.addRow("Procesadores:", self.nproc_spin)

        self.decomp_combo = QComboBox()
        self.decomp_combo.addItems(["simple", "hierarchical", "scotch", "metis", "manual"])
        parform.addRow("Método decomp.:", self.decomp_combo)

        self.decomp_desc = QLabel()
        self.decomp_desc.setWordWrap(True)
        parform.addRow("Descripción:", self.decomp_desc)

        layout.addWidget(par_group)

        self.decomp_combo.currentTextChanged.connect(
            lambda m: self._update_decomp_desc(m)
        )
        self._update_decomp_desc(self.decomp_combo.currentText())

        run_btn = QPushButton("Ejecutar en Paralelo")
        run_btn.clicked.connect(self._on_run_parallel)
        layout.addWidget(run_btn)

        layout.addStretch()
        self.setLayout(layout)


    # — Métodos auxiliares — #

    def _config_spin(self, widget, minimum, maximum, decimals, key, default):
        widget.setRange(minimum, maximum)
        widget.setDecimals(decimals)
        val = self.case_config["controlDict"].get(key, default)
        widget.setValue(val if val is not None else default)
        return widget

    def _connect_control_dict_signals(self):
        self.solver_combo.currentTextChanged.connect(self._on_solver_changed)
        self.sim_combo.currentTextChanged.connect(self._on_sim_changed)

        mapping = [
            (self.start_time, "startTime"),
            (self.end_time,   "endTime"),
            (self.deltaT,     "deltaT"),
            (self.adapt_dt,   "adjustTimeStep"),
            (self.maxCo,      "maxCo"),
            (self.maxDeltaT,  "maxDeltaT"),
            (self.nOuterCorrectors, "nOuterCorrectors"),
            (self.nInnerIterations, "nInnerIterations"),
            (self.write_control,    "writeControl"),
            (self.write_interval,   "writeInterval"),
            (self.write_format,     "writeFormat"),
            (self.write_precision,  "writePrecision"),
            (self.write_compression,"writeCompression")
        ]
        for widget, key in mapping:
            sig = getattr(widget, "valueChanged", None) \
                  or getattr(widget, "stateChanged", None) \
                  or widget.currentTextChanged
            sig.connect(lambda *_, k=key: self._on_cd_change(k))

    def _on_solver_changed(self, text):
        self.case_config["solverSettings"]["solver"] = text
        self._update_pimple(text)
        self._on_cd_change("solver")

    def _on_sim_changed(self, text):
        self.case_config["solverSettings"]["simulationType"] = text
        self._update_visibility(text)
        self._on_cd_change("simulationType")

    def _on_cd_change(self, _):
        cd = {
            "solver":           self.solver_combo.currentText(),
            "simulationType":   self.sim_combo.currentText(),
            "startTime":        self.start_time.value(),
            "endTime":          self.end_time.value() if self.end_time.isVisible() else None,
            "deltaT":           self.deltaT.value() if self.deltaT.isVisible() else None,
            "adjustTimeStep":   self.adapt_dt.isChecked() if self.adapt_dt.isVisible() else None,
            "maxCo":            self.maxCo.value(),
            "maxDeltaT":        self.maxDeltaT.value() if self.maxDeltaT.isVisible() else None,
            "nOuterCorrectors": self.nOuterCorrectors.value() if self.pimple_group.isVisible() else None,
            "nInnerIterations": self.nInnerIterations.value() if self.pimple_group.isVisible() else None,
            "writeControl":     self.write_control.currentText(),
            "writeInterval":    self.write_interval.value(),
            "writeFormat":      self.write_format.currentText(),
            "writePrecision":   self.write_precision.value(),
            "writeCompression": self.write_compression.isChecked()
        }
        self.case_config["controlDict"].update(cd)
        JSONManager().save_section("controlDict", cd)
        self.data_changed.emit()

    def _update_visibility(self, sim):
        is_stat = (sim == "Estacionario")
        for w in (self.end_time, self.deltaT, self.adapt_dt, self.maxDeltaT):
            w.setVisible(not is_stat)
        if is_stat:
            for k in ("endTime", "deltaT", "adjustTimeStep", "maxDeltaT"):
                self.case_config["controlDict"][k] = None

    def _update_pimple(self, solver):
        show = solver in ("pimpleFoam", "pisoFoam")
        self.pimple_group.setVisible(show)
        if not show:
            for k in ("nOuterCorrectors", "nInnerIterations"):
                self.case_config["controlDict"][k] = None

    def _update_decomp_desc(self, method):
        descs = {
            "simple":       "División ortogonal uniforme.",
            "hierarchical": "Jerárquica (subdivisiones en cascada).",
            "scotch":       "Optimiza con Scotch.",
            "metis":        "Equilibra con METIS.",
            "manual":       "Manual: edición de decompositionManualDict."
        }
        self.decomp_desc.setText(descs.get(method, ""))

    def _on_initialize(self):
        temp_dir = os.path.join(self.root_dir, "temp")
        dp0      = os.path.join(temp_dir, "DP0")

        try:
            # 1) condiciones de contorno y carpeta 0
            generate_boundary_conditions(temp_dir, parent=self)
            logging.info("→ Condiciones de contorno generadas.")

            # 2) archivos del directorio constant
            generate_constant_files(self.case_config, self.root_dir)
            logging.info("→ Archivos de constant generados.")

            # 3) reactingCloudProperties (fase discreta)
            discrete_cfg = JSONManager().load_section("Disperse_fase") or {}
            generate_reactingCloudProperties(discrete_cfg, self.root_dir)
            logging.info("→ reactingCloudProperties procesado.")

            # 4) combustionProperties + CHEMKIN
            chem_cfg    = self.case_config.get("combustion", {})
            chem_active = chem_cfg.get("active", False)
            chemkin_dir = os.path.join(self.root_dir, "chemkin")
            comb_prop   = os.path.join(dp0, "constant", "combustionProperties")

            if chem_active:
                # generar combustionProperties en temp/DP0/constant
                generate_combustionProperties(chem_cfg, self.root_dir)
                logging.info("→ combustionProperties generado en %s", comb_prop)

                # Asegurar directorio CHEMKIN en <case>/chemkin
                os.makedirs(chemkin_dir, exist_ok=True)
                logging.info("→ Directorio CHEMKIN preparado en %s", chemkin_dir)
            else:
                # eliminar combustionProperties si existe
                if os.path.isfile(comb_prop):
                    os.remove(comb_prop)
                    logging.info("→ combustionProperties eliminado (química inactiva).")
                # eliminar carpeta CHEMKIN si existe
                if os.path.isdir(chemkin_dir):
                    shutil.rmtree(chemkin_dir)
                    logging.info("→ carpeta chemkin eliminada (química inactiva).")

            # 5) alphat en DP0/0/
            ap = os.path.join(dp0, "0", "alphat")
            os.makedirs(os.path.dirname(ap), exist_ok=True)
            with open(os.path.join(temp_dir, "boundary_conditions.json"), "r", encoding="utf-8") as f:
                bc_data = json.load(f)
            boundary_conditions = bc_data.get("boundaryConditions", {})
            calcType            = bc_data.get(
                "calculationType",
                self.case_config.get("solverSettings", {}).get("calculationType", "Compresible")
            )
            generate_alphat_file(boundary_conditions, ap, calcType)
            logging.info("→ alphat generado.")

            QMessageBox.information(
                self, "Inicialización",
                "Todos los archivos iniciales han sido generados."
            )
            self.data_changed.emit()

        except Exception as e:
            logging.error("Error en Inicialización", exc_info=True)
            QMessageBox.critical(self, "Error Inicialización", str(e))

    def _on_run_parallel(self):
        temp_dp0 = os.path.join(self.root_dir, "temp", "DP0")
        sysd     = os.path.join(temp_dp0, "system")
        os.makedirs(sysd, exist_ok=True)

        # escribir decomposeParDict
        dpp = os.path.join(sysd, "decomposeParDict")
        lines = [
            "FoamFile", "{", "  version 2.0;", "  format ascii;",
            "  class dictionary;", "  object decomposeParDict;", "}",
            f"numberOfSubdomains {self.nproc_spin.value()};",
            f"method          {self.decomp_combo.currentText()};"
        ]
        m = self.decomp_combo.currentText()
        if m == "hierarchical":
            lines += ["hierarchicalCoeffs", "{", "  n (2 2 1);", "  order xyz;", "}"]
        elif m == "manual":
            lines += ["manualCoeffs", "{", "  dataFile \"decompositionManualDict\";", "}"]

        with open(dpp, "w") as f:
            f.write("\n".join(lines))
        logging.info("→ decomposeParDict escrito.")

        try:
            subprocess.run(["decomposePar", "-case", temp_dp0], check=True)
            logging.info("→ decomposePar completado.")

            solver = self.case_config["solverSettings"].get("solver", "simpleFoam")
            subprocess.run([
                "mpirun", "-np", str(self.nproc_spin.value()),
                solver, "-parallel", "-case", temp_dp0
            ], check=True)
            logging.info("→ Solver en paralelo finalizado.")
            QMessageBox.information(self, "Ejecución", "Cálculo en paralelo completado.")
        except subprocess.CalledProcessError as e:
            logging.error("Error en ejecución paralela", exc_info=True)
            QMessageBox.critical(self, "Error Ejecución", str(e))
