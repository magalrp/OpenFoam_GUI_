# ui/main_window.py

import os
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QTreeWidget,
    QStackedWidget, QMessageBox
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

from core.json_manager import JSONManager


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OpenFOAM Setup Interface")
        self.resize(1000, 700)

        # JSON manager y configuración del caso
        self.json_manager = JSONManager()
        self.case_config = self.load_case_config()

        # Layout principal
        main_layout = QHBoxLayout(self)

        # Árbol lateral
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)

        # Construir el árbol y obtener el mapeo clave→QTreeWidgetItem
        self.tree_items = TreeBuilder.build(self.tree)

        # StackedWidget
        self.stacked = QStackedWidget()

        # Crear páginas y añadirlas al stacked
        self.page_directorio     = DirectorioTrabajo(self.case_config)
        self.page_modelos        = Modelo(self.case_config)
        self.page_materiales     = Materiales(self.case_config)
        self.page_bc             = BoundaryConditions(self.case_config)
        self.page_discrete_phase = FaseDiscreta(self.case_config)
        self.page_methods        = Methods(self.case_config)
        self.page_controls       = Controls(self.case_config)
        self.page_inicializacion = Inicializacion(os.path.join(os.getcwd(), "temp"))
        self.page_run_calc       = RunCalculation(self.case_config)

        for page in [
            self.page_directorio,      # key: "directorio"
            self.page_modelos,         # key: "modelos"
            self.page_materiales,      # key: "materiales"
            self.page_bc,              # key: "boundary_conditions"
            self.page_discrete_phase,  # key: "fase_discreta"
            self.page_methods,         # key: "methods"
            self.page_controls,        # key: "controls"
            self.page_inicializacion,  # key: "inicializacion"
            self.page_run_calc         # key: "run_calculation"
        ]:
            self.stacked.addWidget(page)

        # Montar layout
        main_layout.addWidget(self.tree, 1)
        main_layout.addWidget(self.stacked, 4)
        self.setLayout(main_layout)

        # Mapeo de claves a páginas (debe coincidir con TREE_STRUCTURE keys)
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

        # Conexiones de navegación
        self.tree.currentItemChanged.connect(self.on_tree_item_changed)
        # Seleccionar la primera página (“directorio”)
        first_item = self.tree_items.get("directorio")
        if first_item:
            self.tree.setCurrentItem(first_item)

        # Auto-guardado
        self.page_bc.data_changed.connect(self.auto_save_boundary_conditions)
        self.page_materiales.data_changed.connect(self.auto_save_materiales)
        self.page_methods.data_changed.connect(self.auto_save_methods)
        self.page_controls.data_changed.connect(self.auto_save_controls)
        self.page_run_calc.data_changed.connect(self.auto_save_run_calc)
        self.page_directorio.boundaries_loaded.connect(self.sync_boundary_conditions)

    def load_case_config(self):
        """
        Carga la configuración del caso o devuelve valores por
        defecto (incluyendo fvSchemes y fvSolution).
        """
        defaults = {
            "solverSettings": {
                "solver": "icoFoam",
                "simulationType": "Estacionario",
                "calculationType": "Incompresible"
            },
            "controlDict": {
                "startTime": 0.0,
                "endTime": 0.0,
                "deltaT": 0.001,
                "adjustTimeStep": False,
                "maxCo": 1.0,
                "maxDeltaT": 0.0,
                "nOuterCorrectors": None,
                "nInnerIterations": None,
                "writeControl": "timeStep",
                "writeInterval": 1.0,
                "writeFormat": "ascii",
                "writePrecision": 6,
                "writeCompression": False
            },
            "fvSchemes": {},
            "fvSolution": {}
        }
        path = self.json_manager.get_file_path("case_config")
        if os.path.exists(path):
            loaded = self.json_manager.load_section("case_config") or {}
            defaults.update(loaded)
        else:
            self.json_manager.save_section("case_config", defaults)
        return defaults

    def on_tree_item_changed(self, current, previous):
        """
        Cambia la página del stacked según el item seleccionado.
        """
        for key, item in self.tree_items.items():
            if item is current:
                page = self.page_map.get(key)
                if page:
                    self.stacked.setCurrentWidget(page)
                return

    def sync_boundary_conditions(self):
        """
        Integra fronteras desde DirectorioTrabajo en case_config.
        """
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
