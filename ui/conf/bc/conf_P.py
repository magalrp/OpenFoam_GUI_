# ui/conf/bc/conf_p.py

import os
import json
import logging

def generate_p_file(temp_dir, p_file_path):
    """
    Genera el archivo 'p' tomando datos desde boundary_conditions.json (en 'temp_dir')
    y lo escribe en 'p_file_path'.

    Pasos principales:
      1) Verifica parámetros (temp_dir y p_file_path).
      2) Ubica y lee boundary_conditions.json en temp_dir.
      3) Obtiene ambientPressure (o usa 100000 por defecto).
      4) Escribe el archivo 'p' con internalField uniform = ambientPressure
         y un bloque boundaryField para cada frontera, con:
               type  calculated;
               value $internalField;
         (tal como en tu ejemplo).
    """

    logging.debug("[generate_p_file] Iniciando generación del archivo 'p'.")

    # 1) Verificar parámetros
    if not isinstance(temp_dir, str):
        logging.error("[generate_p_file] 'temp_dir' debe ser str. Abortando.")
        return
    if not isinstance(p_file_path, str):
        logging.error("[generate_p_file] 'p_file_path' debe ser str. Abortando.")
        return

    # 2) Ubicar boundary_conditions.json
    bc_json_path = os.path.join(temp_dir, "boundary_conditions.json")
    bc_json_path = os.path.normpath(bc_json_path)

    if not os.path.exists(bc_json_path):
        logging.error(f"[generate_p_file] No se encontró {bc_json_path}. No se generará 'p'.")
        return

    # 3) Leer boundary_conditions.json
    try:
        with open(bc_json_path, "r", encoding="utf-8") as f:
            bc_data = json.load(f)
        logging.info(f"[generate_p_file] Cargado '{bc_json_path}' exitosamente.")
    except Exception as e:
        logging.error(f"[generate_p_file] Error al leer '{bc_json_path}': {e}")
        return

    # 4) Obtener ambientPressure y boundaryConditions
    boundary_conditions = bc_data.get("boundaryConditions", {})
    ambient_pressure = bc_data.get("ambientPressure", 100000.0)
    logging.debug(f"[generate_p_file] Presión Ambiente (Pa): {ambient_pressure}")

    # Encabezado del archivo
    header = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2406                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      p;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [1 -1 -2 0 0 0 0];

internalField   uniform {ambient_pressure};

boundaryField
{{
"""

    # 5) Sección boundaryField para cada frontera
    boundary_entries = []
    for bc_name in boundary_conditions.keys():
        # En tu ejemplo, sin importar si es inlet / outlet / wall / etc.,
        # se escribe el mismo bloque:
        entry = f"""
    {bc_name}
    {{
        type            calculated;
        value           $internalField;
    }}
"""
        boundary_entries.append(entry)

    # 6) Pie del archivo
    footer = """}
\n// ************************************************************************* //
"""

    # Unir todo el contenido
    p_content = header + "".join(boundary_entries) + footer
    logging.debug("[generate_p_file] Contenido construido para 'p':\n" + p_content)

    # Asegurar directorio de salida
    try:
        os.makedirs(os.path.dirname(p_file_path), exist_ok=True)
    except Exception as e:
        logging.error(f"[generate_p_file] No se pudo crear directorio de salida para 'p': {e}")
        return

    # Escribir el archivo p
    try:
        with open(p_file_path, "w", encoding="utf-8") as p_file:
            p_file.write(p_content)
        logging.info(f"[generate_p_file] Archivo 'p' escrito exitosamente en '{p_file_path}'.")
    except Exception as e:
        logging.error(f"[generate_p_file] Error al escribir '{p_file_path}': {e}")
        return

    logging.info("[generate_p_file] Finalizó sin errores.")
