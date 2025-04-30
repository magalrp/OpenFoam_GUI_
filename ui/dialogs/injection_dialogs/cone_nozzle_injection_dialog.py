# ui/dialogs/injection_dialogs/cone_nozzle_injection_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QLabel, QPushButton, QMessageBox, QListWidget, QWidget
)
from PyQt5.QtCore import Qt, QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator
from ui.widgets.numeric_line_edit import NumericLineEdit

class ConeNozzleInjectionDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de ConeNozzleInjection")

        self.injection_data = {
            "name": "",
            "type": "coneNozzleInjection",
            "parameters": {}
        }

        if initial_data:
            self.injection_data.update(initial_data)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Inicializar parámetros_layout y parameters_widgets
        self.parameters_layout = form
        self.parameters_widgets = {}

        # Nombre del inyector
        self.name_input = NumericLineEdit()
        self.name_input.setText(self.injection_data.get("name", ""))
        form.addRow("Nombre del Inyector:", self.name_input)

        # SOI
        soi_label = QLabel("SOI [s]:")
        soi_layout = QHBoxLayout()
        self.soi_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("SOI", 0.0)
        )
        soi_layout.addWidget(self.soi_input)
        soi_layout.addWidget(QLabel("s"))
        form.addRow(soi_label, soi_layout)

        # Mass Total
        mass_total_label = QLabel("Mass Total [kg]:")
        mass_total_layout = QHBoxLayout()
        self.mass_total_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("massTotal", 0.0)
        )
        mass_total_layout.addWidget(self.mass_total_input)
        mass_total_layout.addWidget(QLabel("kg"))
        form.addRow(mass_total_label, mass_total_layout)

        # Outer Diameter
        outer_diameter_label = QLabel("Outer Diameter [m]:")
        outer_diameter_layout = QHBoxLayout()
        self.outer_diameter_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("outerDiameter", 0.0)
        )
        outer_diameter_layout.addWidget(self.outer_diameter_input)
        outer_diameter_layout.addWidget(QLabel("m"))
        form.addRow(outer_diameter_label, outer_diameter_layout)

        # Inner Diameter
        inner_diameter_label = QLabel("Inner Diameter [m]:")
        inner_diameter_layout = QHBoxLayout()
        self.inner_diameter_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("innerDiameter", 0.0)
        )
        inner_diameter_layout.addWidget(self.inner_diameter_input)
        inner_diameter_layout.addWidget(QLabel("m"))
        form.addRow(inner_diameter_label, inner_diameter_layout)

        # Duration
        duration_label = QLabel("Duration [s]:")
        duration_layout = QHBoxLayout()
        self.duration_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("duration", 0.0)
        )
        duration_layout.addWidget(self.duration_input)
        duration_layout.addWidget(QLabel("s"))
        form.addRow(duration_label, duration_layout)

        # Parcel Basis Type
        parcel_basis_label = QLabel("Parcel Basis Type:")
        self.parcel_basis_list = QListWidget()
        self.parcel_basis_list.setSelectionMode(QListWidget.MultiSelection)
        self.parcel_basis_list.addItems(["mass"])  # Puedes agregar más opciones según sea necesario
        selected_parcel_basis = self.injection_data.get("parameters", {}).get("parcelBasisType", [])
        for item_text in selected_parcel_basis:
            items = self.parcel_basis_list.findItems(item_text, Qt.MatchExactly)
            for item in items:
                item.setSelected(True)
        form.addRow(parcel_basis_label, self.parcel_basis_list)

        # Injection Method
        injection_method_label = QLabel("Injection Method:")
        self.injection_method_list = QListWidget()
        self.injection_method_list.setSelectionMode(QListWidget.MultiSelection)
        self.injection_method_list.addItems(["disc"])  # Puedes agregar más opciones según sea necesario
        selected_injection_method = self.injection_data.get("parameters", {}).get("injectionMethod", [])
        for item_text in selected_injection_method:
            items = self.injection_method_list.findItems(item_text, Qt.MatchExactly)
            for item in items:
                item.setSelected(True)
        form.addRow(injection_method_label, self.injection_method_list)

        # Flow Type
        flow_type_label = QLabel("Flow Type:")
        self.flow_type_combo = QComboBox()
        flow_types = ["constantVelocity", "pressureDrivenVelocity", "flowRateAndDischarge"]
        self.flow_type_combo.addItems(flow_types)
        self.flow_type_combo.setCurrentText(self.injection_data.get("parameters", {}).get("flowType", "flowRateAndDischarge"))
        form.addRow(flow_type_label, self.flow_type_combo)

        # Velocity
        velocity_label = QLabel("Velocity (m/s):")
        velocity_widget = QWidget()
        velocity_layout = QHBoxLayout()
        velocity_layout.setContentsMargins(0, 0, 0, 0)

        self.velocity_u = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("velocity", [0.0, 0.0, 0.0])[0] if isinstance(self.injection_data.get("parameters", {}).get("velocity", []), list) else 0.0
        )
        self.velocity_v = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("velocity", [0.0, 0.0, 0.0])[1] if isinstance(self.injection_data.get("parameters", {}).get("velocity", []), list) else 0.0
        )
        self.velocity_z = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("velocity", [0.0, 0.0, 0.0])[2] if isinstance(self.injection_data.get("parameters", {}).get("velocity", []), list) else 0.0
        )

        velocity_layout.addWidget(QLabel("U_x:"))
        velocity_layout.addWidget(self.velocity_u)
        velocity_layout.addWidget(QLabel("U_y:"))
        velocity_layout.addWidget(self.velocity_v)
        velocity_layout.addWidget(QLabel("U_z:"))
        velocity_layout.addWidget(self.velocity_z)

        velocity_widget.setLayout(velocity_layout)
        form.addRow(velocity_label, velocity_widget)

        # Parcels Per Second
        parcels_label = QLabel("Parcels Per Second [parcels/s]:")
        parcels_layout = QHBoxLayout()
        self.parcels_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("parcelsPerSecond", 0.0)
        )
        parcels_layout.addWidget(self.parcels_input)
        parcels_layout.addWidget(QLabel("parcels/s"))
        form.addRow(parcels_label, parcels_layout)

        # Position
        position_label = QLabel("Position (x, y, z) [m]:")
        position_widget = QWidget()
        position_layout = QHBoxLayout()
        position_layout.setContentsMargins(0, 0, 0, 0)

        self.position_x = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("position", [0.0, 0.0, 0.0])[0] if isinstance(self.injection_data.get("parameters", {}).get("position", []), list) else 0.0
        )
        self.position_y = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("position", [0.0, 0.0, 0.0])[1] if isinstance(self.injection_data.get("parameters", {}).get("position", []), list) else 0.0
        )
        self.position_z = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("position", [0.0, 0.0, 0.0])[2] if isinstance(self.injection_data.get("parameters", {}).get("position", []), list) else 0.0
        )

        position_layout.addWidget(QLabel("x:"))
        position_layout.addWidget(self.position_x)
        position_layout.addWidget(QLabel("y:"))
        position_layout.addWidget(self.position_y)
        position_layout.addWidget(QLabel("z:"))
        position_layout.addWidget(self.position_z)

        position_widget.setLayout(position_layout)
        form.addRow(position_label, position_widget)

        # Flow Rate Profile
        self.add_flow_rate_profile_field()

        # Cd
        self.add_cd_field()

        # Theta Inner
        self.add_theta_inner_field()

        # Theta Outer
        self.add_theta_outer_field()

        # Size Distribution
        self.add_size_distribution_field()

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

        # Cargar parámetros iniciales si existen
        if initial_data:
            self.load_initial_parameters()

    def create_scientific_line_edit(self, default=0.0):
        """
        Crea un QLineEdit con un validador que permite números en notación científica.
        """
        line_edit = NumericLineEdit()
        regex = QRegularExpression(r'^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$')
        validator = QRegularExpressionValidator(regex)
        line_edit.setValidator(validator)
        line_edit.setText(str(default))
        return line_edit

    def add_flow_rate_profile_field(self):
        flow_rate_profile_label = QLabel("Flow Rate Profile:")
        self.flow_rate_profile_combo = QComboBox()
        self.flow_rate_profile_combo.addItems(["RosinRammlerDistribution"])  # Solo una opción actualmente
        self.flow_rate_profile_combo.setCurrentText("RosinRammlerDistribution")
        self.flow_rate_profile_combo.currentTextChanged.connect(self.update_size_distribution_field)

        # Layout horizontal para Flow Rate Profile
        flow_rate_layout = QHBoxLayout()
        flow_rate_layout.addWidget(self.flow_rate_profile_combo)

        self.parameters_layout.addRow("Flow Rate Profile:", flow_rate_layout)

        # Inicialmente mostrar los campos para RosinRammlerDistribution
        self.size_distribution_params_widget = QWidget()
        size_dist_layout = QFormLayout()

        self.size_min_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("sizeDistribution_minValue", 0.0)
        )
        size_dist_layout.addRow("Min Value:", self.size_min_input)

        self.size_max_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("sizeDistribution_maxValue", 0.0)
        )
        size_dist_layout.addRow("Max Value:", self.size_max_input)

        self.size_lambda_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("sizeDistribution_lambda", 0.0)
        )
        size_dist_layout.addRow("Lambda:", self.size_lambda_input)

        self.size_n_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("sizeDistribution_n", 0.0)
        )
        size_dist_layout.addRow("n:", self.size_n_input)

        self.size_distribution_params_widget.setLayout(size_dist_layout)
        self.parameters_layout.addRow("Size Distribution Parameters:", self.size_distribution_params_widget)
        self.size_distribution_params_widget.setVisible(True)  # Inicialmente visible

    def update_size_distribution_field(self, text):
        """
        Muestra u oculta los campos de parámetros según el tipo de distribución seleccionado.
        Actualmente, solo "RosinRammlerDistribution" está disponible.
        """
        if text == "RosinRammlerDistribution":
            self.size_distribution_params_widget.setVisible(True)
        else:
            self.size_distribution_params_widget.setVisible(False)

    def add_cd_field(self):
        cd_label = QLabel("Cd:")
        self.cd_combo = QComboBox()
        self.cd_combo.addItems(["constant"])  # Inicialmente solo 'constant'
        self.cd_combo.setCurrentText("constant")
        self.cd_combo.currentTextChanged.connect(self.update_cd_field)

        cd_layout = QHBoxLayout()
        cd_layout.addWidget(self.cd_combo)

        self.cd_value = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("CdValue", 0.0)
        )
        cd_layout.addWidget(self.cd_value)

        cd_layout.addWidget(QLabel(""))  # Espacio para alinear con otros campos

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

        theta_inner_layout = QHBoxLayout()
        theta_inner_layout.addWidget(self.theta_inner_combo)

        self.theta_inner_value = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("thetaInnerValue", 0.0)
        )
        theta_inner_layout.addWidget(self.theta_inner_value)

        theta_inner_layout.addWidget(QLabel(""))  # Espacio para alinear con otros campos

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

        theta_outer_layout = QHBoxLayout()
        theta_outer_layout.addWidget(self.theta_outer_combo)

        self.theta_outer_value = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("thetaOuterValue", 0.0)
        )
        theta_outer_layout.addWidget(self.theta_outer_value)

        theta_outer_layout.addWidget(QLabel(""))  # Espacio para alinear con otros campos

        self.parameters_layout.addRow("Theta Outer:", theta_outer_layout)
        self.parameters_widgets["thetaOuter"] = self.theta_outer_combo
        self.parameters_widgets["thetaOuterValue"] = self.theta_outer_value

    def update_theta_outer_field(self, text):
        if text == "constant":
            self.theta_outer_value.setEnabled(True)
        else:
            self.theta_outer_value.setEnabled(False)

    def add_size_distribution_field(self):
        # Ya implementado en add_flow_rate_profile_field
        pass

    def accept_changes(self):
        # Nombre del Inyector
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "El nombre del inyector no puede estar vacío.")
            return
        self.injection_data["name"] = name

        # SOI
        soi_text = self.soi_input.text().strip()
        if soi_text:
            try:
                soi = float(soi_text)
                self.injection_data["parameters"]["SOI"] = soi
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para SOI.")
                return
        else:
            QMessageBox.warning(self, "Error", "SOI no puede estar vacío.")
            return

        # Mass Total
        mass_total_text = self.mass_total_input.text().strip()
        if mass_total_text:
            try:
                mass_total = float(mass_total_text)
                self.injection_data["parameters"]["massTotal"] = mass_total
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Mass Total.")
                return
        else:
            QMessageBox.warning(self, "Error", "Mass Total no puede estar vacío.")
            return

        # Outer Diameter
        outer_diameter_text = self.outer_diameter_input.text().strip()
        if outer_diameter_text:
            try:
                outer_diameter = float(outer_diameter_text)
                self.injection_data["parameters"]["outerDiameter"] = outer_diameter
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Outer Diameter.")
                return
        else:
            QMessageBox.warning(self, "Error", "Outer Diameter no puede estar vacío.")
            return

        # Inner Diameter
        inner_diameter_text = self.inner_diameter_input.text().strip()
        if inner_diameter_text:
            try:
                inner_diameter = float(inner_diameter_text)
                self.injection_data["parameters"]["innerDiameter"] = inner_diameter
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Inner Diameter.")
                return
        else:
            QMessageBox.warning(self, "Error", "Inner Diameter no puede estar vacío.")
            return

        # Duration
        duration_text = self.duration_input.text().strip()
        if duration_text:
            try:
                duration = float(duration_text)
                self.injection_data["parameters"]["duration"] = duration
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Duration.")
                return
        else:
            QMessageBox.warning(self, "Error", "Duration no puede estar vacío.")
            return

        # Flow Rate Profile y Size Distribution
        size_distribution_type = self.flow_rate_profile_combo.currentText()
        self.injection_data["parameters"]["sizeDistribution"] = size_distribution_type

        # Size Distribution Parameters
        size_min_text = self.size_min_input.text().strip()
        size_max_text = self.size_max_input.text().strip()
        size_lambda_text = self.size_lambda_input.text().strip()
        size_n_text = self.size_n_input.text().strip()

        if size_min_text:
            try:
                size_min = float(size_min_text)
                self.injection_data["parameters"]["sizeDistribution_minValue"] = size_min
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Size Distribution Min Value.")
                return
        else:
            QMessageBox.warning(self, "Error", "Size Distribution Min Value no puede estar vacío.")
            return

        if size_max_text:
            try:
                size_max = float(size_max_text)
                self.injection_data["parameters"]["sizeDistribution_maxValue"] = size_max
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Size Distribution Max Value.")
                return
        else:
            QMessageBox.warning(self, "Error", "Size Distribution Max Value no puede estar vacío.")
            return

        if size_lambda_text:
            try:
                size_lambda = float(size_lambda_text)
                self.injection_data["parameters"]["sizeDistribution_lambda"] = size_lambda
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Size Distribution Lambda.")
                return
        else:
            QMessageBox.warning(self, "Error", "Size Distribution Lambda no puede estar vacío.")
            return

        if size_n_text:
            try:
                size_n = float(size_n_text)
                self.injection_data["parameters"]["sizeDistribution_n"] = size_n
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Size Distribution n.")
                return
        else:
            QMessageBox.warning(self, "Error", "Size Distribution n no puede estar vacío.")
            return

        # Cd
        cd_text = self.cd_value.text().strip()
        if cd_text:
            try:
                cd_value = float(cd_text)
                self.injection_data["parameters"]["CdValue"] = cd_value
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Cd.")
                return
        else:
            QMessageBox.warning(self, "Error", "CdValue no puede estar vacío.")
            return

        # Theta Inner
        theta_inner_text = self.theta_inner_value.text().strip()
        if theta_inner_text:
            try:
                theta_inner_value = float(theta_inner_text)
                self.injection_data["parameters"]["thetaInnerValue"] = theta_inner_value
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Theta Inner.")
                return
        else:
            QMessageBox.warning(self, "Error", "Theta Inner Value no puede estar vacío.")
            return

        # Theta Outer
        theta_outer_text = self.theta_outer_value.text().strip()
        if theta_outer_text:
            try:
                theta_outer_value = float(theta_outer_text)
                self.injection_data["parameters"]["thetaOuterValue"] = theta_outer_value
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Theta Outer.")
                return
        else:
            QMessageBox.warning(self, "Error", "Theta Outer Value no puede estar vacío.")
            return

        # Parcel Basis Type
        parcel_basis_selected = [item.text() for item in self.parcel_basis_list.selectedItems()]
        if parcel_basis_selected:
            self.injection_data["parameters"]["parcelBasisType"] = parcel_basis_selected
        else:
            QMessageBox.warning(self, "Error", "Debe seleccionar al menos un Parcel Basis Type.")
            return

        # Injection Method
        injection_method_selected = [item.text() for item in self.injection_method_list.selectedItems()]
        if injection_method_selected:
            self.injection_data["parameters"]["injectionMethod"] = injection_method_selected
        else:
            QMessageBox.warning(self, "Error", "Debe seleccionar al menos un Injection Method.")
            return

        # Flow Type
        flow_type = self.flow_type_combo.currentText()
        self.injection_data["parameters"]["flowType"] = flow_type

        # Velocity
        try:
            vel_x_text = self.velocity_u.text().strip()
            vel_y_text = self.velocity_v.text().strip()
            vel_z_text = self.velocity_z.text().strip()
            vel_x = float(vel_x_text) if vel_x_text else 0.0
            vel_y = float(vel_y_text) if vel_y_text else 0.0
            vel_z = float(vel_z_text) if vel_z_text else 0.0
            velocity = [vel_x, vel_y, vel_z]
            self.injection_data["parameters"]["velocity"] = velocity
        except ValueError:
            QMessageBox.warning(self, "Error", "Valores inválidos para la velocidad.")
            return

        # Parcels Per Second
        parcels_text = self.parcels_input.text().strip()
        if parcels_text:
            try:
                parcels = float(parcels_text)
                self.injection_data["parameters"]["parcelsPerSecond"] = parcels
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Parcels Per Second.")
                return
        else:
            QMessageBox.warning(self, "Error", "Parcels Per Second no puede estar vacío.")
            return

        # Position
        try:
            pos_x_text = self.position_x.text().strip()
            pos_y_text = self.position_y.text().strip()
            pos_z_text = self.position_z.text().strip()
            pos_x = float(pos_x_text) if pos_x_text else 0.0
            pos_y = float(pos_y_text) if pos_y_text else 0.0
            pos_z = float(pos_z_text) if pos_z_text else 0.0
            position = [pos_x, pos_y, pos_z]
            self.injection_data["parameters"]["position"] = position
        except ValueError:
            QMessageBox.warning(self, "Error", "Valores inválidos para la posición.")
            return

        self.accept()

    def get_injection_data(self):
        """
        Devuelve los datos de la inyección configurada en el diálogo.
        """
        return self.injection_data

    def load_initial_parameters(self):
        parameters = self.injection_data.get("parameters", {})
        # Nombre del Inyector
        self.name_input.setText(str(self.injection_data.get("name", "")))

        # Flow Rate Profile y Size Distribution
        self.flow_rate_profile_combo.setCurrentText(parameters.get("sizeDistribution", "RosinRammlerDistribution"))
        self.size_min_input.setText(str(parameters.get("sizeDistribution_minValue", "")))
        self.size_max_input.setText(str(parameters.get("sizeDistribution_maxValue", "")))
        self.size_lambda_input.setText(str(parameters.get("sizeDistribution_lambda", "")))
        self.size_n_input.setText(str(parameters.get("sizeDistribution_n", "")))

        # Cd
        self.cd_combo.setCurrentText(parameters.get("Cd", "constant"))
        self.cd_value.setText(str(parameters.get("CdValue", "")))

        # Theta Inner
        self.theta_inner_combo.setCurrentText(parameters.get("thetaInner", "constant"))
        self.theta_inner_value.setText(str(parameters.get("thetaInnerValue", "")))

        # Theta Outer
        self.theta_outer_combo.setCurrentText(parameters.get("thetaOuter", "constant"))
        self.theta_outer_value.setText(str(parameters.get("thetaOuterValue", "")))

        # Flow Type
        self.flow_type_combo.setCurrentText(parameters.get("flowType", "flowRateAndDischarge"))

        # Parcel Basis Type
        parcel_basis = parameters.get("parcelBasisType", [])
        if isinstance(parcel_basis, list):
            for item_text in parcel_basis:
                items = self.parcel_basis_list.findItems(item_text, Qt.MatchExactly)
                for item in items:
                    item.setSelected(True)

        # Injection Method
        injection_method = parameters.get("injectionMethod", [])
        if isinstance(injection_method, list):
            for item_text in injection_method:
                items = self.injection_method_list.findItems(item_text, Qt.MatchExactly)
                for item in items:
                    item.setSelected(True)

        # Velocidad
        velocity = parameters.get("velocity", [0.0, 0.0, 0.0])
        if isinstance(velocity, list) and len(velocity) == 3:
            self.velocity_u.setText(str(velocity[0]))
            self.velocity_v.setText(str(velocity[1]))
            self.velocity_z.setText(str(velocity[2]))

        # Parcels Per Second
        self.parcels_input.setText(str(parameters.get("parcelsPerSecond", 0.0)))

        # Position
        position = parameters.get("position", [0.0, 0.0, 0.0])
        if isinstance(position, list) and len(position) == 3:
            self.position_x.setText(str(position[0]))
            self.position_y.setText(str(position[1]))
            self.position_z.setText(str(position[2]))

        # Outer Diameter
        outer_diameter = parameters.get("outerDiameter", 0.0)
        self.outer_diameter_input.setText(str(outer_diameter))

        # Inner Diameter
        inner_diameter = parameters.get("innerDiameter", 0.0)
        self.inner_diameter_input.setText(str(inner_diameter))

        # Duration
        duration = parameters.get("duration", 0.0)
        self.duration_input.setText(str(duration))
