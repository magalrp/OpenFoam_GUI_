# ui/main_window.py

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QStackedWidget, QMessageBox
)
from PyQt5.QtCore import Qt

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

import os

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OpenFOAM Setup Interface")
        self.resize(1000, 700)

        # JSON manager y configuración del caso
        self.json_manager = JSONManager()
        self.case_config  = self.load_case_config()

        # Layout principal
        main_layout = QHBoxLayout(self)

        # Árbol lateral
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)

        # Nodos raíz
        self.item_case         = QTreeWidgetItem(["Case"])
        self.item_case.setFont(0, self.get_bold_font())
        self.item_solver_title = QTreeWidgetItem(["Solver"])
        self.item_solver_title.setFont(0, self.get_bold_font())

        # Hijos bajo 'Case'
        self.item_directorio     = QTreeWidgetItem(["Directorio de trabajo"])
        self.item_modelos        = QTreeWidgetItem(["Modelos"])
        self.item_materiales     = QTreeWidgetItem(["Materiales"])
        self.item_bc             = QTreeWidgetItem(["Boundary Conditions"])
        self.item_discrete_phase = QTreeWidgetItem(["Fase Discreta"])

        # Hijos bajo 'Solver' en el orden deseado
        self.item_methods        = QTreeWidgetItem(["Methods"])
        self.item_controls       = QTreeWidgetItem(["Controls"])
        self.item_inicializacion = QTreeWidgetItem(["Inicialización"])
        self.item_run_calc       = QTreeWidgetItem(["Run Calculation"])

        # Ensamble del árbol
        self.item_case.addChildren([
            self.item_directorio,
            self.item_modelos,
            self.item_materiales,
            self.item_bc,
            self.item_discrete_phase
        ])
        self.tree.addTopLevelItem(self.item_case)

        self.tree.addTopLevelItem(self.item_solver_title)
        for child in [
            self.item_methods,
            self.item_controls,
            self.item_inicializacion,
            self.item_run_calc
        ]:
            self.item_solver_title.addChild(child)

        # StackedWidget
        self.stacked = QStackedWidget()

        # Crear páginas
        self.page_directorio     = DirectorioTrabajo(self.case_config)
        self.page_modelos        = Modelo(self.case_config)
        self.page_materiales     = Materiales(self.case_config)
        self.page_bc             = BoundaryConditions(self.case_config)
        self.page_discrete_phase = FaseDiscreta(self.case_config)
        self.page_methods        = Methods(self.case_config)
        self.page_controls       = Controls(self.case_config)
        self.page_inicializacion = Inicializacion(os.path.join(os.getcwd(), "temp"))
        self.page_run_calc       = RunCalculation(self.case_config)

        # Añadir páginas al stacked en el mismo orden
        for pg in [
            self.page_directorio,      # 0
            self.page_modelos,         # 1
            self.page_materiales,      # 2
            self.page_bc,              # 3
            self.page_discrete_phase,  # 4
            self.page_methods,         # 5
            self.page_controls,        # 6
            self.page_inicializacion,  # 7
            self.page_run_calc         # 8
        ]:
            self.stacked.addWidget(pg)

        # Montar layout
        main_layout.addWidget(self.tree, 1)
        main_layout.addWidget(self.stacked, 4)
        self.setLayout(main_layout)

        # Conexiones de navegación
        self.tree.currentItemChanged.connect(self.on_tree_item_changed)
        self.tree.setCurrentItem(self.item_directorio)
        self.tree.expandItem(self.item_solver_title)

        # Auto-guardado
        self.page_bc.data_changed.connect(self.auto_save_boundary_conditions)
        self.page_materiales.data_changed.connect(self.auto_save_materiales)
        self.page_methods.data_changed.connect(self.auto_save_methods)
        self.page_controls.data_changed.connect(self.auto_save_controls)
        self.page_run_calc.data_changed.connect(self.auto_save_run_calc)
        self.page_directorio.boundaries_loaded.connect(self.sync_boundary_conditions)

    def get_bold_font(self):
        f = self.font()
        f.setBold(True)
        return f

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
        Cambia la página del stacked según el texto del ítem seleccionado.
        """
        text = current.text(0)
        if text == "Directorio de trabajo":
            idx = 0
        elif text == "Modelos":
            idx = 1
        elif text == "Materiales":
            idx = 2
        elif text == "Boundary Conditions":
            idx = 3
        elif text == "Fase Discreta":
            idx = 4
        elif text == "Methods":
            idx = 5
        elif text == "Controls":
            idx = 6
        elif text == "Inicialización":
            idx = 7
        elif text == "Run Calculation":
            idx = 8
        else:
            idx = 0
        self.stacked.setCurrentIndex(idx)

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
