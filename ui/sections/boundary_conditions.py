# ui/sections/boundary_conditions.py

import os
import json
import logging

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QHeaderView, QDialog, QComboBox, QStyledItemDelegate, QMessageBox
)
from ui.widgets.numeric_line_edit import NumericLineEdit
from PyQt5.QtCore import Qt, pyqtSignal

from ui.dialogs.wall_bc_dialog import WallBCDialog
from ui.dialogs.inlet_bc_dialog import InletBCDialog
from ui.dialogs.inlet_outlet_bc_dialog import InletOutletBCDialog
from core.json_manager import JSONManager  # Manejo de JSON


class ComboBoxDelegate(QStyledItemDelegate):
    """
    Delegate para la columna que permite seleccionar el tipo de frontera mediante un desplegable.
    Las opciones disponibles son: Inlet, Outlet, Wall, Symmetry y Periodicity.
    """
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(["Inlet", "Outlet", "Wall", "Symmetry", "Periodicity"])
        return combo

    def setEditorData(self, editor, index):
        value = index.data(Qt.EditRole)
        idx = editor.findText(value)
        if idx >= 0:
            editor.setCurrentIndex(idx)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)


class BoundaryItem(QTreeWidgetItem):
    """
    QTreeWidgetItem personalizado para que la columna del nombre sea de solo lectura
    y únicamente la columna del tipo sea editable.
    """
    def __init__(self, strings):
        super().__init__(strings)

    def flags(self, column):
        base_flags = super().flags(column)
        if column == 0:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        else:
            return base_flags | Qt.ItemIsEditable


class BoundaryConditions(QWidget):
    """
    Ventana para administrar las condiciones de contorno del caso.
    
    En esta interfaz se pueden revisar y editar las fronteras definidas en el modelo.
    Cada frontera se muestra con un nombre (no editable) y se le puede asignar un tipo mediante un desplegable
    (opciones: Inlet, Outlet, Wall, Symmetry y Periodicity). Además, se configuran variables ambientales como la
    presión y la temperatura. Doble clic sobre una frontera abrirá su ventana de configuración específica.
    
    La configuración del modelo se carga desde 'temp/constant.json'. Por ejemplo, si en constant.json se establece
    "especiesActive": true, se asignarán las especies activas al parámetro chosen_species.
    
    Además, si la opción de química no está activada, se eliminará toda la información relacionada con las especies
    al guardar boundary_conditions.json (el archivo se sobrescribe por completo con la última información de la interfaz).
    """
    data_changed = pyqtSignal()

    def __init__(self, case_config):
        super().__init__()
        self.case_config = case_config
        self.json_manager = JSONManager()
        self.section_name = "boundary_conditions"

        self.init_ui()
        self.load_model_config()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Boundary Conditions")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        # Descripción genérica
        description = QLabel(
            "Esta ventana permite administrar las condiciones de contorno del caso.\n"
            "Podrá revisar y editar las fronteras definidas en el modelo, asignar a cada una "
            "su tipo mediante el desplegable (opciones: Inlet, Outlet, Wall, Symmetry y Periodicity),\n"
            "y configurar variables ambientales como la presión y la temperatura.\n"
            "Doble clic sobre una frontera abrirá su ventana de configuración específica."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # Árbol para las fronteras
        self.bc_tree = QTreeWidget()
        self.bc_tree.setHeaderLabels(["Nombre", "Tipo"])
        self.bc_tree.header().setSectionResizeMode(QHeaderView.Stretch)
        self.bc_tree.setItemDelegateForColumn(1, ComboBoxDelegate())
        self.bc_tree.setEditTriggers(QTreeWidget.EditKeyPressed | QTreeWidget.SelectedClicked)
        self.bc_tree.setSelectionBehavior(QTreeWidget.SelectRows)
        self.bc_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.bc_tree.itemChanged.connect(self.on_bc_item_changed)
        self.bc_tree.itemDoubleClicked.connect(self.on_bc_double_clicked)
        layout.addWidget(self.bc_tree)

        # Presión ambiente
        pressure_layout = QHBoxLayout()
        pressure_label = QLabel("Presión Ambiente (Pa):")
        self.pressure_input = NumericLineEdit()
        self.pressure_input.setPlaceholderText("Ingrese valor de la presión ambiente")
        self.pressure_input.setText(str(self.case_config.get("ambientPressure", 101325)))
        self.pressure_input.editingFinished.connect(self.update_ambient_pressure)
        pressure_layout.addWidget(pressure_label)
        pressure_layout.addWidget(self.pressure_input)
        layout.addLayout(pressure_layout)

        # Temperatura ambiente
        temperature_layout = QHBoxLayout()
        temperature_label = QLabel("Temperatura Ambiente (K):")
        self.temperature_input = NumericLineEdit()
        self.temperature_input.setPlaceholderText("Ingrese valor de la temperatura ambiente")
        self.temperature_input.setText(str(self.case_config.get("ambientTemperature", 300.0)))
        self.temperature_input.editingFinished.connect(self.update_ambient_temperature)
        temperature_layout.addWidget(temperature_label)
        temperature_layout.addWidget(self.temperature_input)
        layout.addLayout(temperature_layout)

        layout.addStretch()
        self.setLayout(layout)
        self.update_bc_tree()

    def load_model_config(self):
        constant_path = os.path.join("temp", "constant.json")
        if os.path.exists(constant_path):
            try:
                with open(constant_path, "r") as f:
                    model_config = json.load(f)
                self.case_config["turbulenceModel"] = model_config.get("turbulenceModel", "laminar")
                if isinstance(self.case_config["turbulenceModel"], dict):
                    tm = self.case_config["turbulenceModel"].get("model", "laminar")
                    self.case_config["turbulenceActive"] = (tm.lower() != "laminar")
                else:
                    self.case_config["turbulenceActive"] = (self.case_config["turbulenceModel"].lower() != "laminar")
                self.case_config["chemistryActive"] = model_config.get("especiesActive", False)
                if self.case_config["chemistryActive"]:
                    especies_options = model_config.get("especies_options", {})
                    self.case_config["chosen_species"] = especies_options.get("activeSpecies", [])
                else:
                    self.case_config["chosen_species"] = []
                logging.info("Configuración del modelo cargada desde constant.json")
            except Exception as e:
                logging.error(f"Error al leer constant.json: {e}")
        else:
            logging.info("No se encontró constant.json. Se usarán valores por defecto.")

    def update_bc_tree(self):
        self.bc_tree.blockSignals(True)
        self.bc_tree.clear()
        boundary_conditions = self.case_config.get("boundaryConditions", {})
        for bname, bc_details in boundary_conditions.items():
            item = BoundaryItem([bname, bc_details.get("type", "Inlet")])
            item.setData(0, Qt.UserRole, {"original_name": bname})
            self.bc_tree.addTopLevelItem(item)
        self.bc_tree.expandAll()
        self.bc_tree.blockSignals(False)

    def on_bc_item_changed(self, item, column):
        if column != 1:
            return
        data = item.data(0, Qt.UserRole)
        original_name = data.get("original_name") if data else None
        new_type = item.text(1).strip()
        bc_dict = self.case_config.get("boundaryConditions", {})
        if original_name in bc_dict:
            bc_dict[original_name]["type"] = new_type
        else:
            bc_dict[original_name] = {"type": new_type}
        self.data_changed.emit()

    def on_bc_double_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if not data or "original_name" not in data:
            return
        bname = data["original_name"]
        bc_data = self.case_config["boundaryConditions"].get(bname, {})
        btype = bc_data.get("type", "").lower()
        turbulence_model = self.case_config.get("turbulenceModel", "laminar")
        chemistryActive = self.case_config.get("chemistryActive", False)
        chosen_species = self.case_config.get("chosen_species", [])
        if btype == "inlet":
            dlg = InletBCDialog(
                parent=self,
                turbulenceModel=turbulence_model,
                chemistryActive=chemistryActive,
                chosen_species=chosen_species,
                initial_data=bc_data
            )
        elif btype == "outlet":
            dlg = InletOutletBCDialog(
                parent=self,
                turbulenceModel=turbulence_model,
                chemistryActive=chemistryActive,
                chosen_species=chosen_species,
                initial_data=bc_data
            )
        elif btype == "wall":
            dlg = WallBCDialog(
                parent=self,
                turbulenceModel=turbulence_model,
                chemistryActive=chemistryActive,
                chosen_species=chosen_species,
                initial_data=bc_data
            )
        elif btype in ("symmetry", "periodicity"):
            QMessageBox.information(
                self,
                "Información",
                f"La configuración para el tipo de frontera '{btype}' se implementará próximamente."
            )
            return
        else:
            QMessageBox.information(
                self,
                "Información",
                f"No se ha definido una ventana de configuración para el tipo de frontera '{btype}'."
            )
            return

        if dlg and dlg.exec_() == QDialog.Accepted:
            updated_data = dlg.get_bc_data()
            self.case_config["boundaryConditions"][bname] = updated_data
            logging.info(f"BoundaryConditions: Actualizado '{bname}': {updated_data}")
            self.update_bc_tree()
            self.data_changed.emit()

    def update_ambient_pressure(self):
        text = self.pressure_input.text().strip()
        try:
            pressure = float(text)
            self.case_config["ambientPressure"] = pressure
            self.data_changed.emit()
            logging.info(f"Ambient Pressure updated to: {pressure}")
        except ValueError:
            self.pressure_input.setText(str(self.case_config.get("ambientPressure", 101325)))

    def update_ambient_temperature(self):
        text = self.temperature_input.text().strip()
        try:
            temperature = float(text)
            self.case_config["ambientTemperature"] = temperature
            self.data_changed.emit()
            logging.info(f"Ambient Temperature updated to: {temperature}")
        except ValueError:
            self.temperature_input.setText(str(self.case_config.get("ambientTemperature", 300.0)))

    def collect_data(self):
        data = {
            "ambientPressure": self.case_config.get("ambientPressure", 101325),
            "ambientTemperature": self.case_config.get("ambientTemperature", 300.0),
            "boundaryConditions": {},
            "chemistryActive": self.case_config.get("chemistryActive", False),
            "chosen_species": self.case_config.get("chosen_species", [])
        }
        current_bcs = self.case_config.get("boundaryConditions", {})
        for bc_name, bc in current_bcs.items():
            data["boundaryConditions"][bc_name] = bc.copy()

        # Manejo de la turbulencia: si es dict, extraer "model" y convertir a minúsculas.
        tm = self.case_config.get("turbulenceModel", "laminar")
        if isinstance(tm, dict):
            turbulenceModel = tm.get("model", "laminar").lower()
        else:
            turbulenceModel = tm.lower()

        turbulenceActive = self.case_config.get("turbulenceActive", False)
        if not turbulenceActive:
            data["Turbulence_model"] = False
        else:
            if turbulenceModel == "kepsilon":
                data["Turbulence_model"] = "kEpsilon"
            elif turbulenceModel == "komega":
                data["Turbulence_model"] = "kOmega"
            else:
                data["Turbulence_model"] = "laminar"

        if not data["chemistryActive"]:
            for bc_info in data["boundaryConditions"].values():
                keys_to_remove = [k for k in bc_info.keys() if k.endswith("_chemType") or k.endswith("_chemValue")]
                for key_rm in keys_to_remove:
                    bc_info.pop(key_rm, None)
            if "chosen_species" in data:
                del data["chosen_species"]
            data["chemistryActive"] = False

        logging.info("Recopilando datos para boundary_conditions.json:")
        logging.debug(json.dumps(data, indent=4))
        return data

    def save_boundary_conditions(self):
        data = self.collect_data()
        success, msg = self.json_manager.save_section(self.section_name, data)
        if success:
            logging.info("Boundary Conditions guardadas automáticamente.")
        else:
            logging.error(f"Error al guardar Boundary Conditions: {msg}")

    def load_data(self):
        temp_dir = "temp"
        json_path = os.path.join(temp_dir, "boundary_conditions.json")
        if os.path.exists(json_path):
            data = self.json_manager.load_section(self.section_name)
        else:
            data = None

        if data:
            self.case_config["ambientPressure"] = data.get("ambientPressure", 101325)
            self.pressure_input.setText(str(self.case_config["ambientPressure"]))
            self.case_config["ambientTemperature"] = data.get("ambientTemperature", 300.0)
            self.temperature_input.setText(str(self.case_config["ambientTemperature"]))
            self.case_config["boundaryConditions"] = data.get("boundaryConditions", {})
            self.case_config["chemistryActive"] = data.get("chemistryActive", self.case_config.get("chemistryActive", False))
            self.case_config["chosen_species"] = data.get("chosen_species", self.case_config.get("chosen_species", []))
            logging.info("Boundary Conditions cargadas desde boundary_conditions.json")
            logging.debug(json.dumps(self.case_config["boundaryConditions"], indent=4))
            self.update_bc_tree()
        else:
            logging.info("No se encontró boundary_conditions.json. Usando valores por defecto.")
            self.update_bc_tree()

    def hideEvent(self, event):
        self.save_boundary_conditions()
        super().hideEvent(event)

    def open_gravity_config(self):
        dlg = ConfGravDialog(parent=self, initial_data={"gravity_vector": self.case_config.get("gravity_vector", [0.0, 0.0, -1.0])})
        if dlg.exec_() == QDialog.Accepted:
            self.case_config["gravity_vector"] = dlg.data["gravity_vector"]

    def open_radiation_options_dialog(self):
        dlg = RadiationOptionsDialog(parent=self, initial_data=self.case_config.get("radiation_options", {}))
        if dlg.exec_() == QDialog.Accepted:
            self.case_config["radiation_options"] = dlg.radiation_data

    def open_especies_config_dialog(self):
        dlg = EspeciesConfigDialog(parent=self, initial_data=self.case_config.get("especies_options", {}))
        if dlg.exec_() == QDialog.Accepted:
            self.case_config["especies_options"] = dlg.data

    def _read_constant_json(self):
        constant_path = os.path.join(os.getcwd(), "temp", "constant.json")
        if os.path.exists(constant_path):
            try:
                with open(constant_path, "r") as f:
                    data = json.load(f)
                for key, val in data.items():
                    self.case_config[key] = val
            except Exception:
                pass
