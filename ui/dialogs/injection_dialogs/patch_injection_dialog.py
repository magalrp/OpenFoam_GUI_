# ui/dialogs/injection_dialogs/patch_injection_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QLabel, QPushButton, QMessageBox, QListWidget, QWidget
)
from PyQt5.QtCore import Qt, QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator
import os
import json

from core.boundary_parser import parse_openfoam_boundary


class PatchInjectionDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de PatchInjection")

        self.injection_data = {
            "name": "",
            "type": "patchInjection",
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
        self.name_input = QLineEdit()
        self.name_input.setText(self.injection_data.get("name", ""))
        form.addRow("Nombre del Inyector:", self.name_input)

        # Patch Selection
        patch_label = QLabel("Patch:")
        self.patch_combo = QComboBox()
        # Cargar los patches disponibles usando parse_openfoam_boundary
        self.patch_combo.addItems(self.list_boundary_patches())
        current_patch = self.injection_data.get("parameters", {}).get("patch", "")
        if current_patch:
            index = self.patch_combo.findText(current_patch)
            if index != -1:
                self.patch_combo.setCurrentIndex(index)
        patch_layout = QHBoxLayout()
        patch_layout.addWidget(patch_label)
        patch_layout.addWidget(self.patch_combo)
        form.addRow(patch_layout)

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

        # Duration
        duration_label = QLabel("Duration [s]:")
        duration_layout = QHBoxLayout()
        self.duration_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("duration", 0.0)
        )
        duration_layout.addWidget(self.duration_input)
        duration_layout.addWidget(QLabel("s"))
        form.addRow(duration_label, duration_layout)

        # Parcels Per Second
        parcels_label = QLabel("Parcels Per Second [parcels/s]:")
        parcels_layout = QHBoxLayout()
        self.parcels_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("parcelsPerSecond", 0.0)
        )
        parcels_layout.addWidget(self.parcels_input)
        parcels_layout.addWidget(QLabel("parcels/s"))
        form.addRow(parcels_label, parcels_layout)

        # U0 (Velocity Vector)
        velocity_label = QLabel("U0 (m/s):")
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

        # Parcel Basis Type
        parcel_basis_label = QLabel("Parcel Basis Type:")
        self.parcel_basis_list = QListWidget()
        self.parcel_basis_list.setSelectionMode(QListWidget.MultiSelection)
        self.parcel_basis_list.addItems(["mass"])  # Inicialmente solo 'mass'
        selected_parcel_basis = self.injection_data.get("parameters", {}).get("parcelBasisType", [])
        for item_text in selected_parcel_basis:
            items = self.parcel_basis_list.findItems(item_text, Qt.MatchExactly)
            for item in items:
                item.setSelected(True)
        form.addRow(parcel_basis_label, self.parcel_basis_list)

        # Flow Rate Profile
        flow_rate_profile_label = QLabel("Flow Rate Profile:")
        self.flow_rate_profile_combo = QComboBox()
        self.flow_rate_profile_combo.addItems(["constant"])  # Inicialmente solo 'constant'
        self.flow_rate_profile_combo.setCurrentText(self.injection_data.get("parameters", {}).get("flowRateProfile", "constant"))
        self.flow_rate_profile_combo.currentTextChanged.connect(self.update_flow_rate_profile_field)

        flow_rate_layout = QHBoxLayout()
        flow_rate_layout.addWidget(self.flow_rate_profile_combo)

        self.flow_rate_value = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("flowRateValue", 0.0)
        )
        self.flow_rate_value.setEnabled(self.flow_rate_profile_combo.currentText() == "constant")
        flow_rate_layout.addWidget(self.flow_rate_value)
        flow_rate_layout.addWidget(QLabel("kg/s"))  # Unidades para flow rate

        form.addRow(flow_rate_profile_label, flow_rate_layout)

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
        Crea un QLineEdit con un validador que permite números en notación científica
        y hasta 12 decimales. Muestra hasta dos decimales a menos que el número sea <0.01.
        """
        line_edit = QLineEdit()
        regex = QRegularExpression(r'^[+-]?(\d+(\.\d{0,12})?|\.\d{1,12})([eE][+-]?\d+)?$')
        validator = QRegularExpressionValidator(regex)
        line_edit.setValidator(validator)
        line_edit.setText(self.format_number(default))
        return line_edit

    def format_number(self, number):
        """
        Formatea el número para mostrar hasta dos decimales o en notación científica
        si es menor que 0.01.
        """
        if abs(number) < 0.01 and number != 0.0:
            return "{:.2e}".format(number)
        else:
            return "{:.2f}".format(number)

    def add_size_distribution_field(self):
        size_distribution_label = QLabel("Size Distribution:")
        self.size_distribution_combo = QComboBox()
        self.size_distribution_combo.addItems(["RosinRammlerDistribution"])  # Solo una opción actualmente
        self.size_distribution_combo.setCurrentText(self.injection_data.get("parameters", {}).get("sizeDistribution", "RosinRammlerDistribution"))
        self.size_distribution_combo.currentTextChanged.connect(self.update_size_distribution_field)

        size_distribution_layout = QHBoxLayout()
        size_distribution_layout.addWidget(self.size_distribution_combo)

        self.size_distribution_params_widget = QWidget()
        size_dist_form = QFormLayout()

        self.size_min_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("sizeDistribution_minValue", 0.0)
        )
        size_dist_form.addRow("Min Value:", self.size_min_input)

        self.size_max_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("sizeDistribution_maxValue", 0.0)
        )
        size_dist_form.addRow("Max Value:", self.size_max_input)

        self.size_lambda_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("sizeDistribution_lambda", 0.0)
        )
        size_dist_form.addRow("Lambda:", self.size_lambda_input)

        self.size_n_input = self.create_scientific_line_edit(
            default=self.injection_data.get("parameters", {}).get("sizeDistribution_n", 0.0)
        )
        size_dist_form.addRow("n:", self.size_n_input)

        self.size_distribution_params_widget.setLayout(size_dist_form)
        self.size_distribution_params_widget.setVisible(True)  # Inicialmente visible

        # Agregar a la forma principal
        self.parameters_layout.addRow(size_distribution_label, self.size_distribution_combo)
        self.parameters_layout.addRow("Size Distribution Parameters:", self.size_distribution_params_widget)

    def update_size_distribution_field(self, text):
        """
        Muestra u oculta los campos de parámetros según el tipo de distribución seleccionado.
        Actualmente, solo "RosinRammlerDistribution" está disponible.
        """
        if text == "RosinRammlerDistribution":
            self.size_distribution_params_widget.setVisible(True)
        else:
            self.size_distribution_params_widget.setVisible(False)

    def update_flow_rate_profile_field(self, text):
        """
        Habilita o deshabilita el campo de Flow Rate Value según el tipo seleccionado.
        Actualmente, solo "constant" está disponible.
        """
        if text == "constant":
            self.flow_rate_value.setEnabled(True)
        else:
            self.flow_rate_value.setEnabled(False)

    def list_boundary_patches(self):
        """
        Lista los patches de boundary en el directorio de trabajo actual utilizando parse_openfoam_boundary.
        Lee la ruta desde config.json.
        """
        # Leer la configuración desde config.json
        config = self.read_config()
        if config is None:
            return []  # Retornar lista vacía si hay error

        working_directory = config.get("working_directory", "")
        if not working_directory:
            QMessageBox.critical(self, "Error", "La ruta del directorio de trabajo no está definida en config.json.")
            return []

        # Construir la ruta al archivo boundary
        case_dir = os.path.join(working_directory, "constant", "polyMesh")
        boundary_file_path = os.path.join(case_dir, "boundary")

        patches = []
        try:
            boundaries_info = parse_openfoam_boundary(boundary_file_path)
            for boundary in boundaries_info:
                if boundary.get("type", "").lower() == "patch":
                    patch_name = boundary.get("name", "")
                    if patch_name:  # Asegurarse de que el nombre no esté vacío
                        patches.append(patch_name)
            return patches
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo parsear el archivo boundary:\n{str(e)}")
            return []

    def read_config(self):
        """
        Lee el archivo config.json y devuelve la configuración como un diccionario.
        """
        config_file_path = os.path.join(os.getcwd(), "config.json")
        if not os.path.exists(config_file_path):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo de configuración 'config.json' en {os.getcwd()}.")
            return None

        try:
            with open(config_file_path, 'r') as config_file:
                config = json.load(config_file)
            return config
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "El archivo 'config.json' está mal formateado.")
            return None
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo 'config.json':\n{str(e)}")
            return None

    def accept_changes(self):
        # Nombre del Inyector
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "El nombre del inyector no puede estar vacío.")
            return
        self.injection_data["name"] = name

        # Patch Selection
        patch = self.patch_combo.currentText()
        if not patch:
            QMessageBox.warning(self, "Error", "Debe seleccionar un patch.")
            return
        self.injection_data["parameters"]["patch"] = patch

        # SOI
        soi_text = self.soi_input.text().strip()
        if soi_text:
            try:
                soi = float(soi_text.replace(',', '.'))
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
                mass_total = float(mass_total_text.replace(',', '.'))
                self.injection_data["parameters"]["massTotal"] = mass_total
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Mass Total.")
                return
        else:
            QMessageBox.warning(self, "Error", "Mass Total no puede estar vacío.")
            return

        # Duration
        duration_text = self.duration_input.text().strip()
        if duration_text:
            try:
                duration = float(duration_text.replace(',', '.'))
                self.injection_data["parameters"]["duration"] = duration
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Duration.")
                return
        else:
            QMessageBox.warning(self, "Error", "Duration no puede estar vacío.")
            return

        # Parcels Per Second
        parcels_text = self.parcels_input.text().strip()
        if parcels_text:
            try:
                parcels = float(parcels_text.replace(',', '.'))
                self.injection_data["parameters"]["parcelsPerSecond"] = parcels
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Parcels Per Second.")
                return
        else:
            QMessageBox.warning(self, "Error", "Parcels Per Second no puede estar vacío.")
            return

        # U0 (Velocity Vector)
        try:
            vel_x_text = self.velocity_u.text().strip()
            vel_y_text = self.velocity_v.text().strip()
            vel_z_text = self.velocity_z.text().strip()
            vel_x = float(vel_x_text.replace(',', '.')) if vel_x_text else 0.0
            vel_y = float(vel_y_text.replace(',', '.')) if vel_y_text else 0.0
            vel_z = float(vel_z_text.replace(',', '.')) if vel_z_text else 0.0
            velocity = [vel_x, vel_y, vel_z]
            self.injection_data["parameters"]["velocity"] = velocity
        except ValueError:
            QMessageBox.warning(self, "Error", "Valores inválidos para la velocidad.")
            return

        # Parcel Basis Type
        parcel_basis_selected = [item.text() for item in self.parcel_basis_list.selectedItems()]
        if parcel_basis_selected:
            self.injection_data["parameters"]["parcelBasisType"] = parcel_basis_selected
        else:
            QMessageBox.warning(self, "Error", "Debe seleccionar al menos un Parcel Basis Type.")
            return

        # Flow Rate Profile
        flow_rate_profile = self.flow_rate_profile_combo.currentText()
        self.injection_data["parameters"]["flowRateProfile"] = flow_rate_profile

        if flow_rate_profile == "constant":
            flow_rate_value_text = self.flow_rate_value.text().strip()
            if flow_rate_value_text:
                try:
                    flow_rate_value = float(flow_rate_value_text.replace(',', '.'))
                    self.injection_data["parameters"]["flowRateValue"] = flow_rate_value
                except ValueError:
                    QMessageBox.warning(self, "Error", "Valor inválido para Flow Rate Value.")
                    return
            else:
                QMessageBox.warning(self, "Error", "Flow Rate Value no puede estar vacío.")
                return
        else:
            # Si se implementan otros tipos en el futuro
            self.injection_data["parameters"]["flowRateValue"] = None

        # Size Distribution
        size_distribution_type = self.size_distribution_combo.currentText()
        self.injection_data["parameters"]["sizeDistribution"] = size_distribution_type

        size_min_text = self.size_min_input.text().strip()
        size_max_text = self.size_max_input.text().strip()
        size_lambda_text = self.size_lambda_input.text().strip()
        size_n_text = self.size_n_input.text().strip()

        if size_min_text:
            try:
                size_min = float(size_min_text.replace(',', '.'))
                self.injection_data["parameters"]["sizeDistribution_minValue"] = size_min
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Size Distribution Min Value.")
                return
        else:
            QMessageBox.warning(self, "Error", "Size Distribution Min Value no puede estar vacío.")
            return

        if size_max_text:
            try:
                size_max = float(size_max_text.replace(',', '.'))
                self.injection_data["parameters"]["sizeDistribution_maxValue"] = size_max
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Size Distribution Max Value.")
                return
        else:
            QMessageBox.warning(self, "Error", "Size Distribution Max Value no puede estar vacío.")
            return

        if size_lambda_text:
            try:
                size_lambda = float(size_lambda_text.replace(',', '.'))
                self.injection_data["parameters"]["sizeDistribution_lambda"] = size_lambda
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Size Distribution Lambda.")
                return
        else:
            QMessageBox.warning(self, "Error", "Size Distribution Lambda no puede estar vacío.")
            return

        if size_n_text:
            try:
                size_n = float(size_n_text.replace(',', '.'))
                self.injection_data["parameters"]["sizeDistribution_n"] = size_n
            except ValueError:
                QMessageBox.warning(self, "Error", "Valor inválido para Size Distribution n.")
                return
        else:
            QMessageBox.warning(self, "Error", "Size Distribution n no puede estar vacío.")
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

        # Patch Selection
        patch = parameters.get("patch", "")
        if patch:
            index = self.patch_combo.findText(patch)
            if index != -1:
                self.patch_combo.setCurrentIndex(index)

        # SOI
        soi = parameters.get("SOI", 0.0)
        self.soi_input.setText(str(soi))

        # Mass Total
        mass_total = parameters.get("massTotal", 0.0)
        self.mass_total_input.setText(str(mass_total))

        # Duration
        duration = parameters.get("duration", 0.0)
        self.duration_input.setText(str(duration))

        # Parcels Per Second
        parcels = parameters.get("parcelsPerSecond", 0.0)
        self.parcels_input.setText(str(parcels))

        # U0 (Velocity Vector)
        velocity = parameters.get("velocity", [0.0, 0.0, 0.0])
        if isinstance(velocity, list) and len(velocity) == 3:
            self.velocity_u.setText(str(velocity[0]))
            self.velocity_v.setText(str(velocity[1]))
            self.velocity_z.setText(str(velocity[2]))
        else:
            self.velocity_u.setText("0.0")
            self.velocity_v.setText("0.0")
            self.velocity_z.setText("0.0")

        # Parcel Basis Type
        parcel_basis = parameters.get("parcelBasisType", [])
        if isinstance(parcel_basis, list):
            for item_text in parcel_basis:
                items = self.parcel_basis_list.findItems(item_text, Qt.MatchExactly)
                for item in items:
                    item.setSelected(True)

        # Flow Rate Profile
        flow_rate_profile = parameters.get("flowRateProfile", "constant")
        self.flow_rate_profile_combo.setCurrentText(flow_rate_profile)

        flow_rate_value = parameters.get("flowRateValue", 0.0)
        self.flow_rate_value.setText(str(flow_rate_value))
        self.flow_rate_value.setEnabled(flow_rate_profile == "constant")

        # Size Distribution
        size_distribution_type = parameters.get("sizeDistribution", "RosinRammlerDistribution")
        self.size_distribution_combo.setCurrentText(size_distribution_type)

        size_min = parameters.get("sizeDistribution_minValue", 0.0)
        self.size_min_input.setText(str(size_min))

        size_max = parameters.get("sizeDistribution_maxValue", 0.0)
        self.size_max_input.setText(str(size_max))

        size_lambda = parameters.get("sizeDistribution_lambda", 0.0)
        self.size_lambda_input.setText(str(size_lambda))

        size_n = parameters.get("sizeDistribution_n", 0.0)
        self.size_n_input.setText(str(size_n))
