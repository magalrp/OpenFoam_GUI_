# ui/conf/bc/conf_epsilon.py

import os
import json
import logging

def generate_epsilon_file(root_temp_dir, epsilon_output_path):
    """
    Genera el archivo 'epsilon' leyendo boundary_conditions.json desde `root_temp_dir`
    y escribiéndolo en `epsilon_output_path`.

    Pasos:
      1) root_temp_dir (str): Carpeta donde se ubica boundary_conditions.json (p.ej. "temp").
      2) Se localiza el JSON y se extrae "boundaryConditions".
      3) Se determina un valor de internalField (epsilonInternalValue), por defecto 200.0 si no está definido.
      4) Para cada frontera con 'epsilonType' no vacío, se genera la sección respectiva:
         - inlet  => type=epsilonType, intensity=epsilonIntensity, value=epsilonValue
         - outlet => type=inletOutlet, inletValue=..., value=...
         - wall   => epsilonWallFunction, value=...
         - resto  => fallback genérico
      5) Se escribe el archivo 'epsilon' en `epsilon_output_path`.
    """

    logging.debug("[generate_epsilon_file] Iniciando generación de 'epsilon'.")

    # 1) Validar parámetros
    if not isinstance(root_temp_dir, str):
        logging.error(f"[generate_epsilon_file] 'root_temp_dir' debe ser str, recibido {type(root_temp_dir)}. Abortando.")
        return
    if not isinstance(epsilon_output_path, str):
        logging.error(f"[generate_epsilon_file] 'epsilon_output_path' debe ser str, recibido {type(epsilon_output_path)}. Abortando.")
        return

    bc_json_path = os.path.join(root_temp_dir, "boundary_conditions.json")
    bc_json_path = os.path.normpath(bc_json_path)
    if not os.path.exists(bc_json_path):
        logging.error(f"[generate_epsilon_file] No se encontró '{bc_json_path}'. Abortando 'epsilon'.")
        return

    # 2) Leer boundary_conditions.json
    try:
        with open(bc_json_path, "r", encoding="utf-8") as f:
            bc_data = json.load(f)
        logging.info(f"[generate_epsilon_file] Cargado '{bc_json_path}' exitosamente.")
    except Exception as e:
        logging.error(f"[generate_epsilon_file] Error al leer '{bc_json_path}': {e}")
        return

    # 3) Extraer boundaryConditions
    boundary_dict = bc_data.get("boundaryConditions", {})
    if not isinstance(boundary_dict, dict):
        logging.error("[generate_epsilon_file] 'boundaryConditions' no es un dict. No se genera 'epsilon'.")
        return

    # 4) Determinar el internalField
    epsilon_internal_value = bc_data.get("epsilonInternalValue", 200.0)
    logging.debug(f"[generate_epsilon_file] internalField = {epsilon_internal_value}")

    # Cabecera
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
    object      epsilon;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -3 0 0 0 0];

internalField   uniform {epsilon_internal_value};

boundaryField
{{
"""

    boundary_entries = []

    # 5) Para cada frontera
    for name, bc_info in boundary_dict.items():
        raw_epsilon_type = bc_info.get("epsilonType", None)
        if not (isinstance(raw_epsilon_type, str) and raw_epsilon_type.strip()):
            logging.debug(f"[generate_epsilon_file] Frontera '{name}' sin 'epsilonType' válido. Omitido.")
            continue

        btype = bc_info.get("type", "").lower()
        epsilon_type  = raw_epsilon_type.strip()
        epsilon_value = bc_info.get("epsilonValue", 200.0)
        if epsilon_value is None:
            epsilon_value = 200.0

        logging.debug(f"[generate_epsilon_file] Generando seccion para '{name}' -> btype={btype}, epsilonType={epsilon_type}, epsilonValue={epsilon_value}")
        entry = f"    {name}\n    {{\n"

        if btype == "inlet":
            intensity = bc_info.get("epsilonIntensity", 0.05)
            entry += f"        type            {epsilon_type};\n"
            entry += f"        intensity       {intensity};\n"
            entry += f"        value           uniform {epsilon_value};\n"
        elif btype == "outlet":
            entry += f"        type            inletOutlet;\n"
            entry += f"        inletValue      uniform {epsilon_value};\n"
            entry += f"        value           uniform {epsilon_value};\n"
        elif btype == "wall":
            entry += f"        type            epsilonWallFunction;\n"
            entry += f"        value           uniform {epsilon_value};\n"
        else:
            # Caso genérico
            entry += f"        type            {epsilon_type};\n"
            entry += f"        value           uniform {epsilon_value};\n"

        entry += "    }\n\n"
        boundary_entries.append(entry)

    # 6) Footer
    footer = """}

// ************************************************************************* //
"""

    epsilon_content = header + "".join(boundary_entries) + footer

    # 7) Asegurar carpeta de salida
    out_dir = os.path.dirname(epsilon_output_path)
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception as e:
        logging.error(f"[generate_epsilon_file] No se pudo crear carpeta '{out_dir}': {e}")
        return

    # 8) Escribir el archivo
    try:
        with open(epsilon_output_path, "w", encoding="utf-8") as f:
            f.write(epsilon_content)
        logging.info(f"[generate_epsilon_file] Archivo 'epsilon' escrito en '{epsilon_output_path}'.")
        #logging.debug(f"Contenido final 'epsilon':\n{epsilon_content}")
    except Exception as e:
        logging.error(f"[generate_epsilon_file] Error al escribir '{epsilon_output_path}': {e}")
        return

    logging.info("[generate_epsilon_file] Finalizó sin errores.")
