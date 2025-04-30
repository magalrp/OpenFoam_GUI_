# ui/sections/materiales.py

import os
import json

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QPushButton, QMessageBox, QInputDialog,
    QTabWidget, QFormLayout, QLineEdit, QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal

from core.json_manager import JSONManager
from ui.dialogs.config_material_dialog import ConfigMaterialDialog


class Materiales(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, case_config):
        super().__init__()
        self.case_config = case_config
        self.section_name = "materials"
        self.json_manager = JSONManager()

        # Asegurar secciones en case_config
        self.case_config.setdefault("materials", [])
        self.case_config.setdefault("thermophysicalProperties", {})

        # Cargar desde JSON
        self.load_materials()
        self.load_thermophysical()

        # Inicializar por defecto si hace falta
        self.ensure_default_material()
        self.enforce_constant_viscosity_if_no_energy()

        # Construir interfaz
        self.init_ui()

        # Poblaciones iniciales
        self.update_material_list()
        self.populate_thermo_fields()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Materiales y Propiedades Térmicas")
        title.setStyleSheet("font-weight:bold; font-size:16px;")
        layout.addWidget(title)

        self.tabs = QTabWidget()

        # --- Pestaña Materiales ---
        mat_tab = QWidget()
        mat_layout = QVBoxLayout(mat_tab)

        self.material_table = QTableWidget()
        self.material_table.setColumnCount(2)
        self.material_table.setHorizontalHeaderLabels(["Nombre", "Tipo"])
        self.material_table.horizontalHeader().setStretchLastSection(True)
        self.material_table.verticalHeader().setVisible(False)
        mat_layout.addWidget(self.material_table)

        btns = QHBoxLayout()
        self.btn_create = QPushButton("Crear Material")
        self.btn_create.clicked.connect(self.create_material)
        btns.addWidget(self.btn_create)

        self.btn_config = QPushButton("Configurar Material")
        self.btn_config.clicked.connect(self.configure_material)
        btns.addWidget(self.btn_config)

        btns.addStretch()

        self.btn_delete = QPushButton("Eliminar Material")
        self.btn_delete.clicked.connect(self.delete_material)
        btns.addWidget(self.btn_delete)

        mat_layout.addLayout(btns)
        mat_layout.addStretch()
        self.tabs.addTab(mat_tab, "Materiales")

        # --- Pestaña Propiedades Térmicas ---
        thermo_tab = QWidget()
        form = QFormLayout(thermo_tab)

        tp = self.case_config["thermophysicalProperties"]

        self.thermo_type = QComboBox()
        self.thermo_type.addItems(["heRhoThermo", "rhoThermo", "hConstThermo"])
        self.thermo_type.setCurrentText(tp.get("type", "heRhoThermo"))
        form.addRow("thermoType.type:", self.thermo_type)

        self.mixture = QComboBox()
        self.mixture.addItems(["reactingMixture", "pureMixture"])
        self.mixture.setCurrentText(tp.get("mixture", "reactingMixture"))
        form.addRow("thermoType.mixture:", self.mixture)

        self.transport = QComboBox()
        self.transport.addItems(["const", "sutherland", "powerLaw"])
        self.transport.setCurrentText(tp.get("transport", "sutherland"))
        form.addRow("thermoType.transport:", self.transport)

        self.thermo = QComboBox()
        self.thermo.addItems(["janaf", "hPolynomial"])
        self.thermo.setCurrentText(tp.get("thermo", "janaf"))
        form.addRow("thermoType.thermo:", self.thermo)

        self.energy = QComboBox()
        self.energy.addItems(["sensibleEnthalpy", "totalEnthalpy"])
        self.energy.setCurrentText(tp.get("energy", "sensibleEnthalpy"))
        form.addRow("thermoType.energy:", self.energy)

        self.eos = QComboBox()
        self.eos.addItems(["perfectGas", "incompressible"])
        self.eos.setCurrentText(tp.get("equationOfState", "perfectGas"))
        form.addRow("thermoType.equationOfState:", self.eos)

        self.chemkin_dir = QLineEdit(tp.get("chemkin_dir", "<case>/chemkin"))
        form.addRow("Directorio CHEMKIN:", self.chemkin_dir)

        self.new_format = QCheckBox("newFormat")
        self.new_format.setChecked(tp.get("newFormat", True))
        form.addRow(self.new_format)

        self.tabs.addTab(thermo_tab, "Propiedades Térmicas")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def hideEvent(self, event):
        """
        Cuando la sección completa se oculta (se sale a otra sección del árbol),
        guardamos materiales + propiedades térmicas.
        """
        # Guardar materiales
        self._save_materials()
        # Guardar thermophysical en case_config.json
        self._save_thermophysical()
        # Emitir señal para que main_window pueda notificar
        self.data_changed.emit()
        super().hideEvent(event)

    def load_materials(self):
        data = self.json_manager.load_section(self.section_name)
        if "materials" in data:
            self.case_config["materials"] = data["materials"]

    def load_thermophysical(self):
        path = os.path.join(os.getcwd(), "temp", "constant.json")
        try:
            with open(path, "r") as f:
                cd = json.load(f)
            tp = cd.get("thermophysicalProperties", {})
            self.case_config["thermophysicalProperties"] = tp
        except Exception:
            pass

    def _save_materials(self):
        data = {"materials": self.case_config["materials"]}
        ok, msg = self.json_manager.save_section(self.section_name, data)
        if not ok:
            QMessageBox.critical(self, "Error guardando materiales", msg)
        else:
            print("materials.json actualizado")

    def _save_thermophysical(self):
        tp = {
            "type": self.thermo_type.currentText(),
            "mixture": self.mixture.currentText(),
            "transport": self.transport.currentText(),
            "thermo": self.thermo.currentText(),
            "energy": self.energy.currentText(),
            "equationOfState": self.eos.currentText(),
            "chemkin_dir": self.chemkin_dir.text(),
            "newFormat": self.new_format.isChecked()
        }
        self.case_config["thermophysicalProperties"] = tp
        ok, msg = self.json_manager.save_section("case_config", self.case_config)
        if not ok:
            QMessageBox.critical(self, "Error guardando thermophysical", msg)
        else:
            print("constant.json actualizado con thermophysicalProperties")

    # Alias que el main_window espera para el autoguardado
    def save_materiales(self):
        # No hace nada de más: el verdadero guardado está en hideEvent
        pass

    def ensure_default_material(self):
        if not self.case_config["materials"]:
            default = {
                "name": "Aire",
                "type": "fluid",
                "properties": {"densityModel": "constant", "densityValue": 1.225}
            }
            turb = str(self.case_config.get("turbulenceModel", "")).lower()
            if turb and turb != "laminar":
                default["properties"].update({
                    "viscosityModel": "constant",
                    "viscosityValue": 1.8e-5
                })
            if self.case_config.get("energy_active", False):
                default["properties"].update({
                    "cpModel": "constant",
                    "cpValue": 1005.0,
                    "conductivityModel": "constant",
                    "conductivityValue": 0.025
                })
            self.case_config["materials"].append(default)

    def enforce_constant_viscosity_if_no_energy(self):
        if not self.case_config.get("energy_active", False):
            for mat in self.case_config["materials"]:
                props = mat.setdefault("properties", {})
                if "viscosityModel" in props:
                    props["viscosityModel"] = "constant"

    def update_material_list(self):
        mats = self.case_config["materials"]
        self.material_table.setRowCount(len(mats))
        for i, m in enumerate(mats):
            name_item = QTableWidgetItem(m.get("name", ""))
            type_item = QTableWidgetItem(m.get("type", ""))
            name_item.setFlags(Qt.ItemIsEnabled)
            type_item.setFlags(Qt.ItemIsEnabled)
            self.material_table.setItem(i, 0, name_item)
            self.material_table.setItem(i, 1, type_item)

    def populate_thermo_fields(self):
        tp = self.case_config["thermophysicalProperties"]
        self.thermo_type.setCurrentText(tp.get("type", "heRhoThermo"))
        self.mixture.setCurrentText(tp.get("mixture", "reactingMixture"))
        self.transport.setCurrentText(tp.get("transport", "sutherland"))
        self.thermo.setCurrentText(tp.get("thermo", "janaf"))
        self.energy.setCurrentText(tp.get("energy", "sensibleEnthalpy"))
        self.eos.setCurrentText(tp.get("equationOfState", "perfectGas"))
        self.chemkin_dir.setText(tp.get("chemkin_dir", "<case>/chemkin"))
        self.new_format.setChecked(tp.get("newFormat", True))

    def create_material(self):
        text, ok = QInputDialog.getText(self, "Crear Material", "Nombre del nuevo material:")
        if ok and text.strip():
            new_mat = {
                "name": text.strip(),
                "type": "fluid",
                "properties": {"densityModel": "constant", "densityValue": 1.225}
            }
            turb = str(self.case_config.get("turbulenceModel", "")).lower()
            if turb and turb != "laminar":
                new_mat["properties"].update({
                    "viscosityModel": "constant",
                    "viscosityValue": 1.8e-5
                })
            if self.case_config.get("energy_active", False):
                new_mat["properties"].update({
                    "cpModel": "constant",
                    "cpValue": 1005.0,
                    "conductivityModel": "constant",
                    "conductivityValue": 0.025
                })
            self.case_config["materials"].append(new_mat)
            self.update_material_list()
            dlg = ConfigMaterialDialog(
                case_config=self.case_config,
                parent=self,
                select_material=new_mat["name"]
            )
            if dlg.exec_():
                self.update_material_list()

    def configure_material(self):
        if not self.case_config["materials"]:
            QMessageBox.information(self, "Info", "No hay materiales definidos.")
            return
        dlg = ConfigMaterialDialog(case_config=self.case_config, parent=self)
        if dlg.exec_():
            self.update_material_list()

    def delete_material(self):
        row = self.material_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un material para eliminar.")
            return
        name = self.material_table.item(row, 0).text()
        self.case_config["materials"] = [
            m for m in self.case_config["materials"] if m.get("name") != name
        ]
        self.update_material_list()
