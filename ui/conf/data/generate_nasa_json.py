# ui/conf/data/generate_nasa_json.py

import os
import sys
import json
import logging
from pathlib import Path

import requests
from requests.exceptions import HTTPError, RequestException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# URLs probadas de GRI-Mech 3.0 thermo30.dat
PRIMARY_URL = (
    "https://raw.githubusercontent.com/ReactionMechanismGenerator/"
    "GRI-Mech-III/master/GRI-Mech/thermo/data/thermo30.dat"
)
FALLBACK_URL = "https://combustion.berkeley.edu/gri-mech/version30/files/thermo30.dat"

# Especies que queremos extraer
TARGET_SPECIES = [
    "N2", "O2", "H2", "H", "OH", "H2O", "HO2", "H2O2", "CH4", "CO",
    "CO2", "C2H2", "C2H4", "C2H6", "CH2O", "CH3", "CH3O", "CH3OH", "C", "CN",
    "HCN", "NH3", "NO", "NO2", "N2O", "AR", "HE", "Ne", "Kr", "Xe",
    "C2H5", "C3H8", "C4H10", "C7H16", "isoButane", "nButane", "IC8H18", "JetA",
    "CH2", "CH2*", "CH3*", "CH4*", "C6H6", "C6H5", "CH3CHO", "CH3CO",
    "CH2CO", "CH3COCH3", "COOH", "HCO", "CH3COCH2", "C2H5OH", "CH3CH2OH", "acetone",
    "acetaldehyde", "glyoxal", "soot", "TiCl4", "SiO2", "SO2", "SO3", "HSO3",
    "H2S", "C3H3", "C3H5", "C3H7", "C3H7O", "C3H6", "C5H5", "C7H8", "CH3CN",
    "CH3Cl", "CH3Br", "CH3I", "CH3NH2", "HNO3", "HNO2", "N2H4", "NH2",
    "Cl2", "F2", "HF", "HCl", "PF3", "PH3", "NF3", "SF6", "CF4",
    "C2F6", "C3F8", "C2HF5", "CH2F2", "CHF3", "CCl4", "CHCl3", "CH2Cl2", "CH3Cl2",
    "benzene", "toluene", "xylene", "styrene", "ethanol", "methanol"
]


def download_nasa_dat() -> str:
    """
    Intenta descargar thermo30.dat de PRIMARY_URL.
    Si responde 404, prueba con FALLBACK_URL.
    Devuelve el texto completo o lanza excepción si ninguna funciona.
    """
    for url in (PRIMARY_URL, FALLBACK_URL):
        try:
            logging.info(f"→ Descargando thermo30.dat desde {url} …")
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            logging.info("   → Descarga satisfactoria.")
            return r.text
        except HTTPError as e:
            status = getattr(e.response, 'status_code', None)
            logging.warning(f"   → Falló descarga ({status}), {url}")
        except RequestException as e:
            logging.warning(f"   → Error de conexión a {url}: {e}")

    raise RuntimeError(
        "No ha sido posible descargar 'thermo30.dat'.\n"
        "Comprueba tu conexión o descarga manualmente desde:\n"
        "  • https://combustion.berkeley.edu/gri-mech/version30/files/thermo30.dat\n"
        "y guárdalo en 'ui/conf/data/thermo30.dat'."
    )


def parse_nasa_dat(dat_text: str) -> dict:
    """
    Parse thermo30.dat en formato NASA 7-coefs. Devuelve un dict:
      { 'Especie': { T_low, T_high, T_mid, coeffs_low: [...], coeffs_high: [...] }, ... }
    Sólo se incluyen las TARGET_SPECIES.
    """
    lines = dat_text.splitlines()
    thermo = {}
    i = 0
    n = len(lines)

    while i < n:
        header = lines[i].strip()
        # Línea de header de especie: nombre + T_low,T_high,T_mid
        if not header or header.startswith("!"):
            i += 1
            continue
        spc = header[:18].strip()
        if spc in TARGET_SPECIES:
            # extraer temperaturas
            T_low  = float(header[44:52])
            T_high = float(header[53:61])
            T_mid  = float(header[62:70])
            # coeficientes low (líneas i+1 y i+2)
            coefs_low = (
                lines[i+1][0:15]  + lines[i+1][15:30]  +
                lines[i+2][0:15]  + lines[i+2][15:30]  +
                lines[i+2][30:45]
            ).split()
            coefs_low = [float(c) for c in coefs_low]
            # coeficientes high (líneas i+3, i+4)
            coefs_high = (
                lines[i+3][0:15]  + lines[i+3][15:30]  +
                lines[i+4][0:15]  + lines[i+4][15:30]  +
                lines[i+4][30:45]
            ).split()
            coefs_high = [float(c) for c in coefs_high]

            thermo[spc] = {
                "T_low":  T_low,
                "T_high": T_high,
                "T_mid":  T_mid,
                "coeffs_low":  coefs_low,
                "coeffs_high": coefs_high
            }
            logging.info(f"   • {spc}: registrado.")
        # saltar bloque de 5 líneas
        i += 5

    missing = set(TARGET_SPECIES) - set(thermo.keys())
    if missing:
        logging.warning(f"No se encontraron datos para: {', '.join(sorted(missing))}")
    return thermo


def save_as_json(thermo: dict, out_path: str):
    """
    Guarda el dict thermo en formato JSON indentado.
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(thermo, f, indent=2, ensure_ascii=False)
    logging.info(f"→ Guardado JSON en: {out_path}")


def main():
    try:
        dat_text = download_nasa_dat()
        thermo_map = parse_nasa_dat(dat_text)
        out_file = Path(__file__).parent / "nasa_coeffs.json"
        save_as_json(thermo_map, str(out_file))
        logging.info("¡Proceso completado con éxito!")
    except Exception as e:
        logging.error("ERROR: " + str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
