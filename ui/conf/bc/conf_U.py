# ui/conf/bc/conf_U.py

import os
import json
import logging

def generate_u_file(root_temp_dir, u_output_path):
    """
    Genera el archivo 'U' leyendo la información de boundary_conditions.json en 'root_temp_dir'
    (por ejemplo: "temp") y escribiéndolo en 'u_output_path' (por ejemplo: "temp/DP0/0/U").

    Lógica existente (sin remover funcionalidades):
      - Se analizan las fronteras definidas en boundary_conditions.json
      - Se generan secciones 'inlet', 'outlet', 'wall' según sus variables
        (velocityType, velocityValue, velocityInit, kType, etc.)
      - Para btype desconocido => se asigna 'fixedValue' y (0,0,0).
    """

    logging.debug("[generate_u_file] Iniciando generación del archivo 'U'.")

    # 1) Verificar parámetros
    if not isinstance(root_temp_dir, str):
        logging.error(f"[generate_u_file] 'root_temp_dir' debe ser str, recibido {type(root_temp_dir)}. Abortando.")
        return
    if not isinstance(u_output_path, str):
        logging.error(f"[generate_u_file] 'u_output_path' debe ser str, recibido {type(u_output_path)}. Abortando.")
        return

    # 2) Ruta del boundary_conditions.json
    bc_json_path = os.path.join(root_temp_dir, "boundary_conditions.json")
    bc_json_path = os.path.normpath(bc_json_path)

    if not os.path.exists(bc_json_path):
        logging.error(f"[generate_u_file] No se encontró '{bc_json_path}'. No se generará 'U'.")
        return

    # 3) Leer el JSON
    try:
        with open(bc_json_path, "r", encoding='utf-8') as f:
            bc_data = json.load(f)
        logging.info(f"[generate_u_file] Cargado '{bc_json_path}' exitosamente.")
    except Exception as e:
        logging.error(f"[generate_u_file] Error al leer '{bc_json_path}': {e}")
        return

    # 4) Extraer la sección boundaryConditions
    bc_dict = bc_data.get("boundaryConditions", {})
    if not isinstance(bc_dict, dict):
        logging.error("[generate_u_file] 'boundaryConditions' no es un dict. Abortando 'U'.")
        return

    # 5) Construir el encabezado del archivo 'U'
    header = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2406                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       volVectorField;
    object      U;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 1 -1 0 0 0 0];

internalField   uniform (0 0 0);

boundaryField
{
"""

    boundary_entries = []

    # 6) Recorrer fronteras para generar secciones
    for name, bc in bc_dict.items():
        btype = bc.get("type", "").lower()
        logging.debug(f"[generate_u_file] Procesando frontera '{name}' de tipo '{btype}'")

        entry = f"    {name}\n    {{\n"

        if btype == "inlet":
            velocity_type  = bc.get("velocityType", "fixedValue")
            velocity_value = bc.get("velocityValue", 0.0)
            velocity_init  = bc.get("velocityInit", 0.0)

            logging.debug(f"[generate_u_file] Inlet '{name}': velocityType='{velocity_type}', "
                          f"velocityValue={velocity_value}, velocityInit={velocity_init}")

            entry += f"        type {velocity_type};\n"

            if velocity_type == "flowRateInletVelocity":
                # volumetricFlowRate => velocityValue
                entry += f"        volumetricFlowRate      {velocity_value};\n"
                entry += f"        value uniform ({velocity_init} {velocity_init} {velocity_init});\n"
            elif velocity_type == "fixedValue":
                entry += f"        value uniform ({velocity_init} {velocity_init} {velocity_init});\n"
            else:
                # Caso genérico => 0,0,0
                entry += f"        value uniform (0 0 0);\n"

        elif btype == "outlet":
            # Se usó "kType" en la versión original, pero normalmente para U => "inletOutlet"
            # lo que hacía era: type => k_type ?? => "inletOutlet"
            # Mantengamos la lógica original:
            k_type = bc.get("kType", "inletOutlet")
            logging.debug(f"[generate_u_file] Outlet '{name}': kType='{k_type}'")

            entry += f"        type            {k_type};\n"
            entry += f"        inletValue      uniform (0 0 0);\n"

        elif btype == "wall":
            no_friction = bc.get("noFriction", False)
            wall_type   = "noSlip" if no_friction else "fixedValue"

            logging.debug(f"[generate_u_file] Wall '{name}': noFriction={no_friction}")

            entry += f"        type            {wall_type};\n"
            if not no_friction:
                # Si es fixedValue => value => (0,0,0)
                entry += f"        value           uniform (0 0 0);\n"

        else:
            # btype desconocido => fixedValue => (0,0,0)
            logging.debug(f"[generate_u_file] Tipo desconocido '{btype}' para '{name}'. Usando 'fixedValue' con (0,0,0).")
            entry += f"        type            fixedValue;\n"
            entry += f"        value            uniform (0 0 0);\n"

        entry += f"    }}\n\n"
        boundary_entries.append(entry)

    # 7) Pie del archivo
    footer = """} // Fin de boundaryField

// ************************************************************************* //
"""

    # 8) Combinar contenido final
    u_content = header + "".join(boundary_entries) + footer
    logging.debug(f"[generate_u_file] Contenido final 'U':\n{u_content}")

    # 9) Asegurar carpeta de salida
    out_dir = os.path.dirname(u_output_path)
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception as e:
        logging.error(f"[generate_u_file] No se pudo crear carpeta de salida '{out_dir}': {e}")
        return

    # 10) Escribir en disco
    try:
        with open(u_output_path, "w", encoding='utf-8') as u_file:
            u_file.write(u_content)
        logging.info(f"[generate_u_file] Archivo 'U' escrito exitosamente en {u_output_path}.")
    except Exception as e:
        logging.error(f"[generate_u_file] Error al escribir '{u_output_path}': {e}")
        return

    logging.info("[generate_u_file] Finalizó sin errores.")
