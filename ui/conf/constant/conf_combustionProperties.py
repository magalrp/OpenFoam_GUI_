# ui/conf/constant/conf_combustionProperties.py

import os
import json
import logging

from core.species_library import get_species_library

def generate_combustionProperties(case_config: dict, main_dir: str):
    """
    Genera:
      - temp/DP0/constant/combustionProperties
      - temp/DP0/constant/chemkin/therm.dat filtrado para las especies activas

    Se basa en boundary_conditions.json para:
      - chemistryActive (bool)
      - chosen_species (list of str)
    """

    # 1) Leer boundary_conditions.json
    temp_dir = os.path.join(main_dir, "temp")
    bc_path = os.path.join(temp_dir, "boundary_conditions.json")
    try:
        with open(bc_path, "r", encoding="utf-8") as f:
            bc = json.load(f)
    except Exception as e:
        logging.error(f"No se pudo leer boundary_conditions.json: {e}")
        return

    chemistry_active = bc.get("chemistryActive", False)
    chosen = bc.get("chosen_species", [])

    # 2) Directorio DP0/constant
    dp0_const = os.path.join(temp_dir, "DP0", "constant")
    os.makedirs(dp0_const, exist_ok=True)

    # Si la química está desactivada, eliminar chemkin y combustionProperties
    chemkin_dir = os.path.join(dp0_const, "chemkin")
    comb_prop_path = os.path.join(dp0_const, "combustionProperties")
    if not chemistry_active or not chosen:
        # eliminar si existía
        if os.path.isdir(chemkin_dir):
            try:    os.rmdir(chemkin_dir)
            except: pass
        if os.path.isfile(comb_prop_path):
            try:    os.remove(comb_prop_path)
            except: pass
        logging.info("Química desactivada: no se crea combustionProperties ni chemkin/")
        return

    # 3) Generar combustionProperties
    #    (solo plantillas mínimas, ajusta si necesitas más campos)
    tpl = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  {version}                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      combustionProperties;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

combustionModel {model};

active          yes;

// ************************************************************************* //
"""
    version = case_config.get("chemistry", {}).get("version", "v2406")
    model   = case_config.get("chemistry", {}).get("combustionModel", "PaSR")

    try:
        with open(comb_prop_path, "w", encoding="utf-8") as f:
            f.write(tpl.format(version=version, model=model))
        logging.info(f"'combustionProperties' generado en: {comb_prop_path}")
    except Exception as e:
        logging.error(f"Error escribiendo combustionProperties: {e}")

    # 4) Crear chemkin_dir y escribir therm.dat
    os.makedirs(chemkin_dir, exist_ok=True)
    lib_text = get_species_library().splitlines()

    # Extraer header (líneas iniciales) y final 'END'
    try:
        hdr_idx = next(i for i, L in enumerate(lib_text) if L.strip().startswith("THERMO"))
        end_idx = next(i for i, L in enumerate(lib_text) if L.strip() == "END")
    except StopIteration:
        logging.error("species_library no contiene bloque 'THERMO ... END'")
        return

    header = lib_text[hdr_idx : hdr_idx + 2]  # THERMO ALL + rango
    footer = ["END"]

    # Construir bloques por especie
    # recorrer líneas entre header y footer, agrupar por especie
    species_blocks = {}
    block = []
    current = None
    for line in lib_text[hdr_idx + 2 : end_idx]:
        if not line.startswith(" ") and line.strip():
            # línea de cabecera de especie
            if current and block:
                species_blocks[current] = block
            parts = line.strip().split()
            current = parts[0]
            block = [line]
        else:
            block.append(line)
    if current and block:
        species_blocks[current] = block

    # Filtrar especies activas
    out = []
    out.extend(header)
    for sp in chosen:
        if sp in species_blocks:
            out.extend(species_blocks[sp])
        else:
            logging.error(f"🔴 Falta datos termo NASA para especie activa: '{sp}'")
    out.extend(footer)

    # Escribir therm.dat
    therm_path = os.path.join(chemkin_dir, "therm.dat")
    try:
        with open(therm_path, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
        logging.info(f"'therm.dat' generado en: {therm_path}")
    except Exception as e:
        logging.error(f"Error escribiendo therm.dat: {e}")
