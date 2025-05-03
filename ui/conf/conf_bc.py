# ui/conf/bc/conf_bc.py

import os
import json
import logging
from PyQt5.QtWidgets import QMessageBox

# Importar los módulos para generar 'U', 'T', 'p', 'p_rgh'
from ui.conf.bc.conf_U import generate_u_file
from ui.conf.bc.conf_T import generate_t_file
from ui.conf.bc.conf_P import generate_p_file
from ui.conf.bc.conf_p_rgh import generate_p_rgh_file

# Importar los módulos de turbulencia
from ui.conf.bc.conf_k import generate_k_file
from ui.conf.bc.conf_epsilon import generate_epsilon_file
from ui.conf.bc.conf_omega import generate_omega_file

# Importar la función para generar 'nut'
from ui.conf.bc.conf_nut import generate_nut_file

# Importar la función para generar archivos de especies
from ui.conf.bc.conf_especies import generate_species_files

# Importar la función para generar 'Ydefault'
from ui.conf.bc.conf_Ydefault import generate_ydefault_file


def generate_boundary_conditions(temp_dir, parent=None):
    """
    Orquesta la generación de los archivos de condiciones de contorno:
      'U', 'T', 'p', 'p_rgh', 'k', 'epsilon', 'omega', 'nut',
    así como los archivos de especies y el archivo 'Ydefault' si la química está activa.

    Se basa en la lectura del archivo boundary_conditions.json (ubicado en temp_dir),
    el cual contiene:
      - boundaryConditions
      - chemistryActive, chosen_species
      - Turbulence_model => puede ser 'kEpsilon', 'kOmega', o False/otro
    En función de dicho modelo de turbulencia, se generan/elimiman k, epsilon, omega.
    """

    logging.info("Iniciando la generación de condiciones de contorno (conf_bc.py).")

    # 1) Ubicar el archivo boundary_conditions.json
    bc_file_path = os.path.join(temp_dir, "boundary_conditions.json")
    bc_file_path = os.path.normpath(bc_file_path)
    logging.info(f"Ruta al archivo boundary_conditions.json: {bc_file_path}")

    if not os.path.exists(bc_file_path):
        error_msg = f"No se encontró el archivo {bc_file_path}."
        QMessageBox.critical(parent, "Error", error_msg)
        logging.error(error_msg)
        return
    else:
        logging.info(f"El archivo {bc_file_path} existe.")

    # 2) Leer boundary_conditions.json
    try:
        with open(bc_file_path, "r", encoding='utf-8') as file:
            boundary_conditions_full = json.load(file)
        logging.info("Boundary Conditions cargadas exitosamente:")
        logging.debug(json.dumps(boundary_conditions_full, indent=4))
    except Exception as e:
        error_msg = f"No se pudo leer el archivo {bc_file_path}: {e}"
        QMessageBox.critical(parent, "Error", error_msg)
        logging.error(error_msg)
        return

    # 3) Extraer secciones importantes
    boundary_conditions = boundary_conditions_full.get("boundaryConditions", {})
    chemistryActive     = boundary_conditions_full.get("chemistryActive", False)
    chosen_species      = boundary_conditions_full.get("chosen_species", [])
    turbulence_model    = boundary_conditions_full.get("Turbulence_model", False)  # 'kEpsilon', 'kOmega' o False

    # 4) Detectar si hay turbulencia, epsilon, omega en las definiciones
    turbulence_active = any(
        isinstance(bc.get("kType"), str) and bc["kType"].strip() != ""
        for bc in boundary_conditions.values()
    )
    epsilon_active = any(
        isinstance(bc.get("epsilonType"), str) and bc["epsilonType"].strip() != ""
        for bc in boundary_conditions.values()
    )
    omega_active = any(
        isinstance(bc.get("omegaType"), str) and bc["omegaType"].strip() != ""
        for bc in boundary_conditions.values()
    )

    logging.info(f"Turbulence_model en JSON: {turbulence_model}")
    logging.info(f"Turbulencia activa: {'Sí' if turbulence_active else 'No'}")
    logging.info(f"Epsilon activa: {'Sí' if epsilon_active else 'No'}")
    logging.info(f"Omega activa: {'Sí' if omega_active else 'No'}")

    # 5) Validar la estructura del JSON
    if not validate_boundary_conditions(boundary_conditions_full,
                                        turbulence_active, epsilon_active, omega_active,
                                        parent):
        error_msg = "El archivo boundary_conditions.json está incompleto o mal formateado."
        QMessageBox.critical(parent, "Error", error_msg)
        logging.error(error_msg)
        return
    else:
        logging.info("Estructura del JSON validada correctamente.")

    # 6) Crear la carpeta temp/DP0/0
    target_dir = os.path.join(temp_dir, "DP0", "0")
    target_dir = os.path.normpath(target_dir)
    try:
        os.makedirs(target_dir, exist_ok=True)
        logging.info(f"Directorio {target_dir} creado o ya existe.")
    except Exception as e:
        error_msg = f"No se pudo crear el directorio {target_dir}: {e}"
        QMessageBox.critical(parent, "Error", error_msg)
        logging.error(error_msg)
        return

    # -------------------------------------------------------------------------
    # 7) Generar archivos básicos (U, T, p, p_rgh)
    try:
        u_file_path = os.path.join(target_dir, "U")
        generate_u_file(temp_dir, u_file_path)
        logging.info(f"Archivo 'U' generado en {u_file_path}.")
    except Exception as e:
        error_msg = f"Error al generar 'U': {e}"
        QMessageBox.critical(parent, "Error", error_msg)
        logging.error(error_msg)
        return

    try:
        t_file_path = os.path.join(target_dir, "T")
        generate_t_file(temp_dir, t_file_path)
        logging.info(f"Archivo 'T' generado en {t_file_path}.")
    except Exception as e:
        error_msg = f"Error al generar 'T': {e}"
        QMessageBox.critical(parent, "Error", error_msg)
        logging.error(error_msg)
        return

    try:
        p_file_path = os.path.join(target_dir, "p")
        generate_p_file(temp_dir, p_file_path)
        logging.info(f"Archivo 'p' generado en {p_file_path}.")
    except Exception as e:
        error_msg = f"Error al generar 'p': {e}"
        QMessageBox.critical(parent, "Error", error_msg)
        logging.error(error_msg)
        return

    try:
        p_rgh_file_path = os.path.join(target_dir, "p_rgh")
        generate_p_rgh_file(temp_dir, p_rgh_file_path)
        logging.info(f"Archivo 'p_rgh' generado en {p_rgh_file_path}.")
    except Exception as e:
        error_msg = f"Error al generar 'p_rgh': {e}"
        QMessageBox.critical(parent, "Error", error_msg)
        logging.error(error_msg)
        return

    # -------------------------------------------------------------------------
    # 8) Generar/Eliminar 'k' según turbulence_model
    k_file_path = os.path.join(target_dir, "k")
    if turbulence_model in ("kEpsilon", "kOmega"):
        try:
            generate_k_file(temp_dir, k_file_path)
            logging.info(f"Archivo 'k' generado en {k_file_path}.")
        except Exception as e:
            error_msg = f"Error al generar 'k': {e}"
            QMessageBox.critical(parent, "Error", error_msg)
            logging.error(error_msg)
            return
    else:
        if os.path.exists(k_file_path):
            try:
                os.remove(k_file_path)
                logging.info(f"Archivo 'k' eliminado (laminar).")
            except Exception as e:
                logging.warning(f"No se pudo eliminar 'k': {e}")

    # Manejo de epsilon y omega
    epsilon_file_path = os.path.join(target_dir, "epsilon")
    omega_file_path   = os.path.join(target_dir, "omega")

    if turbulence_model == "kEpsilon":
        if epsilon_active:
            try:
                generate_epsilon_file(temp_dir, epsilon_file_path)
                logging.info(f"Archivo 'epsilon' generado en {epsilon_file_path}.")
            except Exception as e:
                error_msg = f"Error al generar 'epsilon': {e}"
                QMessageBox.critical(parent, "Error", error_msg)
                logging.error(error_msg)
                return
        else:
            if os.path.exists(epsilon_file_path):
                os.remove(epsilon_file_path)
                logging.info(f"Archivo 'epsilon' eliminado (kepsilon).")

        if os.path.exists(omega_file_path):
            try:
                os.remove(omega_file_path)
                logging.info("Archivo 'omega' eliminado (kEpsilon activo).")
            except Exception as e:
                logging.warning(f"No se pudo eliminar 'omega': {e}")

    elif turbulence_model == "kOmega":
        if omega_active:
            try:
                generate_omega_file(temp_dir, omega_file_path)
                logging.info(f"Archivo 'omega' generado en {omega_file_path}.")
            except Exception as e:
                error_msg = f"Error al generar 'omega': {e}"
                QMessageBox.critical(parent, "Error", error_msg)
                logging.error(error_msg)
                return
        else:
            if os.path.exists(omega_file_path):
                os.remove(omega_file_path)
                logging.info("Archivo 'omega' eliminado (kOmega sin definiciones).")

        if os.path.exists(epsilon_file_path):
            try:
                os.remove(epsilon_file_path)
                logging.info(f"Archivo 'epsilon' eliminado (kOmega activo).")
            except Exception as e:
                logging.warning(f"No se pudo eliminar 'epsilon': {e}")
    else:
        if os.path.exists(epsilon_file_path):
            try:
                os.remove(epsilon_file_path)
                logging.info("Archivo 'epsilon' eliminado (laminar).")
            except Exception as e:
                logging.warning(f"No se pudo eliminar 'epsilon': {e}")

        if os.path.exists(omega_file_path):
            try:
                os.remove(omega_file_path)
                logging.info("Archivo 'omega' eliminado (laminar).")
            except Exception as e:
                logging.warning(f"No se pudo eliminar 'omega': {e}")

    # Generar nut
    try:
        nut_file_path = os.path.join(target_dir, "nut")
        generate_nut_file(boundary_conditions, nut_file_path)
        logging.info(f"Archivo 'nut' generado en {nut_file_path}.")
    except Exception as e:
        error_msg = f"Error al generar 'nut': {e}"
        QMessageBox.critical(parent, "Error", error_msg)
        logging.error(error_msg)
        return

    # Archivos de especies
    chemistryActive = boundary_conditions_full.get("chemistryActive", False)
    chosen_species  = boundary_conditions_full.get("chosen_species", [])
    if chemistryActive and chosen_species:
        try:
            generate_species_files(boundary_conditions, chosen_species, target_dir)
            generate_ydefault_file(boundary_conditions, target_dir)
            logging.info("Archivos de especies y 'Ydefault' generados con éxito.")
        except Exception as e:
            error_msg = f"Error al generar especies o Ydefault: {e}"
            QMessageBox.critical(parent, "Error", error_msg)
            logging.error(error_msg)
            return
    else:
        logging.info("No se generarán archivos de especies ni 'Ydefault' (química desactivada o sin especies).")

    # Mensaje final de éxito
    msg = "Se han generado correctamente los archivos de condiciones de contorno: 'U', 'T', 'p', 'p_rgh'"
    if turbulence_model in ("kEpsilon", "kOmega"):
        msg += ", 'k'"
        if turbulence_model == "kEpsilon":
            msg += ", 'epsilon'"
        elif turbulence_model == "kOmega":
            msg += ", 'omega'"
    msg += ", 'nut'"

    if chemistryActive and chosen_species:
        msg += " y archivos de especies activas + 'Ydefault'."

    QMessageBox.information(parent, "Éxito", msg)
    logging.info(msg)


def validate_boundary_conditions(bc_data, turbulence_active, epsilon_active, omega_active, parent=None):
    logging.debug("Iniciando validación de boundary_conditions.json en conf_bc.py.")
    required_fields = ["ambientPressure", "ambientTemperature", "boundaryConditions"]
    for field in required_fields:
        if field not in bc_data:
            logging.error(f"Campo requerido '{field}' no encontrado en JSON.")
            return False

    # Validar cada condición de contorno
    for name, bc in bc_data["boundaryConditions"].items():
        btype = bc.get("type", "").lower()
        if not btype:
            if name.lower() == "walls":
                btype = "wall"
                logging.debug(f"Inferido 'wall' para la condición '{name}'.")
            else:
                logging.error(f"Campo 'type' no encontrado en la condición '{name}'.")
                return False

        if btype == "inlet":
            required_inlet_fields = ["velocityType", "velocityValue", "velocityInit", "temperature"]
            for f in required_inlet_fields:
                if f not in bc:
                    logging.error(f"Campo '{f}' no encontrado en 'Inlet' '{name}'.")
                    return False
        elif btype == "outlet":
            required_outlet_fields = ["pressureValue", "temperature"]
            for f in required_outlet_fields:
                if f not in bc:
                    logging.error(f"Campo '{f}' no encontrado en 'Outlet' '{name}'.")
                    return False
        elif btype == "wall":
            # Ahora aceptamos slipType O noFriction
            if "slipType" not in bc and "noFriction" not in bc:
                logging.error(f"Ni 'slipType' ni 'noFriction' encontrado en 'Wall' '{name}'.")
                return False
            # Temperatura requerida: temperature O wallTemperature
            if "temperature" not in bc and "wallTemperature" not in bc:
                logging.error(f"Ni 'temperature' ni 'wallTemperature' encontrado en 'Wall' '{name}'.")
                return False
        else:
            logging.error(f"Tipo de contorno desconocido '{btype}' para '{name}'.")
            return False

        # Revisar turbulencia (k, epsilon, omega)
        if turbulence_active and isinstance(bc.get("kType"), str) and bc["kType"].strip() != "":
            if "kValue" not in bc:
                logging.error(f"Campo 'kValue' no encontrado en '{name}' (turbulencia activa).")
                return False
        if epsilon_active and isinstance(bc.get("epsilonType"), str) and bc["epsilonType"].strip() != "":
            if "epsilonValue" not in bc:
                logging.error(f"Campo 'epsilonValue' no encontrado en '{name}' (epsilon activa).")
                return False
        if omega_active and isinstance(bc.get("omegaType"), str) and bc["omegaType"].strip() != "":
            if "omegaValue" not in bc:
                logging.error(f"Campo 'omegaValue' no encontrado en '{name}' (omega activa).")
                return False

    logging.debug("Validación completada con éxito en conf_bc.py.")
    return True
