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
from ui.conf.constant.conf_thermophysicalProperties import generate_thermophysicalProperties

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

    Archivos generados:
      - turbulenceProperties
      - radiationProperties
      - g (si gravity_active)
      - thermophysicalProperties
      - chemistryProperties (si especiesActive)
      - combustionProperties (si combustión activa)
      - particleTrackProperties (si fase discreta activa)
    """
    # 1) Incorporar valores de constant.json
    constant_data = load_constant_config(root_dir)
    if constant_data:
        case_config.update(constant_data)

    # 2) Directorio de salida
    constant_dir = os.path.join(root_dir, "temp", "DP0", "constant")
    os.makedirs(constant_dir, exist_ok=True)
    logging.info(f"Generando archivos en: {constant_dir}")

    # --- turbulenceProperties ---
    turb_file = os.path.join(constant_dir, "turbulenceProperties")
    turb = case_config.get("turbulenceModel", {"category": "Laminar", "model": "Laminar"})
    if isinstance(turb, dict):
        cat = turb.get("category", "Laminar")
        mdl = turb.get("model", "Laminar")
        final_model = "laminar" if cat.lower() == "laminar" else mdl
    else:
        final_model = "laminar" if str(turb).lower() == "laminar" else turb
    turb_cfg = {
        "turbulenceModel": final_model,
        "turbulence": "on" if str(final_model).lower() != "laminar" else "off",
        "printCoeffs": "on"
    }
    generate_turbulenceProperties(turb_cfg, turb_file)

    # --- radiationProperties ---
    rad_file = os.path.join(constant_dir, "radiationProperties")
    generate_radiationProperties(case_config, rad_file)

    # --- g (gravedad) ---
    if case_config.get("gravity_active", False):
        g_file = os.path.join(constant_dir, "g")
        generate_g_file(case_config, g_file)
        logging.info(f"Archivo 'g' generado en: {g_file}")

    # --- thermophysicalProperties ---
    thermo_cfg = case_config.get("thermophysicalProperties", {})
    thermo_file = os.path.join(constant_dir, "thermophysicalProperties")
    generate_thermophysicalProperties(thermo_cfg, thermo_file)

    # --- chemistryProperties ---
    chem_file = os.path.join(constant_dir, "chemistryProperties")
    if case_config.get("especiesActive", False):
        generate_chemistryProperties(case_config, chem_file)
        logging.info(f"Archivo 'chemistryProperties' generado en: {chem_file}")
    else:
        if os.path.exists(chem_file):
            os.remove(chem_file)
            logging.info("Archivo 'chemistryProperties' eliminado (especies off)")

    # --- combustionProperties ---
    comb_file = os.path.join(constant_dir, "combustionProperties")
    especies_on = case_config.get("especiesActive", False)
    modelo_comb = case_config.get("especies_options", {}).get("modelo", "")
    comb_on = especies_on and modelo_comb in ["combustionSinPremezcla", "combustionPremezclada"]
    if comb_on:
        generate_combustionProperties(case_config, comb_file)
        logging.info(f"Archivo 'combustionProperties' generado en: {comb_file}")
    else:
        if os.path.exists(comb_file):
            os.remove(comb_file)
            logging.info("Archivo 'combustionProperties' eliminado (combustión off)")

    # --- particleTrackProperties ---
    disp_data = load_disperse_phase_config(root_dir)
    dp_on = disp_data.get("discrete_phase_active", False)
    pt_cfg = disp_data.get("particleTrackProperties", {})
    if dp_on:
        if not pt_cfg:
            pt_cfg = {
                "cloudName": "reactingCloud1",
                "sampleFrequency": 1,
                "maxPositions": 1000000,
                "setFormat": "vtk",
                "fields": "",
                "maxTracks": -1
            }
        case_config["particleTrackProperties"] = pt_cfg
        pt_file = os.path.join(constant_dir, "particleTrackProperties")
        generate_particleTrackProperties(case_config, pt_file)
        logging.info(f"Archivo 'particleTrackProperties' generado en: {pt_file}")
    else:
        pt_file = os.path.join(constant_dir, "particleTrackProperties")
        if os.path.exists(pt_file):
            os.remove(pt_file)
            logging.info("Archivo 'particleTrackProperties' eliminado (fase discreta off)")

    logging.info("Archivos del directorio constant generados correctamente.")


if __name__ == "__main__":
    # Ejemplo de uso
    example = {
        "turbulenceModel": {"category": "RAS", "model": "kEpsilon"},
        "gravity_active": True,
        "gravity_vector": [0.0, 0.0, -9.81],
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
        "thermophysicalProperties": {
            "version": "v2406",
            "type": "heRhoThermo",
            "mixture": "reactingMixture",
            "transport": "sutherland",
            "thermo": "janaf",
            "energy": "sensibleEnthalpy",
            "equationOfState": "perfectGas",
            "specie": "specie",
            "chemkin_dir": "<case>/chemkin",
            "newFormat": True,
            "inertSpecie": "N2",
            "liquids": ["C7H16"],
            "solids": []
        },
        "discrete_phase_active": True,
        "particleTrackProperties": {
            "cloudName": "genericCloud",
            "sampleFrequency": 1,
            "maxPositions": 1000000,
            "setFormat": "vtk",
            "fields": "",
            "maxTracks": -1
        }
    }
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    generate_constant_files(example, root)
