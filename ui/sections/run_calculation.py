# ui/sections/run_calculation.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel,
    QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox,
    QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QLocale
from core.json_manager import JSONManager

class RunCalculation(QWidget):
    """
    Sección de 'Run calculation' para parametrizar y generar el archivo controlDict.
    Aquí el usuario selecciona el solver, tipo de simulación, control de tiempo, salida,
    y parámetros avanzados como Courant, adaptabilidad de deltaT y PIMPLE.
    """
    data_changed = pyqtSignal()

    def __init__(self, case_config):
        super().__init__()
        self.case_config = case_config

        # Forzar uso de '.' como separador decimal
        self.setLocale(QLocale(QLocale.C))

        # Cargar valores previos de controlDict.json si existen
        jm = JSONManager()
        persisted = jm.load_section("controlDict") or {}
        self.case_config.setdefault("solverSettings", {})
        self.case_config.setdefault("controlDict", {})
        # Mezclar persisted en case_config
        for k, v in persisted.items():
            if k in ["solver", "simulationType"]:
                self.case_config["solverSettings"][k] = v
            else:
                self.case_config["controlDict"][k] = v

        # Opciones
        self.solvers = ["icoFoam", "simpleFoam", "pisoFoam", "pimpleFoam", "reactingParcelFoam"]
        self.modes   = ["Estacionario", "Transitorio"]

        default_solver = self.case_config["solverSettings"].get("solver", self.solvers[0])
        default_sim    = self.case_config["solverSettings"].get("simulationType", self.modes[0])

        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Run calculation")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        # Descripción
        desc = QLabel(
            "En esta sección define el solver de OpenFOAM, el tipo de simulación, los parámetros de tiempo,\n"
            "y ajustes avanzados como el número de Courant y control adaptativo de deltaT."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.form = QFormLayout()

        # Solver
        self.solver_combo = QComboBox()
        self.solver_combo.addItems(self.solvers)
        self.solver_combo.setCurrentText(default_solver)
        self.form.addRow("Solver:", self.solver_combo)

        # Simulation Type
        self.sim_combo = QComboBox()
        self.sim_combo.addItems(self.modes)
        self.sim_combo.setCurrentText(default_sim)
        self.form.addRow("Simulation Type:", self.sim_combo)

        # Time control
        self.start_time = QDoubleSpinBox()
        self._configure_spinbox(self.start_time, 0.0, 1e6, 6, "startTime", 0.0)
        self.form.addRow("Start Time:", self.start_time)

        self.end_time = QDoubleSpinBox()
        self._configure_spinbox(self.end_time, 0.0, 1e6, 6, "endTime", 0.0)
        self.form.addRow("End Time:", self.end_time)

        self.deltaT = QDoubleSpinBox()
        self._configure_spinbox(self.deltaT, 1e-6, 1e6, 6, "deltaT", 0.001)
        self.form.addRow("Δt (Time Step):", self.deltaT)

        # Adapt deltaT
        self.adapt_dt = QCheckBox()
        self.adapt_dt.setChecked(self._get_cfg("adjustTimeStep", False))
        self.form.addRow("Adjust deltaT:", self.adapt_dt)

        # Courant number
        self.maxCo = QDoubleSpinBox()
        self._configure_spinbox(self.maxCo, 0.0, 10.0, 6, "maxCo", 1.0)
        self.form.addRow("Max Courant (maxCo):", self.maxCo)

        # Max deltaT
        self.maxDeltaT = QDoubleSpinBox()
        self._configure_spinbox(self.maxDeltaT, 1e-6, 1e6, 6, "maxDeltaT", 0.0)
        self.form.addRow("Max Δt (maxDeltaT):", self.maxDeltaT)

        # PIMPLE controls
        self.pimple_box = QGroupBox("PIMPLE/PISO Controls")
        p_layout = QFormLayout()
        self.nOuterCorrectors = QSpinBox(); self.nOuterCorrectors.setRange(1, 100)
        self.nOuterCorrectors.setValue(self._get_cfg("nOuterCorrectors", 2))
        p_layout.addRow("Outer Correctors:", self.nOuterCorrectors)
        self.nInnerIterations = QSpinBox(); self.nInnerIterations.setRange(1, 100)
        self.nInnerIterations.setValue(self._get_cfg("nInnerIterations", 1))
        p_layout.addRow("Inner Iterations:", self.nInnerIterations)
        self.pimple_box.setLayout(p_layout)

        # Output control
        self.write_control = QComboBox(); self.write_control.addItems(["timeStep","runTime","clockTime"])
        self.write_control.setCurrentText(self.case_config["controlDict"].get("writeControl", "timeStep"))
        self.form.addRow("Write Control:", self.write_control)

        self.write_interval = QDoubleSpinBox()
        self._configure_spinbox(self.write_interval, 0.0, 1e6, 6, "writeInterval", 1.0)
        self.form.addRow("Write Interval:", self.write_interval)

        self.write_format = QComboBox(); self.write_format.addItems(["ascii","binary","compressed"])
        self.write_format.setCurrentText(self.case_config["controlDict"].get("writeFormat", "ascii"))
        self.form.addRow("Write Format:", self.write_format)

        self.write_precision = QSpinBox(); self.write_precision.setRange(0,16)
        self.write_precision.setValue(self._get_cfg("writePrecision", 6))
        self.form.addRow("Write Precision:", self.write_precision)

        self.write_compression = QCheckBox()
        self.write_compression.setChecked(self._get_cfg("writeCompression", False))
        self.form.addRow("Write Compression:", self.write_compression)

        layout.addLayout(self.form)
        layout.addWidget(self.pimple_box)
        layout.addStretch()

        # Signals
        self.solver_combo.currentTextChanged.connect(self._on_solver_changed)
        self.sim_combo.currentTextChanged.connect(self._on_simulation_changed)
        for w in [self.start_time, self.end_time, self.deltaT,
                  self.adapt_dt, self.maxCo, self.maxDeltaT,
                  self.nOuterCorrectors, self.nInnerIterations,
                  self.write_control, self.write_interval,
                  self.write_format, self.write_precision,
                  self.write_compression]:
            if hasattr(w, 'valueChanged'):
                w.valueChanged.connect(self._on_data_changed)
            elif hasattr(w, 'stateChanged'):
                w.stateChanged.connect(self._on_data_changed)
            elif hasattr(w, 'currentTextChanged'):
                w.currentTextChanged.connect(self._on_data_changed)

        # Inicializar visibilidad
        self._update_visibility(default_sim)
        self._update_pimple_visibility(default_solver)

    def _get_cfg(self, key, default):
        # Retorna valor guardado o default si es None
        val = self.case_config["controlDict"].get(key)
        return default if val is None else val

    def _configure_spinbox(self, widget, minimum, maximum, decimals, key, default):
        widget.setRange(minimum, maximum)
        widget.setDecimals(decimals)
        val = self._get_cfg(key, default)
        widget.setValue(val)
        return widget

    def _on_solver_changed(self, text):
        self.case_config["solverSettings"]["solver"] = text
        self._update_pimple_visibility(text)
        self._on_data_changed()

    def _on_simulation_changed(self, text):
        self.case_config["solverSettings"]["simulationType"] = text
        self._update_visibility(text)
        self._on_data_changed()

    def _update_visibility(self, sim_type):
        is_stat = (sim_type == "Estacionario")
        for key, widget in [("endTime", self.end_time), ("deltaT", self.deltaT),
                             ("adjustTimeStep", self.adapt_dt), ("maxDeltaT", self.maxDeltaT)]:
            visible = not is_stat
            self._set_row_visible(widget, visible)
            if not visible:
                self.case_config["controlDict"][key] = None

    def _update_pimple_visibility(self, solver):
        show = solver in ["pimpleFoam","pisoFoam"]
        self.pimple_box.setVisible(show)
        if not show:
            self.case_config["controlDict"]["nOuterCorrectors"] = None
            self.case_config["controlDict"]["nInnerIterations"] = None

    def _set_row_visible(self, widget, visible):
        for i in range(self.form.rowCount()):
            label = self.form.itemAt(i, QFormLayout.LabelRole)
            field = self.form.itemAt(i, QFormLayout.FieldRole)
            if field and field.widget() is widget:
                label.widget().setVisible(visible)
                widget.setVisible(visible)
                break

    def _on_data_changed(self, *args):
        jm = JSONManager()
        cd = {
            'solver': self.case_config['solverSettings'].get('solver'),
            'simulationType': self.case_config['solverSettings'].get('simulationType'),
            'startTime': self.start_time.value(),
            'endTime': self.end_time.value() if self.end_time.isVisible() else None,
            'deltaT': self.deltaT.value() if self.deltaT.isVisible() else None,
            'adjustTimeStep': self.adapt_dt.isChecked() if self.adapt_dt.isVisible() else None,
            'maxCo': self.maxCo.value() if self.maxCo.isVisible() else None,
            'maxDeltaT': self.maxDeltaT.value() if self.maxDeltaT.isVisible() else None,
            'nOuterCorrectors': self.nOuterCorrectors.value() if self.pimple_box.isVisible() else None,
            'nInnerIterations': self.nInnerIterations.value() if self.pimple_box.isVisible() else None,
            'writeControl': self.write_control.currentText(),
            'writeInterval': self.write_interval.value(),
            'writeFormat': self.write_format.currentText(),
            'writePrecision': self.write_precision.value(),
            'writeCompression': self.write_compression.isChecked()
        }
        self.case_config['controlDict'].update(cd)
        jm.save_section('controlDict', cd)
        self.data_changed.emit()
