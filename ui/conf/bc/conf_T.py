# ui/conf/bc/conf_T.py

import os
import json
import logging

def generate_t_file(temp_dir, t_file_path):
    """
    Genera el archivo 'T' tomando datos desde boundary_conditions.json en 'temp_dir'
    y lo escribe en 't_file_path'.

    Pasos:
      1) Verifica los parámetros (temp_dir y t_file_path).
      2) Ubica y lee el archivo boundary_conditions.json (buscándolo en temp_dir).
      3) Toma el 'ambientTemperature' del JSON o usa 300.0 por defecto.
      4) Genera la sección boundaryField para cada frontera (inlet, outlet, wall, etc.)
         según la variable 'temperature' de cada una.
      5) Escribe el archivo T en la ruta t_file_path.
    """

    logging.debug("[generate_t_file] Iniciando generación del archivo 'T'.")

    # 1) Verificar parámetros
    if not isinstance(temp_dir, str):
        logging.error("[generate_t_file] 'temp_dir' debe ser str. Abortando.")
        return
    if not isinstance(t_file_path, str):
        logging.error("[generate_t_file] 't_file_path' debe ser str. Abortando.")
        return

    # 2) Ubicar y leer boundary_conditions.json
    bc_json_path = os.path.join(temp_dir, "boundary_conditions.json")
    bc_json_path = os.path.normpath(bc_json_path)

    if not os.path.exists(bc_json_path):
        logging.error(f"[generate_t_file] No se encontró {bc_json_path}. No se generará 'T'.")
        return

    try:
        with open(bc_json_path, "r", encoding="utf-8") as f:
            bc_data = json.load(f)
        logging.info(f"[generate_t_file] Cargado '{bc_json_path}' exitosamente.")
    except Exception as e:
        logging.error(f"[generate_t_file] Error al leer '{bc_json_path}': {e}")
        return

    # 3) Obtener boundaryConditions y ambientTemperature
    boundary_conditions = bc_data.get("boundaryConditions", {})
    ambient_temperature = bc_data.get("ambientTemperature", 300.0)
    logging.debug(f"[generate_t_file] Temperatura Ambiente (K): {ambient_temperature}")

    # 4) Construir el encabezado
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
    object      T;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 0 0 1 0 0 0];

internalField   uniform {ambient_temperature};

boundaryField
{{
"""

    # 5) Generar los entries para cada frontera
    boundary_entries = []
    for name, bc in boundary_conditions.items():
        btype = bc.get("type", "").lower()
        # Si no hay 'temperature' en la frontera, usar ambient_temperature como fallback
        frontier_temp = bc.get("temperature", ambient_temperature)
        logging.debug(f"[generate_t_file] Procesando '{name}' (type='{btype}') con T={frontier_temp}")

        if btype == "inlet":
            entry = f"""
    {name}
    {{
        type            fixedValue;
        value           uniform {frontier_temp};
    }}
"""
        elif btype == "outlet":
            entry = f"""
    {name}
    {{
        type            inletOutlet;
        inletValue      uniform {frontier_temp};
        value           uniform {frontier_temp};
    }}
"""
        elif btype == "wall":
            entry = f"""
    {name}
    {{
        type            zeroGradient;
    }}
"""
        else:
            # Fronteras desconocidas => zeroGradient por defecto
            entry = f"""
    {name}
    {{
        type            zeroGradient;
    }}
"""
        boundary_entries.append(entry)

    # 6) Pie final
    footer = """
} // Fin de boundaryField


// ************************************************************************* //
"""

    # 7) Contenido completo
    t_content = header + "".join(boundary_entries) + footer
    logging.debug("[generate_t_file] Contenido construido para 'T':\n" + t_content)

    # 8) Asegurar directorio de salida
    try:
        os.makedirs(os.path.dirname(t_file_path), exist_ok=True)
    except Exception as e:
        logging.error(f"[generate_t_file] No se pudo crear directorio de salida para T: {e}")
        return

    # 9) Escribir el archivo T
    try:
        with open(t_file_path, "w", encoding="utf-8") as t_file:
            t_file.write(t_content)
        logging.info(f"[generate_t_file] Archivo 'T' escrito exitosamente en {t_file_path}.")
    except Exception as e:
        logging.error(f"[generate_t_file] Error al escribir '{t_file_path}': {e}")
        return

    logging.info("[generate_t_file] Finalizó sin errores.")
