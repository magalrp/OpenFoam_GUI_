# ui/main_window.py

import os
import logging
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QTreeWidget, QStackedWidget, QMessageBox,
    QSplitter
)
from PyQt5.QtCore import Qt

from ui.tree_builder import TreeBuilder
from ui.sections.directorio_trabajo import DirectorioTrabajo
from ui.sections.modelo import Modelo
from ui.sections.materiales import Materiales
from ui.sections.boundary_conditions import BoundaryConditions
from ui.sections.fase_discreta import FaseDiscreta
from ui.sections.inicializacion import Inicializacion
from ui.sections.methods import Methods
from ui.sections.controls import Controls
from ui.sections.run_calculation import RunCalculation

from ui.sections.console_panel    import ConsolePanel, QtHandler
from ui.sections.visualizer_panel import VisualizerPanel

from core.json_manager import JSONManager


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenFOAM Setup Interface")
        self.resize(1200, 800)

        # Aplicar un stylesheet más elegante
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #fafafa;
                border: 1px solid #ddd;
                font-size: 14px;
            }
            QStackedWidget {
                background-color: #fff;
                border: 1px solid #ddd;
            }
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-top: 0.5em;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
            }
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #dcdcdc;
                border: none;
                font-family: monospace;
            }
            QSplitter::handle {
                background-color: #ddd;
            }
        """)

        # JSON manager y configuración
        self.json_manager = JSONManager()
        self.case_config  = self.load_case_config()

        # Layout principal con QSplitter horizontal
        main_layout = QHBoxLayout(self)
        splitter_h = QSplitter(Qt.Horizontal, self)

        # 1) Árbol lateral
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree_items = TreeBuilder.build(self.tree)
        splitter_h.addWidget(self.tree)

        # 2) Páginas centrales
        self.stacked = QStackedWidget()
        self.page_directorio     = DirectorioTrabajo(self.case_config)
        self.page_modelos        = Modelo(self.case_config)
        self.page_materiales     = Materiales(self.case_config)
        self.page_bc             = BoundaryConditions(self.case_config)
        self.page_discrete_phase = FaseDiscreta(self.case_config)
        self.page_methods        = Methods(self.case_config)
        self.page_controls       = Controls(self.case_config)
        self.page_inicializacion = Inicializacion(os.path.join(os.getcwd(), "temp"))
        self.page_run_calc       = RunCalculation(self.case_config)

        for pg in [
            self.page_directorio,
            self.page_modelos,
            self.page_materiales,
            self.page_bc,
            self.page_discrete_phase,
            self.page_methods,
            self.page_controls,
            self.page_inicializacion,
            self.page_run_calc
        ]:
            self.stacked.addWidget(pg)

        splitter_h.addWidget(self.stacked)

        # 3) Panel derecho fijo con QSplitter vertical
        right_splitter = QSplitter(Qt.Vertical)
        self.visualizer = VisualizerPanel()
        self.console    = ConsolePanel()
        right_splitter.addWidget(self.visualizer)
        right_splitter.addWidget(self.console)
        # Alturas iniciales: más espacio al visualizador
        right_splitter.setSizes([600, 200])

        splitter_h.addWidget(right_splitter)

        # Anchos iniciales: árbol estrecho, páginas medias, panel derecho
        splitter_h.setSizes([200, 600, 400])

        main_layout.addWidget(splitter_h)

        # Mapeo clave → página
        self.page_map = {
            "directorio":          self.page_directorio,
            "modelos":             self.page_modelos,
            "materiales":          self.page_materiales,
            "boundary_conditions": self.page_bc,
            "fase_discreta":       self.page_discrete_phase,
            "methods":             self.page_methods,
            "controls":            self.page_controls,
            "inicializacion":      self.page_inicializacion,
            "run_calculation":     self.page_run_calc
        }

        # Conexiones árbol → stacked
        self.tree.currentItemChanged.connect(self.on_tree_item_changed)
        first = self.tree_items.get("directorio")
        if first:
            self.tree.setCurrentItem(first)

        # Auto-guardado
        self.page_bc.data_changed.connect(self.auto_save_boundary_conditions)
        self.page_materiales.data_changed.connect(self.auto_save_materiales)
        self.page_methods.data_changed.connect(self.auto_save_methods)
        self.page_controls.data_changed.connect(self.auto_save_controls)
        self.page_run_calc.data_changed.connect(self.auto_save_run_calc)
        self.page_directorio.boundaries_loaded.connect(self.sync_boundary_conditions)

        # Logging → consola
        handler = QtHandler(self.console.log_widget)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

    def load_case_config(self):
        defaults = {
            "solverSettings": {
                "solver": "icoFoam",
                "simulationType": "Estacionario",
                "calculationType": "Incompresible"
            },
            "controlDict": {
                "startTime": 0.0, "endTime": 0.0, "deltaT": 0.001,
                "adjustTimeStep": False, "maxCo": 1.0, "maxDeltaT": 0.0,
                "nOuterCorrectors": None, "nInnerIterations": None,
                "writeControl": "timeStep", "writeInterval": 1.0,
                "writeFormat": "ascii", "writePrecision": 6,
                "writeCompression": False
            },
            "fvSchemes": {}, "fvSolution": {}
        }
        path = self.json_manager.get_file_path("case_config")
        if os.path.exists(path):
            loaded = self.json_manager.load_section("case_config") or {}
            defaults.update(loaded)
        else:
            self.json_manager.save_section("case_config", defaults)
        return defaults

    def on_tree_item_changed(self, current, previous):
        for key, item in self.tree_items.items():
            if item is current:
                page = self.page_map.get(key)
                if page:
                    self.stacked.setCurrentWidget(page)
                return

    def sync_boundary_conditions(self):
        boundaries = self.page_directorio.boundaries_info
        for b in boundaries:
            name = b.get("name")
            if name and name not in self.case_config.get("boundaryConditions", {}):
                default_type = (
                    "Inlet" if "inlet" in name.lower() else
                    "Outlet" if "outlet" in name.lower() else
                    "Wall"
                )
                self.case_config.setdefault("boundaryConditions", {})[name] = {
                    "type": default_type, "value": ""
                }
        self.page_bc.update_bc_tree()

    def auto_save_boundary_conditions(self):
        self.page_bc.save_boundary_conditions()

    def auto_save_materiales(self):
        self.page_materiales.save_materiales()

    def auto_save_methods(self):
        schemes = self.case_config.get("fvSchemes", {})
        success, msg = self.json_manager.save_section("fvSchemes", schemes)
        if not success:
            QMessageBox.critical(self, "Error guardando fvSchemes", msg)

    def auto_save_controls(self):
        sol = self.case_config.get("fvSolution", {})
        success, msg = self.json_manager.save_section("fvSolution", sol)
        if not success:
            QMessageBox.critical(self, "Error guardando fvSolution", msg)

    def auto_save_run_calc(self):
        cd = self.case_config.get("controlDict", {})
        success, msg = self.json_manager.save_section("controlDict", cd)
        if not success:
            QMessageBox.critical(self, "Error guardando controlDict", msg)
