# injection_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QDoubleSpinBox, QLabel, QPushButton, QMessageBox, QListWidget, QListWidgetItem, QCheckBox, QWidget
)
from PyQt5.QtCore import Qt

class InjectionDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Inyector")

        self.injection_data = {
            "name": "",
            "type": "patchInjection",
            "parameters": {}
        }

        if initial_data:
            self.injection_data.update(initial_data)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Nombre del inyector
        self.name_input = QLineEdit()
        self.name_input.setText(self.injection_data.get("name", ""))
        form.addRow("Nombre del Inyector:", self.name_input)

        # Tipo de inyector
        self.type_combo = QComboBox()
        self.type_combo.addItems(["patchInjection", "coneNozzleInjection"])
        self.type_combo.setCurrentText(self.injection_data.get("type", "patchInjection"))
        self.type_combo.currentTextChanged.connect(self.update_parameters_form)
        form.addRow("Tipo de Inyector:", self.type_combo)

        # Formulario dinámico para parámetros
        self.parameters_layout = QFormLayout()
        form.addRow(self.parameters_layout)

        layout.addLayout(form)

        # Botones Aceptar/Cancelar
        btn_layout = QHBoxLayout()
        btn_accept = QPushButton("Aceptar")
        btn_cancel = QPushButton("Cancelar")
        btn_accept.clicked.connect(self.accept_changes)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_accept)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)

        self.parameters_widgets = {}

        # Construir el formulario de parámetros según el tipo inicial
        self.update_parameters_form(self.type_combo.currentText())

        # Cargar parámetros iniciales si existen
        if initial_data:
            self.load_initial_parameters()

    def load_initial_parameters(self):
        parameters = self.injection_data.get("parameters", {})
        # Manejar campos individuales primero
        for key, value in parameters.items():
            if key in self.parameters_widgets:
                widget = self.parameters_widgets[key]
                if isinstance(widget, QDoubleSpinBox):
                    widget.setValue(float(value))
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(value))
                elif isinstance(widget, QListWidget):
                    widget.clear()
                    for item in value:
                        list_item = QListWidgetItem(item)
                        list_item.setSelected(True)
                        widget.addItem(list_item)
                elif isinstance(widget, QComboBox):
                    index = widget.findText(value)
                    if index != -1:
                        widget.setCurrentIndex(index)
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))

        # Manejar campos agrupados: position, direction, velocity
        for group_key, axes in [("position", ["x", "y", "z"]), ("direction", ["x", "y", "z"]), ("velocity", ["u", "v", "w"])]:
            if group_key in parameters and isinstance(parameters[group_key], list) and len(parameters[group_key]) == 3:
                values = parameters[group_key]
                for i, axis in enumerate(['x', 'y', 'z']) if group_key in ["position", "direction"] else enumerate(['u', 'v', 'w']):
                    widget_key = f"{group_key}_{axis}"
                    if widget_key in self.parameters_widgets:
                        self.parameters_widgets[widget_key].setValue(float(values[i]))

    def update_parameters_form(self, injection_type):
        # Limpiar el formulario dinámico
        while self.parameters_layout.count():
            child = self.parameters_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.injection_data["parameters"] = {}
        self.parameters_widgets = {}

        if injection_type == "patchInjection":
            self.add_parameter_field("patchName", "Nombre del Patch:", QLineEdit, "")
            self.add_parameter_field("U0", "Velocidad Inicial (U0) [m/s]:", QDoubleSpinBox, 0.0, suffix=" m/s")
            self.add_parameter_field("d", "Diámetro (d) [m]:", QDoubleSpinBox, 0.0, suffix=" m")
            self.add_parameter_field("massFlowRate", "Flujo Másico (massFlowRate) [kg/s]:", QDoubleSpinBox, 0.0, suffix=" kg/s")
        elif injection_type == "coneNozzleInjection":
            # Agregar campos específicos para coneNozzleInjection
            self.add_parameter_field("SOI", "SOI [s]:", QDoubleSpinBox, 0.0, suffix=" s")
            self.add_parameter_field("massTotal", "Mass Total [kg]:", QDoubleSpinBox, 0.0, suffix=" kg")
            self.add_parameter_field("parcelBasisType", "Parcel Basis Type:", QListWidget, [], multiple=True)
            self.add_parameter_field("injectionMethod", "Injection Method:", QListWidget, [], multiple=True)
            self.add_parameter_field("flowType", "Flow Type:", QComboBox, "flowRateAndDischarge")
            self.add_parameter_field("outerDiameter", "Outer Diameter [m]:", QDoubleSpinBox, 0.0, suffix=" m")
            self.add_parameter_field("innerDiameter", "Inner Diameter [m]:", QDoubleSpinBox, 0.0, suffix=" m")
            self.add_parameter_field("duration", "Duration [s]:", QDoubleSpinBox, 0.0, suffix=" s")
            self.add_position_field("position", "Posición (x, y, z) [m]:", "position")
            self.add_direction_field("direction", "Dirección (x, y, z) [m]:", "direction")
            self.add_parameter_field("parcelsPerSecond", "Parcels Per Second [parcels/s]:", QDoubleSpinBox, 0.0, suffix=" parcels/s")
            self.add_flow_rate_profile_field()
            self.add_velocity_field("velocity", "Velocity (U_x, U_y, U_z) [m/s]:", ["velocity_u", "velocity_v", "velocity_w"])
            self.add_cd_field()
            self.add_theta_inner_field()
            self.add_theta_outer_field()
            self.add_size_distribution_field()

    def add_parameter_field(self, key, label, widget_class, default, suffix="", multiple=False):
        if widget_class == QDoubleSpinBox:
            widget = widget_class()
            widget.setRange(-1e6, 1e6)  # Ajustar rango según necesidades
            widget.setValue(default)
            if suffix:
                widget.setSuffix(suffix)
        elif widget_class == QLineEdit:
            widget = widget_class()
            widget.setText(default)
        elif widget_class == QListWidget:
            widget = QListWidget()
            if multiple:
                widget.setSelectionMode(QListWidget.MultiSelection)
            else:
                widget.setSelectionMode(QListWidget.SingleSelection)
            # Inicializar con opciones específicas si es necesario
            if key == "parcelBasisType":
                widget.addItems(["mass"])  # Puedes agregar más opciones según sea necesario
            elif key == "injectionMethod":
                widget.addItems(["disc"])  # Puedes agregar más opciones según sea necesario
            self.parameters_layout.addRow(label, widget)
            self.parameters_widgets[key] = widget
            return  # Retornar para evitar agregar de nuevo en el siguiente bloque
        elif widget_class == QComboBox:
            widget = QComboBox()
            # Dependiendo del campo, agregar opciones específicas
            if key == "flowType":
                # Opciones actualizadas según solicitud
                flow_types = ["constantVelocity", "pressureDrivenVelocity", "flowRateAndDischarge"]
                widget.addItems(flow_types)
                widget.setCurrentText(default)
            elif key == "flowRateProfile":
                widget.addItems(["constant"])  # Inicialmente solo 'constant'
            elif key == "Cd":
                widget.addItems(["constant"])  # Inicialmente solo 'constant'
            elif key == "thetaInner":
                widget.addItems(["constant"])  # Inicialmente solo 'constant'
            elif key == "thetaOuter":
                widget.addItems(["constant"])  # Inicialmente solo 'constant'
            elif key == "sizeDistribution":
                widget.addItems(["RosinRammler"])  # Inicialmente solo 'RosinRammler'
            widget.setCurrentText(default)
        elif widget_class == QCheckBox:
            widget = QCheckBox()
            widget.setChecked(default)
        else:
            widget = widget_class()

        self.parameters_layout.addRow(label, widget)
        self.injection_data["parameters"][key] = default
        self.parameters_widgets[key] = widget

        # Conectar señales para manejar cambios dinámicos
        if isinstance(widget, QComboBox):
            widget.currentTextChanged.connect(self.update_dynamic_field_specific)
        elif isinstance(widget, QListWidget):
            widget.itemSelectionChanged.connect(self.update_dynamic_field_specific)

    def add_position_field(self, key, label, param_key):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        pos_x = QDoubleSpinBox()
        pos_x.setRange(-1e6, 1e6)
        pos_x.setValue(0.0)
        pos_x.setSuffix(" m")
        pos_y = QDoubleSpinBox()
        pos_y.setRange(-1e6, 1e6)
        pos_y.setValue(0.0)
        pos_y.setSuffix(" m")
        pos_z = QDoubleSpinBox()
        pos_z.setRange(-1e6, 1e6)
        pos_z.setValue(0.0)
        pos_z.setSuffix(" m")

        layout.addWidget(QLabel("x:"))
        layout.addWidget(pos_x)
        layout.addWidget(QLabel("y:"))
        layout.addWidget(pos_y)
        layout.addWidget(QLabel("z:"))
        layout.addWidget(pos_z)

        widget.setLayout(layout)
        self.parameters_layout.addRow(label, widget)

        self.parameters_widgets[param_key + "_x"] = pos_x
        self.parameters_widgets[param_key + "_y"] = pos_y
        self.parameters_widgets[param_key + "_z"] = pos_z

    def add_direction_field(self, key, label, param_key):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        dir_x = QDoubleSpinBox()
        dir_x.setRange(-1e6, 1e6)
        dir_x.setValue(0.0)
        dir_x.setSuffix(" m")
        dir_y = QDoubleSpinBox()
        dir_y.setRange(-1e6, 1e6)
        dir_y.setValue(0.0)
        dir_y.setSuffix(" m")
        dir_z = QDoubleSpinBox()
        dir_z.setRange(-1e6, 1e6)
        dir_z.setValue(0.0)
        dir_z.setSuffix(" m")

        layout.addWidget(QLabel("x:"))
        layout.addWidget(dir_x)
        layout.addWidget(QLabel("y:"))
        layout.addWidget(dir_y)
        layout.addWidget(QLabel("z:"))
        layout.addWidget(dir_z)

        widget.setLayout(layout)
        self.parameters_layout.addRow(label, widget)

        self.parameters_widgets[param_key + "_x"] = dir_x
        self.parameters_widgets[param_key + "_y"] = dir_y
        self.parameters_widgets[param_key + "_z"] = dir_z

    def add_velocity_field(self, key, label, param_keys):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        vel_u = QDoubleSpinBox()
        vel_u.setRange(-1e6, 1e6)
        vel_u.setValue(0.0)
        vel_u.setSuffix(" m/s")
        vel_v = QDoubleSpinBox()
        vel_v.setRange(-1e6, 1e6)
        vel_v.setValue(0.0)
        vel_v.setSuffix(" m/s")
        vel_w = QDoubleSpinBox()
        vel_w.setRange(-1e6, 1e6)
        vel_w.setValue(0.0)
        vel_w.setSuffix(" m/s")

        layout.addWidget(QLabel("U_x:"))
        layout.addWidget(vel_u)
        layout.addWidget(QLabel("U_y:"))
        layout.addWidget(vel_v)
        layout.addWidget(QLabel("U_z:"))
        layout.addWidget(vel_w)

        widget.setLayout(layout)
        self.parameters_layout.addRow(label, widget)

        for param_key, spin_box in zip(param_keys, [vel_u, vel_v, vel_w]):
            self.parameters_widgets[param_key] = spin_box

    def add_flow_rate_profile_field(self):
        flow_rate_profile_label = QLabel("Flow Rate Profile:")
        self.flow_rate_profile_combo = QComboBox()
        self.flow_rate_profile_combo.addItems(["constant"])  # Inicialmente solo 'constant'
        self.flow_rate_profile_combo.setCurrentText("constant")
        self.flow_rate_profile_combo.currentTextChanged.connect(self.update_flow_rate_profile)

        self.flow_rate_profile_value = QDoubleSpinBox()
        self.flow_rate_profile_value.setRange(-1e6, 1e6)
        self.flow_rate_profile_value.setValue(0.0)
        self.flow_rate_profile_value.setSuffix(" ")

        # Layout horizontal para Flow Rate Profile y su valor
        flow_rate_layout = QHBoxLayout()
        flow_rate_layout.addWidget(self.flow_rate_profile_combo)
        flow_rate_layout.addWidget(self.flow_rate_profile_value)

        self.parameters_layout.addRow("Flow Rate Profile:", flow_rate_layout)
        self.parameters_widgets["flowRateProfile"] = self.flow_rate_profile_combo
        self.parameters_widgets["flowRateProfileValue"] = self.flow_rate_profile_value

    def update_flow_rate_profile(self, text):
        if text == "constant":
            self.flow_rate_profile_value.setEnabled(True)
        else:
            self.flow_rate_profile_value.setEnabled(False)

    def add_cd_field(self):
        cd_label = QLabel("Cd:")
        self.cd_combo = QComboBox()
        self.cd_combo.addItems(["constant"])  # Inicialmente solo 'constant'
        self.cd_combo.setCurrentText("constant")
        self.cd_combo.currentTextChanged.connect(self.update_cd_field)

        self.cd_value = QDoubleSpinBox()
        self.cd_value.setRange(-1e6, 1e6)
        self.cd_value.setValue(0.0)
        self.cd_value.setSuffix(" ")

        # Layout horizontal para Cd y su valor
        cd_layout = QHBoxLayout()
        cd_layout.addWidget(self.cd_combo)
        cd_layout.addWidget(self.cd_value)

        self.parameters_layout.addRow("Cd:", cd_layout)
        self.parameters_widgets["Cd"] = self.cd_combo
        self.parameters_widgets["CdValue"] = self.cd_value

    def update_cd_field(self, text):
        if text == "constant":
            self.cd_value.setEnabled(True)
        else:
            self.cd_value.setEnabled(False)

    def add_theta_inner_field(self):
        theta_inner_label = QLabel("Theta Inner:")
        self.theta_inner_combo = QComboBox()
        self.theta_inner_combo.addItems(["constant"])  # Inicialmente solo 'constant'
        self.theta_inner_combo.setCurrentText("constant")
        self.theta_inner_combo.currentTextChanged.connect(self.update_theta_inner_field)

        self.theta_inner_value = QDoubleSpinBox()
        self.theta_inner_value.setRange(-1e6, 1e6)
        self.theta_inner_value.setValue(0.0)
        self.theta_inner_value.setSuffix(" ")

        # Layout horizontal para Theta Inner y su valor
        theta_inner_layout = QHBoxLayout()
        theta_inner_layout.addWidget(self.theta_inner_combo)
        theta_inner_layout.addWidget(self.theta_inner_value)

        self.parameters_layout.addRow("Theta Inner:", theta_inner_layout)
        self.parameters_widgets["thetaInner"] = self.theta_inner_combo
        self.parameters_widgets["thetaInnerValue"] = self.theta_inner_value

    def update_theta_inner_field(self, text):
        if text == "constant":
            self.theta_inner_value.setEnabled(True)
        else:
            self.theta_inner_value.setEnabled(False)

    def add_theta_outer_field(self):
        theta_outer_label = QLabel("Theta Outer:")
        self.theta_outer_combo = QComboBox()
        self.theta_outer_combo.addItems(["constant"])  # Inicialmente solo 'constant'
        self.theta_outer_combo.setCurrentText("constant")
        self.theta_outer_combo.currentTextChanged.connect(self.update_theta_outer_field)

        self.theta_outer_value = QDoubleSpinBox()
        self.theta_outer_value.setRange(-1e6, 1e6)
        self.theta_outer_value.setValue(0.0)
        self.theta_outer_value.setSuffix(" ")

        # Layout horizontal para Theta Outer y su valor
        theta_outer_layout = QHBoxLayout()
        theta_outer_layout.addWidget(self.theta_outer_combo)
        theta_outer_layout.addWidget(self.theta_outer_value)

        self.parameters_layout.addRow("Theta Outer:", theta_outer_layout)
        self.parameters_widgets["thetaOuter"] = self.theta_outer_combo
        self.parameters_widgets["thetaOuterValue"] = self.theta_outer_value

    def update_theta_outer_field(self, text):
        if text == "constant":
            self.theta_outer_value.setEnabled(True)
        else:
            self.theta_outer_value.setEnabled(False)

    def add_size_distribution_field(self):
        size_dist_label = QLabel("Size Distribution:")
        self.size_distribution_combo = QComboBox()
        self.size_distribution_combo.addItems(["RosinRammler"])  # Inicialmente solo 'RosinRammler'
        self.size_distribution_combo.setCurrentText("RosinRammler")
        self.size_distribution_combo.currentTextChanged.connect(self.update_size_distribution_field)

        self.parameters_layout.addRow("Size Distribution:", self.size_distribution_combo)
        self.parameters_widgets["sizeDistribution"] = self.size_distribution_combo

        # Campos para RosinRammler
        self.size_distribution_min = QDoubleSpinBox()
        self.size_distribution_min.setRange(-1e6, 1e6)
        self.size_distribution_min.setValue(0.0)
        self.size_distribution_min.setSuffix(" ")

        self.size_distribution_max = QDoubleSpinBox()
        self.size_distribution_max.setRange(-1e6, 1e6)
        self.size_distribution_max.setValue(0.0)
        self.size_distribution_max.setSuffix(" ")

        self.size_distribution_lambda = QDoubleSpinBox()
        self.size_distribution_lambda.setRange(-1e6, 1e6)
        self.size_distribution_lambda.setValue(0.0)
        self.size_distribution_lambda.setSuffix(" ")

        self.size_distribution_n = QDoubleSpinBox()
        self.size_distribution_n.setRange(-1e6, 1e6)
        self.size_distribution_n.setValue(0.0)
        self.size_distribution_n.setSuffix(" ")

        # Layout para Size Distribution RosinRammler
        size_dist_rosin_layout = QFormLayout()
        size_dist_rosin_layout.addRow("Min Value:", self.size_distribution_min)
        size_dist_rosin_layout.addRow("Max Value:", self.size_distribution_max)
        size_dist_rosin_layout.addRow("Lambda:", self.size_distribution_lambda)
        size_dist_rosin_layout.addRow("n:", self.size_distribution_n)

        self.size_distribution_rosin_widget = QWidget()
        self.size_distribution_rosin_widget.setLayout(size_dist_rosin_layout)
        self.parameters_layout.addRow("Size Distribution Parameters:", self.size_distribution_rosin_widget)
        self.size_distribution_rosin_widget.setVisible(True)  # Inicialmente visible

        self.parameters_widgets["sizeDistribution_minValue"] = self.size_distribution_min
        self.parameters_widgets["sizeDistribution_maxValue"] = self.size_distribution_max
        self.parameters_widgets["sizeDistribution_lambda"] = self.size_distribution_lambda
        self.parameters_widgets["sizeDistribution_n"] = self.size_distribution_n

    def update_size_distribution_field(self, text):
        if text == "RosinRammler":
            self.size_distribution_rosin_widget.setVisible(True)
        else:
            self.size_distribution_rosin_widget.setVisible(False)

    def accept_changes(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "El nombre del inyector no puede estar vacío.")
            return

        self.injection_data["name"] = name
        self.injection_data["type"] = self.type_combo.currentText()

        # Guardar parámetros
        for key, widget in self.parameters_widgets.items():
            if key.startswith("position_") or key.startswith("direction_") or key.startswith("velocity_"):
                # Estos campos se agruparán más adelante
                continue
            if isinstance(widget, QDoubleSpinBox):
                self.injection_data["parameters"][key] = widget.value()
            elif isinstance(widget, QLineEdit):
                self.injection_data["parameters"][key] = widget.text().strip()
            elif isinstance(widget, QListWidget):
                selected_items = widget.selectedItems()
                self.injection_data["parameters"][key] = [item.text() for item in selected_items]
            elif isinstance(widget, QComboBox):
                self.injection_data["parameters"][key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                self.injection_data["parameters"][key] = widget.isChecked()

        # Agrupar campos de posición, dirección y velocidad
        for group_key, axes in [("position", ["x", "y", "z"]), ("direction", ["x", "y", "z"]), ("velocity", ["u", "v", "w"])]:
            group_values = []
            for axis in axes:
                widget_key = f"{group_key}_{axis}"
                if widget_key in self.parameters_widgets:
                    group_values.append(self.parameters_widgets[widget_key].value())
            if group_values:
                self.injection_data["parameters"][group_key] = group_values
                # Eliminar los campos individuales
                for axis in axes:
                    widget_key = f"{group_key}_{axis}"
                    self.injection_data["parameters"].pop(widget_key, None)

        # Validaciones adicionales para coneNozzleInjection
        if self.injection_data["type"] == "coneNozzleInjection":
            required_fields = [
                "SOI", "massTotal", "parcelBasisType", "injectionMethod",
                "flowType", "outerDiameter", "innerDiameter", "duration",
                "position", "direction", "parcelsPerSecond",
                "flowRateProfile", "flowRateProfileValue", "velocity",
                "Cd", "CdValue", "thetaInner", "thetaInnerValue",
                "thetaOuter", "thetaOuterValue", "sizeDistribution",
                "sizeDistribution_minValue", "sizeDistribution_maxValue",
                "sizeDistribution_lambda", "sizeDistribution_n"
            ]
            missing_fields = [field for field in required_fields if field not in self.injection_data["parameters"]]
            if missing_fields:
                QMessageBox.warning(self, "Error", f"Los siguientes campos son requeridos para coneNozzleInjection: {', '.join(missing_fields)}.")
                return

        self.accept()

    def update_dynamic_field_specific(self, text):
        """
        Método genérico para manejar actualizaciones dinámicas específicas.
        Puede ser extendido si se necesitan manejos adicionales.
        """
        pass  # Actualmente, no se necesita ninguna acción adicional
