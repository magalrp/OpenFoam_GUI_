# ui/conf/conf_constant.py
import os
import json
import logging

from ui.conf.constant.conf_turbulenceProperties import generate_turbulenceProperties
from ui.conf.constant.conf_radiation import generate_radiationProperties
from ui.conf.constant.conf_g import generate_g_file
from ui.conf.constant.conf_chem import generate_chemistryProperties
from ui.conf.constant.conf_combustion import generate_combustionProperties
from ui.conf.constant.conf_particleTrack import generate_particleTrackProperties

def load_constant_config(root_dir):
    """
    Lee el archivo constant.json ubicado en root_dir/temp/constant.json
    y retorna un diccionario con su contenido.
    """
    constant_file = os.path.join(root_dir, "temp", "constant.json")
    if os.path.exists(constant_file):
        try:
            with open(constant_file, "r") as f:
                constant_data = json.load(f)
            logging.info(f"constant.json leído correctamente desde {constant_file}")
            return constant_data
        except Exception as e:
            logging.error(f"Error al leer constant.json: {e}")
            return {}
    else:
        logging.warning(f"constant.json no existe en {constant_file}")
        return {}

def load_disperse_phase_config(root_dir):
    """
    Lee el archivo Disperse_fase.json ubicado en root_dir/temp/Disperse_fase.json
    y retorna un diccionario con su contenido.
    """
    disperse_file = os.path.join(root_dir, "temp", "Disperse_fase.json")
    if os.path.exists(disperse_file):
        try:
            with open(disperse_file, "r") as f:
                disperse_data = json.load(f)
            logging.info(f"Disperse_fase.json leído correctamente desde {disperse_file}")
            return disperse_data
        except Exception as e:
            logging.error(f"Error al leer Disperse_fase.json: {e}")
            return {}
    else:
        logging.warning(f"Disperse_fase.json no existe en {disperse_file}")
        return {}

def generate_constant_files(case_config, root_dir):
    """
    Genera los archivos del directorio constant (en temp/DP0/constant)
    basándose en la configuración actual (case_config).

    Se generan:
      - turbulenceProperties
      - radiationProperties
      - g (si la gravedad está activa)
      - chemistryProperties (si especiesActive está activado)
      - combustionProperties (si la combustión está activa)
      - particleTrackProperties (si la fase discreta está activa según Disperse_fase.json)
    """
    # Actualiza case_config con constant.json (si existe)
    constant_data = load_constant_config(root_dir)
    if constant_data:
        case_config.update(constant_data)
    
    # Ruta de salida para DP0/constant
    constant_dir = os.path.join(root_dir, "temp", "DP0", "constant")
    if not os.path.exists(constant_dir):
        os.makedirs(constant_dir)
    logging.info(f"Generando archivos en: {constant_dir}")
    
    # --- turbulenceProperties ---
    turbulence_file = os.path.join(constant_dir, "turbulenceProperties")
    turb = case_config.get("turbulenceModel", {"category": "Laminar", "model": "Laminar"})
    if isinstance(turb, dict):
        category = turb.get("category", "Laminar")
        model = turb.get("model", "Laminar")
        final_model = "laminar" if category.lower() == "laminar" else model
    else:
        final_model = "laminar" if turb.lower() == "laminar" else turb
    turbulence_config = {
        "turbulenceModel": final_model,
        "turbulence": "on" if final_model.lower() != "laminar" else "off",
        "printCoeffs": "on"
    }
    generate_turbulenceProperties(turbulence_config, turbulence_file)
    
    # --- radiationProperties ---
    radiation_file = os.path.join(constant_dir, "radiationProperties")
    generate_radiationProperties(case_config, radiation_file)
    
    # --- g (gravedad) ---
    if case_config.get("gravity_active", False):
        g_file = os.path.join(constant_dir, "g")
        generate_g_file(case_config, g_file)
        logging.info(f"Archivo 'g' generado correctamente en: {g_file}")
    
    # --- chemistryProperties ---
    chemistry_file = os.path.join(constant_dir, "chemistryProperties")
    if case_config.get("especiesActive", False):
        generate_chemistryProperties(case_config, chemistry_file)
        logging.info(f"Archivo 'chemistryProperties' generado correctamente en: {chemistry_file}")
    else:
        if os.path.exists(chemistry_file):
            os.remove(chemistry_file)
            logging.info("Archivo 'chemistryProperties' eliminado porque las especies están apagadas.")
    
    # --- combustionProperties ---
    combustion_file = os.path.join(constant_dir, "combustionProperties")
    especies_active = case_config.get("especiesActive", False)
    modelo_comb = case_config.get("especies_options", {}).get("modelo", "None")
    combustion_active = especies_active and (modelo_comb in ["combustionSinPremezcla", "combustionPremezclada"])
    if combustion_active:
        generate_combustionProperties(case_config, combustion_file)
        logging.info(f"Archivo 'combustionProperties' generado correctamente en: {combustion_file}")
    else:
        if os.path.exists(combustion_file):
            os.remove(combustion_file)
            logging.info("Archivo 'combustionProperties' eliminado porque la combustión no está activa o las especies están apagadas.")
    
    # --- particleTrackProperties ---
    # Cargar la configuración de fase discreta desde Disperse_fase.json
    disperse_data = load_disperse_phase_config(root_dir)
    discrete_active = disperse_data.get("discrete_phase_active", False)
    particle_track_config = disperse_data.get("particleTrackProperties", {})
    if discrete_active:
        # Si no se encuentra la configuración, se asignan valores por defecto
        if not particle_track_config:
            particle_track_config = {
                "cloudName": "reactingCloud1",
                "sampleFrequency": 1,
                "maxPositions": 1000000,
                "setFormat": "vtk",
                "fields": "",
                "maxTracks": -1
            }
        # Actualiza case_config para que generate_particleTrackProperties lo use
        case_config["particleTrackProperties"] = particle_track_config
        generate_particleTrackProperties(case_config, os.path.join(constant_dir, "particleTrackProperties"))
        logging.info(f"Archivo 'particleTrackProperties' generado correctamente en: {os.path.join(constant_dir, 'particleTrackProperties')}")
    else:
        particle_track_file = os.path.join(constant_dir, "particleTrackProperties")
        if os.path.exists(particle_track_file):
            os.remove(particle_track_file)
            logging.info("Archivo 'particleTrackProperties' eliminado porque la fase discreta no está activa.")
    
    logging.info("Archivos del directorio constant generados correctamente.")

if __name__ == "__main__":
    # Ejemplo de uso
    example_config = {
        "turbulenceModel": {"category": "RAS", "model": "kEpsilon"},
        "gravity_active": True,
        "gravity_vector": [0.0, 0.0, -1.0],
        "radiation_active": True,
        "radiation_options": {
            "radiationModel": "viewFactor",
            "nTheta": 8,
            "nPhi": 8,
            "solverFreq": 1
        },
        "especiesActive": True,
        "especies_options": {
            "chemSolver": "ODE",
            "chemSolverParams": {
                "initial_time": 1e-07,
                "ode_solver": "seulex",
                "eps": 0.05
            },
            "modelo": "combustionSinPremezcla",
            "combustionParams": {
                "Cmix": 1.0,
                "A": 4.0,
                "B": 0.5,
                "ZFen": 0.2,
                "tauRes": 0.01,
                "reactionRateFactor": 1.0
            }
        },
        "discrete_phase_active": True,  # Aunque esta clave puede no estar en constant.json, se usa aquí para ejemplo
        # La configuración de particleTrackProperties se esperaría que esté en Disperse_fase.json,
        # pero se puede definir aquí para forzar un ejemplo:
        "particleTrackProperties": {
            "cloudName": "genericCloud",
            "sampleFrequency": 1,
            "maxPositions": 1000000,
            "setFormat": "vtk",
            "fields": "",
            "maxTracks": -1
        }
    }
    root_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    generate_constant_files(example_config, root_directory)
