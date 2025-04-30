# ui/sections/fase_discreta.py

import os
import json
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QComboBox, QCheckBox,
    QListWidget, QListWidgetItem, QDialog, QGroupBox, QGridLayout, QScrollArea,
    QHeaderView, QSpacerItem, QSizePolicy
)
from ui.widgets.numeric_line_edit import NumericLineEdit
from PyQt5.QtCore import Qt, pyqtSignal

from ui.dialogs.injection_dialogs.patch_injection_dialog import PatchInjectionDialog
from ui.dialogs.injection_dialogs.cone_nozzle_injection_dialog import ConeNozzleInjectionDialog
from ui.dialogs.injection_dialogs.type_selection_dialog import TypeSelectionDialog
from ui.dialogs.injection_dialogs.dialog_opt_disperse_fase import OptDisperseFaseDialog

# Configuración de logging para mensajes en consola
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class FaseDiscreta(QWidget):
    def __init__(self, case_config):
        super().__init__()
        self.case_config = case_config

        # Establecer el objectName para permitir la localización desde otros widgets
        self.setObjectName("FaseDiscreta")

        # Inicializar estructuras en case_config si no existen
        self.initialize_case_config()

        # Leer constant.json para actualizar las especies activas
        self.load_constant_species()

        # Establecer el directorio TEMP relativo a main.py (se asume que main.py está en la raíz del proyecto)
        self.CONFIG_DIR = self.read_config()

        # Cargar la configuración previa de fase discreta (discrete_phase_models, injections,
        # flag discrete_phase_active y particleTrackProperties)
        self.load_disperse_phase_config()

        self.init_ui()

    def initialize_case_config(self):
        # Inicializar estructuras necesarias si no existen
        self.case_config.setdefault("discrete_phase_models", {}).setdefault("compositionModel", {})
        composition_model = self.case_config["discrete_phase_models"]["compositionModel"]
        composition_model.setdefault("model", "none")
        composition_model.setdefault("speciesType", {})
        composition_model.setdefault("fractions", {})

        # Verificar que 'speciesType' es un dict; si es lista se convierte
        species_type = composition_model.get("speciesType", {})
        if isinstance(species_type, list):
            composition_model["speciesType"] = {species: "Gas" for species in species_type}
        elif not isinstance(species_type, dict):
            composition_model["speciesType"] = {}

        # Inicializar inyecciones si no existen
        self.case_config.setdefault("injections", [])
        # Inicializar flag de fase discreta si no existe
        if "discrete_phase_active" not in self.case_config:
            self.case_config["discrete_phase_active"] = False
        # Inicializar la configuración de tracking de partículas
        self.case_config.setdefault("particleTrackProperties", {
            "cloudName": "genericCloud",
            "sampleFrequency": 1,
            "maxPositions": 1e6,
            "setFormat": "vtk",
            "fields": "",
            "maxTracks": -1
        })

    def load_constant_species(self):
        """
        Lee constant.json y, si las especies están activas, actualiza la lista de especies
        activas en case_config["chosen_species"].
        """
        constant_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "temp", "constant.json")
        if os.path.exists(constant_path):
            try:
                with open(constant_path, "r") as f:
                    constant_data = json.load(f)
                if constant_data.get("especiesActive", False):
                    self.case_config["chosen_species"] = constant_data.get("especies_options", {}).get("activeSpecies", [])
                else:
                    self.case_config["chosen_species"] = []
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error al leer constant.json:\n{e}")
                self.case_config["chosen_species"] = []
        else:
            self.case_config["chosen_species"] = []

    def read_config(self):
        """
        Lee config.json y devuelve la ruta del directorio temp, asumiendo que main.py se encuentra en la raíz del proyecto.
        """
        main_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        config_file_path = os.path.join(main_dir, "config.json")
        if not os.path.exists(config_file_path):
            QMessageBox.critical(self, "Error", f"No se encontró 'config.json' en {main_dir}.")
            return None
        try:
            with open(config_file_path, "r") as config_file:
                config = json.load(config_file)
            temp_dir = os.path.join(main_dir, "temp")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            return temp_dir
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer 'config.json':\n{str(e)}")
            return None

    def load_disperse_phase_config(self):
        """
        Lee el archivo Disperse_fase.json (si existe) y actualiza la configuración de fase discreta,
        incluyendo discrete_phase_models, injections, discrete_phase_active y particleTrackProperties.
        """
        filename = os.path.join(self.CONFIG_DIR, "Disperse_fase.json")
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    data = json.load(f)
                if "discrete_phase_models" in data:
                    self.case_config["discrete_phase_models"] = data["discrete_phase_models"]
                if "injections" in data:
                    self.case_config["injections"] = data["injections"]
                if "discrete_phase_active" in data:
                    self.case_config["discrete_phase_active"] = data["discrete_phase_active"]
                if "particleTrackProperties" in data:
                    self.case_config["particleTrackProperties"] = data["particleTrackProperties"]
                logging.info("Disperse_fase.json cargado correctamente.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error al leer Disperse_fase.json:\n{e}")

    def save_disperse_phase_config(self):
        """
        Guarda la configuración de fase discreta en Disperse_fase.json, incluyendo discrete_phase_models,
        injections, particleTrackProperties y el flag discrete_phase_active.
        Se sobrescribe completamente el archivo.
        """
        filename = os.path.join(self.CONFIG_DIR, "Disperse_fase.json")
        try:
            data_to_save = {
                "discrete_phase_active": self.case_config.get("discrete_phase_active", False),
                "discrete_phase_models": self.case_config.get("discrete_phase_models", {}),
                "injections": self.case_config.get("injections", []),
                "particleTrackProperties": self.case_config.get("particleTrackProperties", {})
            }
            with open(filename, "w") as f:
                json.dump(data_to_save, f, indent=4)
            logging.info(f"Disperse_fase.json guardado correctamente en: {filename}")
            print(f"Disperse_fase.json guardado correctamente en: {filename}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al guardar Disperse_fase.json:\n{e}")

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Título y descripción
        title = QLabel("Fase Discreta")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        description = QLabel(
            "En esta sección se definen las partículas lagrangianas (fase discreta) del modelo. Aquí se pueden configurar tanto las propiedades constantes (densidad, temperatura inicial, capacidad calorífica) como los inyectores y modelos asociados a la fase discreta.\n\n"
            "Además, se gestionan opciones avanzadas para el tracking de partículas mediante el archivo particleTrackProperties.\n\n"
            "El estado de la fase discreta se guarda en Disperse_fase.json, incluyendo el flag 'discrete_phase_active'."
        )
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)

        # Opción para activar/desactivar la fase discreta
        self.toggle_discrete_phase = QCheckBox("Activar Fase Discreta")
        self.toggle_discrete_phase.setChecked(self.case_config.get("discrete_phase_active", False))
        self.toggle_discrete_phase.stateChanged.connect(
            lambda state: self.case_config.update({"discrete_phase_active": state == Qt.Checked}) or self.update_discrete_phase_visibility(state == Qt.Checked)
        )
        layout.addWidget(self.toggle_discrete_phase)

        # Botón para configurar tracking de partículas (particleTrackProperties)
        self.btn_particle_track = QPushButton("Configurar tracking de partículas")
        self.btn_particle_track.clicked.connect(self.open_particle_tracking_options)
        layout.addWidget(self.btn_particle_track)

        # Scroll Area para el contenido de Fase Discreta
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        # Widget principal de contenido
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)

        # Propiedades Constantes
        propiedades_label = QLabel("Propiedades Constantes:")
        self.content_layout.addWidget(propiedades_label)

        rho_layout = QHBoxLayout()
        rho_label = QLabel("Densidad (rho0) [kg/m³]:")
        self.rho0_input = NumericLineEdit()
        self.rho0_input.setText(str(self.case_config.get("discrete_phase_models", {}).get("rho0", "1000")))
        self.rho0_input.editingFinished.connect(self.update_rho0)
        rho_layout.addWidget(rho_label)
        rho_layout.addWidget(self.rho0_input)
        self.content_layout.addLayout(rho_layout)

        T_layout = QHBoxLayout()
        T_label = QLabel("Temperatura Inicial (T0) [K]:")
        self.T0_input = NumericLineEdit()
        self.T0_input.setText(str(self.case_config.get("discrete_phase_models", {}).get("T0", "300")))
        self.T0_input.editingFinished.connect(self.update_T0)
        T_layout.addWidget(T_label)
        T_layout.addWidget(self.T0_input)
        self.content_layout.addLayout(T_layout)

        Cp_layout = QHBoxLayout()
        Cp_label = QLabel("Capacidad Calorífica (Cp0) [J/(kg·K)]:")
        self.Cp0_input = NumericLineEdit()
        self.Cp0_input.setText(str(self.case_config.get("discrete_phase_models", {}).get("Cp0", "4186")))
        self.Cp0_input.editingFinished.connect(self.update_Cp0)
        Cp_layout.addWidget(Cp_label)
        Cp_layout.addWidget(self.Cp0_input)
        self.content_layout.addLayout(Cp_layout)

        # Sección de Inyectores
        injectors_label = QLabel("Inyectores:")
        self.content_layout.addWidget(injectors_label)

        self.injectors_table = QTableWidget()
        self.injectors_table.setColumnCount(4)
        self.injectors_table.setHorizontalHeaderLabels(["Nombre", "Tipo", "SOI [s]", "Posición (x, y, z)"])
        self.injectors_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.injectors_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.injectors_table.setSelectionMode(QTableWidget.SingleSelection)
        self.injectors_table.doubleClicked.connect(self.edit_injector)
        self.content_layout.addWidget(self.injectors_table)

        injectors_btn_layout = QHBoxLayout()
        self.add_injector_button = QPushButton("Añadir Inyector")
        self.remove_injector_button = QPushButton("Eliminar Inyector")
        self.add_injector_button.clicked.connect(self.add_injector)
        self.remove_injector_button.clicked.connect(self.remove_injector)
        injectors_btn_layout.addWidget(self.add_injector_button)
        injectors_btn_layout.addWidget(self.remove_injector_button)
        self.content_layout.addLayout(injectors_btn_layout)

        # Sección de Modelos de Fase Discreta
        modelos_label = QLabel("Modelos de Fase Discreta:")
        self.content_layout.addWidget(modelos_label)

        dispersion_layout = QHBoxLayout()
        dispersion_label = QLabel("Dispersion Model:")
        self.dispersion_combo = QComboBox()
        self.dispersion_combo.addItems(["none", "constantDispersion", "linearDispersion"])
        self.dispersion_combo.setCurrentText(self.case_config["discrete_phase_models"].get("dispersionModel", "none"))
        self.dispersion_combo.currentTextChanged.connect(self.update_dispersion_model)
        dispersion_layout.addWidget(dispersion_label)
        dispersion_layout.addWidget(self.dispersion_combo)
        self.content_layout.addLayout(dispersion_layout)

        patch_interaction_layout = QHBoxLayout()
        patch_interaction_label = QLabel("Patch Interaction Model:")
        self.patch_interaction_combo = QComboBox()
        self.patch_interaction_combo.addItems(["none", "standardWallInteraction", "rebound"])
        current_patch_model = self.case_config["discrete_phase_models"].get("patchInteractionModel", {}).get("model", "none")
        self.patch_interaction_combo.setCurrentText(current_patch_model)
        self.patch_interaction_combo.currentTextChanged.connect(self.update_patch_interaction_model)
        patch_interaction_layout.addWidget(patch_interaction_label)
        patch_interaction_layout.addWidget(self.patch_interaction_combo)
        self.content_layout.addLayout(patch_interaction_layout)

        heat_transfer_layout = QHBoxLayout()
        heat_transfer_label = QLabel("Heat Transfer Model:")
        self.heat_transfer_combo = QComboBox()
        self.heat_transfer_combo.addItems(["none", "RanzMarshallCoeffs"])
        current_heat_transfer = self.case_config["discrete_phase_models"].get("heatTransferModel", {}).get("model", "none")
        self.heat_transfer_combo.setCurrentText(current_heat_transfer)
        self.heat_transfer_combo.currentTextChanged.connect(self.update_heat_transfer_model)
        heat_transfer_layout.addWidget(heat_transfer_label)
        heat_transfer_layout.addWidget(self.heat_transfer_combo)
        self.content_layout.addLayout(heat_transfer_layout)

        self.bird_correction_checkbox = QCheckBox("Activar Bird Correction")
        bird_correction = self.case_config["discrete_phase_models"].get("heatTransferModel", {}).get("BirdCorrection", False)
        self.bird_correction_checkbox.setChecked(bird_correction)
        self.bird_correction_checkbox.stateChanged.connect(self.toggle_bird_correction)
        self.bird_correction_checkbox.setVisible(self.heat_transfer_combo.currentText() != "none")
        self.content_layout.addWidget(self.bird_correction_checkbox)

        composition_layout = QVBoxLayout()
        composition_label = QLabel("Composition Model:")
        self.composition_combo = QComboBox()
        self.composition_combo.addItems(["none", "singleMixtureFractionCoeffs"])
        current_composition = self.case_config["discrete_phase_models"]["compositionModel"].get("model", "none")
        self.composition_combo.setCurrentText(current_composition)
        self.composition_combo.currentTextChanged.connect(self.update_composition_model)
        composition_layout.addWidget(composition_label)
        composition_layout.addWidget(self.composition_combo)

        self.composition_options_widget = QWidget()
        composition_options_layout = QVBoxLayout(self.composition_options_widget)
        active_species = self.case_config.get("chosen_species", [])
        if self.case_config.get("especiesActive", False) and active_species:
            self.composition_model_widget = CompositionModelWidget(
                available_species=active_species,
                assigned_species_types=self.get_assigned_species_types(),
                case_config=self.case_config
            )
            self.composition_model_widget.classification_changed.connect(self.update_composition_model_from_ui)
            composition_options_layout.addWidget(self.composition_model_widget)
        else:
            no_species_label = QLabel("No hay especies activas para la composición.")
            composition_options_layout.addWidget(no_species_label)
        self.composition_options_widget.setLayout(composition_options_layout)
        self.composition_options_widget.setVisible(current_composition == "singleMixtureFractionCoeffs")
        composition_layout.addWidget(self.composition_options_widget)
        self.content_layout.addLayout(composition_layout)

        phase_change_layout = QVBoxLayout()
        phase_change_label = QLabel("Phase Change Model:")
        self.phase_change_combo = QComboBox()
        self.phase_change_combo.addItems(["none", "liquidEvaporationCoeffs"])
        current_phase_change = self.case_config["discrete_phase_models"].get("phaseChangeModel", {}).get("model", "none")
        self.phase_change_combo.setCurrentText(current_phase_change)
        self.phase_change_combo.currentTextChanged.connect(self.update_phase_change_model)
        phase_change_layout.addWidget(phase_change_label)
        phase_change_layout.addWidget(self.phase_change_combo)

        self.phase_change_options_widget = QWidget()
        phase_change_options_layout = QVBoxLayout(self.phase_change_options_widget)
        enthalpy_layout = QHBoxLayout()
        enthalpy_label = QLabel("Tipo de Entalpía:")
        self.enthalpy_combo = QComboBox()
        self.enthalpy_combo.addItems(["enthalpyDifference"])
        current_enthalpy = self.case_config["discrete_phase_models"].get("phaseChangeModel", {}).get("enthalpyTransfer", "enthalpyDifference")
        self.enthalpy_combo.setCurrentText(current_enthalpy)
        enthalpy_layout.addWidget(enthalpy_label)
        enthalpy_layout.addWidget(self.enthalpy_combo)
        phase_change_options_layout.addLayout(enthalpy_layout)

        liquids_layout = QHBoxLayout()
        liquids_label = QLabel("Líquidos Activos:")
        self.liquids_selection = QListWidget()
        self.liquids_selection.setSelectionMode(QListWidget.MultiSelection)
        active_liquids = self.case_config["discrete_phase_models"].get("phaseChangeModel", {}).get("activeLiquids", [])
        for species in self.case_config.get("chosen_species", []):
            item = QListWidgetItem(species)
            if species in active_liquids:
                item.setSelected(True)
            self.liquids_selection.addItem(item)
        liquids_layout.addWidget(liquids_label)
        liquids_layout.addWidget(self.liquids_selection)
        phase_change_options_layout.addLayout(liquids_layout)

        self.phase_change_options_widget.setVisible(current_phase_change == "liquidEvaporationCoeffs")
        phase_change_layout.addWidget(self.phase_change_options_widget)
        self.content_layout.addLayout(phase_change_layout)

        devolatilisation_layout = QHBoxLayout()
        devolatilisation_label = QLabel("Devolatilisation Model:")
        self.devolatilisation_combo = QComboBox()
        self.devolatilisation_combo.addItems(["none"])
        current_devolatilisation = self.case_config["discrete_phase_models"].get("devolatilisationModel", "none")
        self.devolatilisation_combo.setCurrentText(current_devolatilisation)
        devolatilisation_layout.addWidget(devolatilisation_label)
        devolatilisation_layout.addWidget(self.devolatilisation_combo)
        self.content_layout.addLayout(devolatilisation_layout)

        surface_reaction_layout = QHBoxLayout()
        surface_reaction_label = QLabel("Surface Reaction Model:")
        self.surface_reaction_combo = QComboBox()
        self.surface_reaction_combo.addItems(["none"])
        current_surface_reaction = self.case_config["discrete_phase_models"].get("surfaceReactionModel", "none")
        self.surface_reaction_combo.setCurrentText(current_surface_reaction)
        surface_reaction_layout.addWidget(surface_reaction_label)
        surface_reaction_layout.addWidget(self.surface_reaction_combo)
        self.content_layout.addLayout(surface_reaction_layout)

        stochastic_collision_layout = QHBoxLayout()
        stochastic_collision_label = QLabel("Stochastic Collision Model:")
        self.stochastic_collision_combo = QComboBox()
        self.stochastic_collision_combo.addItems(["none"])
        current_stochastic_collision = self.case_config["discrete_phase_models"].get("stochasticCollisionModel", "none")
        self.stochastic_collision_combo.setCurrentText(current_stochastic_collision)
        stochastic_collision_layout.addWidget(stochastic_collision_label)
        stochastic_collision_layout.addWidget(self.stochastic_collision_combo)
        self.content_layout.addLayout(stochastic_collision_layout)

        surface_film_layout = QHBoxLayout()
        surface_film_label = QLabel("Surface Film Model:")
        self.surface_film_combo = QComboBox()
        self.surface_film_combo.addItems(["none"])
        current_surface_film = self.case_config["discrete_phase_models"].get("surfaceFilmModel", "none")
        self.surface_film_combo.setCurrentText(current_surface_film)
        surface_film_layout.addWidget(surface_film_label)
        surface_film_layout.addWidget(self.surface_film_combo)
        self.content_layout.addLayout(surface_film_layout)

        radiation_layout = QHBoxLayout()
        radiation_label = QLabel("Radiation:")
        self.radiation_combo = QComboBox()
        self.radiation_combo.addItems(["none"])
        current_radiation = self.case_config["discrete_phase_models"].get("radiation", "none")
        self.radiation_combo.setCurrentText(current_radiation)
        radiation_layout.addWidget(radiation_label)
        radiation_layout.addWidget(self.radiation_combo)
        self.content_layout.addLayout(radiation_layout)

        self.content_layout.addStretch()
        scroll_layout.addWidget(self.content_widget)

        self.update_discrete_phase_visibility(self.case_config.get("discrete_phase_active", False))
        self.update_injectors_table()

        layout.addLayout(scroll_layout)
        self.setLayout(layout)

    def toggle_discrete_phase_changed(self, state):
        is_active = (state == Qt.Checked)
        self.case_config["discrete_phase_active"] = is_active
        self.update_discrete_phase_visibility(is_active)

    def update_discrete_phase_visibility(self, is_active):
        if is_active:
            self.content_widget.show()
            if hasattr(self, 'off_label'):
                self.off_label.hide()
        else:
            self.content_widget.hide()
            if not hasattr(self, 'off_label'):
                self.off_label = QLabel("Fase Discreta off")
                self.off_label.setAlignment(Qt.AlignCenter)
                self.off_label.setStyleSheet("font-style: italic; color: gray;")
                self.layout().addWidget(self.off_label)
            self.off_label.show()

    def update_rho0(self):
        try:
            rho0 = float(self.rho0_input.text())
            self.case_config["discrete_phase_models"]["rho0"] = rho0
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingrese un valor válido para Densidad (rho0).")
            self.rho0_input.setText(str(self.case_config.get("discrete_phase_models", {}).get("rho0", "1000")))

    def update_T0(self):
        try:
            T0 = float(self.T0_input.text())
            self.case_config["discrete_phase_models"]["T0"] = T0
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingrese un valor válido para Temperatura Inicial (T0).")
            self.T0_input.setText(str(self.case_config.get("discrete_phase_models", {}).get("T0", "300")))

    def update_Cp0(self):
        try:
            Cp0 = float(self.Cp0_input.text())
            self.case_config["discrete_phase_models"]["Cp0"] = Cp0
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingrese un valor válido para Capacidad Calorífica (Cp0).")
            self.Cp0_input.setText(str(self.case_config.get("discrete_phase_models", {}).get("Cp0", "4186")))

    def update_dispersion_model(self, text):
        self.case_config["discrete_phase_models"]["dispersionModel"] = text

    def update_patch_interaction_model(self, text):
        self.case_config["discrete_phase_models"]["patchInteractionModel"] = self.case_config["discrete_phase_models"].get("patchInteractionModel", {})
        self.case_config["discrete_phase_models"]["patchInteractionModel"]["model"] = text
        if text == "standardWallInteraction":
            self.case_config["discrete_phase_models"]["patchInteractionModel"]["type"] = "standardWallInteraction"
        elif text == "rebound":
            self.case_config["discrete_phase_models"]["patchInteractionModel"]["type"] = "rebound"
        else:
            self.case_config["discrete_phase_models"]["patchInteractionModel"].pop("type", None)

    def update_heat_transfer_model(self, text):
        self.case_config["discrete_phase_models"]["heatTransferModel"] = self.case_config["discrete_phase_models"].get("heatTransferModel", {})
        self.case_config["discrete_phase_models"]["heatTransferModel"]["model"] = text
        if text != "none":
            self.bird_correction_checkbox.setVisible(True)
        else:
            self.bird_correction_checkbox.setVisible(False)
            self.case_config["discrete_phase_models"]["heatTransferModel"]["BirdCorrection"] = False
            self.bird_correction_checkbox.setChecked(False)

    def toggle_bird_correction(self, state):
        active = (state == Qt.Checked)
        self.case_config["discrete_phase_models"]["heatTransferModel"]["BirdCorrection"] = active

    def update_composition_model(self, text):
        self.case_config["discrete_phase_models"]["compositionModel"]["model"] = text
        if text == "singleMixtureFractionCoeffs":
            self.composition_options_widget.setVisible(True)
        else:
            self.composition_options_widget.setVisible(False)
            self.case_config["discrete_phase_models"]["compositionModel"]["speciesType"] = {}
            self.case_config["discrete_phase_models"]["compositionModel"]["fractions"] = {}

    def update_composition_model_from_ui(self):
        classified = self.composition_model_widget.get_classified_species()
        species_type = {}
        for category, species_list in classified.items():
            for species in species_list:
                species_type[species] = category
        self.case_config["discrete_phase_models"]["compositionModel"]["speciesType"] = species_type
        if not species_type:
            QMessageBox.warning(self, "Error", "Debe clasificar al menos una especie como Gas, Líquido o Sólido.")
            return
        QMessageBox.information(self, "Éxito", "Clasificación de especies actualizada correctamente.")

    def update_phase_change_model(self, text):
        self.case_config["discrete_phase_models"]["phaseChangeModel"] = self.case_config["discrete_phase_models"].get("phaseChangeModel", {})
        self.case_config["discrete_phase_models"]["phaseChangeModel"]["model"] = text
        if text == "liquidEvaporationCoeffs":
            self.phase_change_options_widget.setVisible(True)
        else:
            self.phase_change_options_widget.setVisible(False)
            self.case_config["discrete_phase_models"]["phaseChangeModel"]["enthalpyTransfer"] = "enthalpyDifference"
            self.case_config["discrete_phase_models"]["phaseChangeModel"]["activeLiquids"] = []

    def update_injectors_table(self):
        injectors = self.case_config.get("injections", [])
        self.injectors_table.setRowCount(len(injectors))
        for row, injector in enumerate(injectors):
            name_item = QTableWidgetItem(injector.get("name", ""))
            type_item = QTableWidgetItem(injector.get("type", ""))
            parameters = injector.get("parameters", {})
            SOI = parameters.get("SOI", "")
            position = parameters.get("position", [])
            SOI_item = QTableWidgetItem(str(SOI))
            if isinstance(position, list) and len(position) == 3:
                position_str = f"({position[0]:.2f}, {position[1]:.2f}, {position[2]:.2f})"
            else:
                position_str = ""
            position_item = QTableWidgetItem(position_str)
            self.injectors_table.setItem(row, 0, name_item)
            self.injectors_table.setItem(row, 1, type_item)
            self.injectors_table.setItem(row, 2, SOI_item)
            self.injectors_table.setItem(row, 3, position_item)
        self.injectors_table.resizeColumnsToContents()
        self.injectors_table.horizontalHeader().setStretchLastSection(True)
        self.injectors_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def add_injector(self):
        from ui.dialogs.injection_dialogs.type_selection_dialog import TypeSelectionDialog
        from PyQt5.QtWidgets import QDialog
        type_selection_dialog = TypeSelectionDialog(parent=self)
        if type_selection_dialog.exec_() == QDialog.Accepted:
            selected_type = type_selection_dialog.selected_type
            if selected_type == "patchInjection":
                dlg = PatchInjectionDialog(parent=self)
            elif selected_type == "coneNozzleInjection":
                from ui.dialogs.injection_dialogs.cone_nozzle_injection_dialog import ConeNozzleInjectionDialog
                dlg = ConeNozzleInjectionDialog(parent=self)
            else:
                QMessageBox.warning(self, "Error", f"Tipo de inyector desconocido: {selected_type}")
                return
            if dlg.exec_() == QDialog.Accepted:
                new_injector = dlg.get_injection_data()
                if any(inj["name"] == new_injector["name"] for inj in self.case_config.get("injections", [])):
                    QMessageBox.warning(self, "Error", f"El inyector '{new_injector['name']}' ya existe.")
                    return
                self.case_config.setdefault("injections", []).append(new_injector)
                self.update_injectors_table()
                self.save_injector_config(new_injector)
                self.save_disperse_phase_config()

    def remove_injector(self):
        selected_items = self.injectors_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Atención", "No has seleccionado ningún inyector para eliminar.")
            return
        selected_row = self.injectors_table.currentRow()
        injector_name = self.injectors_table.item(selected_row, 0).text()
        reply = QMessageBox.question(
            self, 'Confirmar Eliminación',
            f"¿Estás seguro de que deseas eliminar el inyector '{injector_name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            injector = self.case_config["injections"].pop(selected_row)
            self.update_injectors_table()
            self.delete_injector_config(injector)
            self.save_disperse_phase_config()

    def edit_injector(self, index):
        from PyQt5.QtWidgets import QDialog
        row = index.row()
        injector = self.case_config["injections"][row]
        if injector.get("type", "patchInjection") == "patchInjection":
            dlg = PatchInjectionDialog(parent=self, initial_data=injector)
        elif injector.get("type", "patchInjection") == "coneNozzleInjection":
            from ui.dialogs.injection_dialogs.cone_nozzle_injection_dialog import ConeNozzleInjectionDialog
            dlg = ConeNozzleInjectionDialog(parent=self, initial_data=injector)
        else:
            QMessageBox.warning(self, "Error", f"Tipo de inyector desconocido: {injector.get('type')}")
            return
        if dlg.exec_() == QDialog.Accepted:
            updated_injector = dlg.get_injection_data()
            if updated_injector["name"] != injector["name"] and any(inj["name"] == updated_injector["name"] for inj in self.case_config.get("injections", [])):
                QMessageBox.warning(self, "Error", f"El inyector '{updated_injector['name']}' ya existe.")
                return
            self.case_config["injections"][row] = updated_injector
            self.update_injectors_table()
            self.save_injector_config(updated_injector, overwrite=True)
            self.save_disperse_phase_config()

    def save_injector_config(self, injector, overwrite=False):
        if not self.CONFIG_DIR:
            QMessageBox.warning(self, "Error", "El directorio de configuración no está definido.")
            return
        filename = os.path.join(self.CONFIG_DIR, f"{injector['name']}.json")
        mode = 'w' if overwrite else 'x'
        try:
            with open(filename, mode, encoding='utf-8') as f:
                json.dump(injector, f, indent=4, ensure_ascii=False)
        except FileExistsError:
            QMessageBox.warning(self, "Error", f"El archivo para el inyector '{injector['name']}' ya existe.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar la configuración: {str(e)}")

    def delete_injector_config(self, injector):
        if not self.CONFIG_DIR:
            QMessageBox.warning(self, "Error", "El directorio de configuración no está definido.")
            return
        filename = os.path.join(self.CONFIG_DIR, f"{injector['name']}.json")
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo eliminar el archivo de configuración: {str(e)}")

    def get_assigned_species_types(self):
        species_type = self.case_config["discrete_phase_models"]["compositionModel"].get("speciesType", {})
        if isinstance(species_type, list):
            species_type = {species: "Gas" for species in species_type}
            self.case_config["discrete_phase_models"]["compositionModel"]["speciesType"] = species_type
        elif not isinstance(species_type, dict):
            species_type = {}
            self.case_config["discrete_phase_models"]["compositionModel"]["speciesType"] = {}
        return species_type

    def update_composition_model_from_ui(self):
        classified = self.composition_model_widget.get_classified_species()
        species_type = {}
        for category, species_list in classified.items():
            for species in species_list:
                species_type[species] = category
        self.case_config["discrete_phase_models"]["compositionModel"]["speciesType"] = species_type
        if not species_type:
            QMessageBox.warning(self, "Error", "Debe clasificar al menos una especie como Gas, Líquido o Sólido.")
            return
        QMessageBox.information(self, "Éxito", "Clasificación de especies actualizada correctamente.")

    def update_composition_model(self, text):
        self.case_config["discrete_phase_models"]["compositionModel"]["model"] = text
        if text == "singleMixtureFractionCoeffs":
            self.composition_options_widget.setVisible(True)
        else:
            self.composition_options_widget.setVisible(False)
            self.case_config["discrete_phase_models"]["compositionModel"]["speciesType"] = {}
            self.case_config["discrete_phase_models"]["compositionModel"]["fractions"] = {}

    def update_phase_change_model(self, text):
        self.case_config["discrete_phase_models"]["phaseChangeModel"] = self.case_config["discrete_phase_models"].get("phaseChangeModel", {})
        self.case_config["discrete_phase_models"]["phaseChangeModel"]["model"] = text
        if text == "liquidEvaporationCoeffs":
            self.phase_change_options_widget.setVisible(True)
        else:
            self.phase_change_options_widget.setVisible(False)
            self.case_config["discrete_phase_models"]["phaseChangeModel"]["enthalpyTransfer"] = "enthalpyDifference"
            self.case_config["discrete_phase_models"]["phaseChangeModel"]["activeLiquids"] = []

    def hideEvent(self, event):
        # Al abandonar la sección, guardar la configuración completa en Disperse_fase.json
        self.save_disperse_phase_config()
        super().hideEvent(event)

    def save_disperse_phase_config(self):
        filename = os.path.join(self.CONFIG_DIR, "Disperse_fase.json")
        try:
            data_to_save = {
                "discrete_phase_active": self.case_config.get("discrete_phase_active", False),
                "discrete_phase_models": self.case_config.get("discrete_phase_models", {}),
                "injections": self.case_config.get("injections", []),
                "particleTrackProperties": self.case_config.get("particleTrackProperties", {})
            }
            with open(filename, "w") as f:
                json.dump(data_to_save, f, indent=4)
            logging.info(f"Disperse_fase.json guardado correctamente en: {filename}")
            print(f"Disperse_fase.json guardado correctamente en: {filename}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al guardar Disperse_fase.json:\n{e}")

    def open_particle_tracking_options(self):
        from PyQt5.QtWidgets import QDialog
        dlg = OptDisperseFaseDialog(parent=self, initial_data=self.case_config.get("particleTrackProperties", {}))
        if dlg.exec_() == QDialog.Accepted:
            self.case_config["particleTrackProperties"] = dlg.get_tracking_data()
            QMessageBox.information(self, "Tracking actualizado", "La configuración de particleTrackProperties se ha actualizado correctamente.")

    def open_gravity_config(self):
        from ui.dialogs.conf_grav import ConfGravDialog
        from PyQt5.QtWidgets import QDialog
        dlg = ConfGravDialog(parent=self, initial_data={"gravity_vector": self.case_config.get("gravity_vector", [0.0, 0.0, -1.0])})
        if dlg.exec_() == QDialog.Accepted:
            self.case_config["gravity_vector"] = dlg.data["gravity_vector"]

    def open_radiation_options_dialog(self):
        from ui.dialogs.radiation_options_dialog import RadiationOptionsDialog
        from PyQt5.QtWidgets import QDialog
        dlg = RadiationOptionsDialog(parent=self, initial_data=self.case_config.get("radiation_options", {}))
        if dlg.exec_() == QDialog.Accepted:
            self.case_config["radiation_options"] = dlg.radiation_data

    def open_especies_config_dialog(self):
        from ui.dialogs.especies_config_dialog import EspeciesConfigDialog
        from PyQt5.QtWidgets import QDialog
        dlg = EspeciesConfigDialog(parent=self, initial_data=self.case_config.get("especies_options", {}))
        if dlg.exec_() == QDialog.Accepted:
            self.case_config["especies_options"] = dlg.data

    def _read_constant_json(self):
        constant_path = os.path.join(os.getcwd(), "temp", "constant.json")
        if os.path.exists(constant_path):
            try:
                with open(constant_path, "r") as f:
                    data = json.load(f)
                self.case_config.update(data)
            except Exception as e:
                print(f"Error al leer constant.json: {e}")

    def _write_constant_json(self):
        data_to_save = {
            "gravity_active": self.case_config.get("gravity_active", False),
            "gravity_vector": self.case_config.get("gravity_vector", [0.0, 0.0, -1.0]),
            "energy_active": self.case_config.get("energy_active", False),
            "turbulenceModel": self.case_config.get("turbulenceModel", {"category": "Laminar", "model": "Laminar"}),
            "radiation_active": self.case_config.get("radiation_active", False),
            "radiation_options": self.case_config.get("radiation_options", {}),
            "multiPhaseActive": self.case_config.get("multiPhaseActive", False),
            "especiesActive": self.case_config.get("especiesActive", False),
            "phase": self.case_config.get("phase", "singlePhase"),
            "especies_options": self.case_config.get("especies_options", {}),
            "futureExtension": self.case_config.get("futureExtension", None),
            "particleTrackProperties": self.case_config.get("particleTrackProperties", {})
        }
        constant_path = os.path.join(os.getcwd(), "temp", "constant.json")
        try:
            with open(constant_path, "w") as f:
                json.dump(data_to_save, f, indent=4)
        except Exception as e:
            print(f"Error al escribir constant.json: {e}")

    def _show_turbulence_description(self):
        turbulence_info = self.case_config.get("turbulenceModel", "Laminar")
        if isinstance(turbulence_info, dict):
            category = turbulence_info.get("category", "Laminar")
            model = turbulence_info.get("model", "Laminar")
        else:
            if turbulence_info.lower() == "laminar":
                category = "Laminar"
                model = "Laminar"
            else:
                category = "RAS"
                model = turbulence_info
        desc = ""
        if category == "Laminar":
            desc = "Flujo sin turbulencia, aplicable a bajos números de Reynolds."
        elif category == "RAS":
            desc = f"Modelos RANS: {model}. Se recomienda revisar los parámetros específicos en la documentación de OpenFOAM."
        elif category == "DNS":
            desc = "Direct Numerical Simulation (DNS): Resuelve todas las escalas de turbulencia, muy costoso."
        elif category == "LES":
            desc = f"Large Eddy Simulation (LES): {model}. Para LES se recomienda configurar parámetros adicionales (por ejemplo, coeficiente de Smagorinsky)."
        self.turb_desc_label.setText(desc)

    def update_radiation_state(self, text):
        active = (text == "Activada")
        self.case_config["radiation_active"] = active
        self._write_constant_json()

    def update_multiphase_state(self, text):
        active = (text == "Activada")
        self.case_config["multiPhaseActive"] = active
        self.case_config["phase"] = "multiPhase" if active else "singlePhase"

    def update_especies_state(self, text):
        active = (text == "Activada")
        self.case_config["especiesActive"] = active
        self._write_constant_json()


# --- Clase CompositionModelWidget ---
class CompositionModelWidget(QWidget):
    classification_changed = pyqtSignal()

    def __init__(self, available_species, assigned_species_types, case_config, parent=None):
        super().__init__(parent)
        self.available_species = available_species
        self.assigned_species_types = assigned_species_types
        self.case_config = case_config
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Izquierda: Lista de especies activas
        active_layout = QVBoxLayout()
        active_label = QLabel("Especies Activas")
        self.active_list = QListWidget()
        self.active_list.setSelectionMode(QListWidget.SingleSelection)
        active_layout.addWidget(active_label)
        active_layout.addWidget(self.active_list)
        main_layout.addLayout(active_layout)

        # Derecha: Grupos para clasificar
        groups_layout = QHBoxLayout()
        self.gas_group = self.create_group("Gas")
        self.liquid_group = self.create_group("Líquido")
        self.solid_group = self.create_group("Sólido")
        groups_layout.addLayout(self.gas_group)
        groups_layout.addLayout(self.liquid_group)
        groups_layout.addLayout(self.solid_group)
        main_layout.addLayout(groups_layout)

        self.setLayout(main_layout)
        self.populate_lists()

    def create_group(self, group_name):
        layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        label = QLabel(group_name)
        label.setStyleSheet("font-weight: bold;")
        btn_assign = QPushButton("✔")
        btn_assign.setToolTip(f"Asignar a {group_name}")
        btn_assign.clicked.connect(lambda: self.assign_species_to_group(group_name))
        btn_remove = QPushButton("✖")
        btn_remove.setToolTip(f"Quitar de {group_name}")
        btn_remove.clicked.connect(lambda: self.remove_species_from_group(group_name))
        header_layout.addWidget(label)
        header_layout.addWidget(btn_assign)
        header_layout.addWidget(btn_remove)
        header_layout.addStretch()
        list_widget = QListWidget()
        list_widget.setFixedWidth(150)
        list_widget.setSelectionMode(QListWidget.SingleSelection)
        if group_name == "Gas":
            self.gas_list = list_widget
        elif group_name == "Líquido":
            self.liquid_list = list_widget
        elif group_name == "Sólido":
            self.solid_list = list_widget
        layout.addLayout(header_layout)
        layout.addWidget(list_widget)
        return layout

    def populate_lists(self):
        self.active_list.clear()
        for species in self.available_species:
            if species not in self.assigned_species_types:
                item = QListWidgetItem(species)
                item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.active_list.addItem(item)
        self.gas_list.clear()
        self.liquid_list.clear()
        self.solid_list.clear()
        for species, group in self.assigned_species_types.items():
            item = QListWidgetItem(species)
            item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            if group == "Gas":
                self.gas_list.addItem(item)
            elif group == "Líquido":
                self.liquid_list.addItem(item)
            elif group == "Sólido":
                self.solid_list.addItem(item)

    def assign_species_to_group(self, group_name):
        selected_item = self.active_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Atención", "Seleccione una especie activa para asignar.")
            return
        species = selected_item.text()
        self.assigned_species_types[species] = group_name
        row = self.active_list.row(selected_item)
        self.active_list.takeItem(row)
        if group_name == "Gas":
            self.gas_list.addItem(selected_item)
        elif group_name == "Líquido":
            self.liquid_list.addItem(selected_item)
        elif group_name == "Sólido":
            self.solid_list.addItem(selected_item)
        self.case_config["discrete_phase_models"]["compositionModel"]["speciesType"][species] = group_name
        self.classification_changed.emit()

    def remove_species_from_group(self, group_name):
        if group_name == "Gas":
            list_widget = self.gas_list
        elif group_name == "Líquido":
            list_widget = self.liquid_list
        elif group_name == "Sólido":
            list_widget = self.solid_list
        else:
            return
        selected_item = list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Atención", f"Seleccione una especie en {group_name} para quitar.")
            return
        species = selected_item.text()
        row = list_widget.row(selected_item)
        list_widget.takeItem(row)
        self.active_list.addItem(selected_item)
        if species in self.case_config["discrete_phase_models"]["compositionModel"]["speciesType"]:
            del self.case_config["discrete_phase_models"]["compositionModel"]["speciesType"][species]
        self.classification_changed.emit()

    def get_classified_species(self):
        classified = {"Gas": [], "Líquido": [], "Sólido": []}
        for list_widget, category in [(self.gas_list, "Gas"), (self.liquid_list, "Líquido"), (self.solid_list, "Sólido")]:
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                classified[category].append(item.text())
        return classified

    def update_species_lists(self, available_species, assigned_species_types):
        self.available_species = available_species
        self.assigned_species_types = assigned_species_types
        self.populate_lists()

    def update_species_from_selection(self, chosen_species):
        self.available_species = chosen_species
        species_to_remove = [s for s in self.assigned_species_types if s not in chosen_species]
        for s in species_to_remove:
            del self.assigned_species_types[s]
        self.populate_lists()
        

# Fin de CompositionModelWidget

