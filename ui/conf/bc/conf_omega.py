# ui/conf/bc/conf_omega.py

import os
import json
import logging

def generate_omega_file(root_temp_dir, omega_output_path):
    """
    Genera el archivo 'omega' leyendo boundary_conditions.json desde `root_temp_dir`
    y escribiéndolo en `omega_output_path`.

    1. Abre boundary_conditions.json en `root_temp_dir`.
    2. Determina un omegaInternalValue (por defecto 4.5e-3).
    3. Para cada frontera que tenga un 'omegaType' válido (str no vacío):
       - Si btype='wall' y omegaType='omegaWallFunction', escribe con Cmu, kappa, E...
       - Si es inlet => type=omegaType, mixingLength=..., etc.
       - Si es outlet => type=inletOutlet...
       - Resto => se ignora/usa valor por defecto.
    """

    logging.debug("[generate_omega_file] Iniciando...")

    # 1) Verificar que root_temp_dir sea una ruta válida
    if not isinstance(root_temp_dir, str):
        logging.error(f"[generate_omega_file] 'root_temp_dir' debe ser str, no {type(root_temp_dir)}. Cancelado.")
        return

    # 2) Localizar boundary_conditions.json
    bc_json_path = os.path.join(root_temp_dir, "boundary_conditions.json")
    bc_json_path = os.path.normpath(bc_json_path)
    if not os.path.exists(bc_json_path):
        logging.error(f"[generate_omega_file] No se encontró '{bc_json_path}'. Abortando 'omega'.")
        return

    # 3) Cargar boundary_conditions.json
    try:
        with open(bc_json_path, "r", encoding='utf-8') as f:
            bc_data = json.load(f)
        logging.info(f"[generate_omega_file] Cargado '{bc_json_path}' exitosamente.")
    except Exception as e:
        logging.error(f"[generate_omega_file] Error al leer '{bc_json_path}': {e}")
        return

    # 4) boundaryConditions
    boundary_dict = bc_data.get("boundaryConditions", {})
    if not isinstance(boundary_dict, dict):
        logging.error("[generate_omega_file] 'boundaryConditions' no es un dict. No se genera 'omega'.")
        return

    # 5) Determinar el internalField
    #    Por defecto 4.5e-3; si existiera un "omegaInternalValue" en el JSON, tomarlo
    default_omega_val = 4.5e-3
    chosen_internal = bc_data.get("omegaInternalValue", default_omega_val)
    logging.debug(f"[generate_omega_file] Usando internalField={chosen_internal}")

    # 6) Encabezado
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
    object      omega;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 0 -1 0 0 0 0];

internalField   uniform {chosen_internal};

boundaryField
{{
"""

    boundary_entries = []

    # 7) Recorrer cada frontera
    for bc_name, info in boundary_dict.items():
        # Revisar si hay un omegaType (str no vacío)
        raw_omega_type = info.get("omegaType", "")
        if not (isinstance(raw_omega_type, str) and raw_omega_type.strip()):
            logging.debug(f"[generate_omega_file] Frontera '{bc_name}': 'omegaType' ausente o no válido. Se omite.")
            continue
        omega_type = raw_omega_type.strip()

        btype = info.get("type", "").lower()
        local_omega_val = info.get("omegaValue", chosen_internal)
        if local_omega_val is None:
            local_omega_val = chosen_internal

        entry = f"    {bc_name}\n    {{\n"
        logging.debug(f"[generate_omega_file] Procesando '{bc_name}' (type='{btype}', omegaType='{omega_type}')")

        if btype == "wall":
            if omega_type == "omegaWallFunction":
                cmu   = info.get("Cmu", 0.09)
                kappa = info.get("kappa", 0.41)
                e_val = info.get("E", 9.8)
                val_opt = info.get("omegaValueOption", "$internalField")

                entry += f"        type            {omega_type};\n"
                entry += f"        Cmu             {cmu};\n"
                entry += f"        kappa           {kappa};\n"
                entry += f"        E               {e_val};\n"
                entry += f"        value           {val_opt};\n"
            else:
                # fixedValue, etc.
                entry += f"        type            {omega_type};\n"
                entry += f"        value           uniform {local_omega_val};\n"

        elif btype == "inlet":
            # Ej. "turbulentMixingLengthFrequencyInlet"
            mixing_len = info.get("omegaMixingLength", 0.007)
            entry += f"        type            {omega_type};\n"
            entry += f"        mixingLength    {mixing_len};\n"
            entry += f"        k               k;\n"
            entry += f"        value           uniform {local_omega_val};\n"

        elif btype == "outlet":
            entry += f"        type            inletOutlet;\n"
            entry += f"        inletValue      uniform {local_omega_val};\n"

        else:
            # Caso "desconocido" => se escribe algo genérico
            entry += f"        type            {omega_type};\n"
            entry += f"        value           uniform {local_omega_val};\n"

        entry += "    }\n\n"
        boundary_entries.append(entry)

    # 8) Footer
    footer = """}

// ************************************************************************* //
"""

    # 9) Combinar
    omega_content = header + "".join(boundary_entries) + footer

    # 10) Asegurar carpeta
    out_dir = os.path.dirname(omega_output_path)
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception as e:
        logging.error(f"[generate_omega_file] Error creando carpeta '{out_dir}': {e}")
        return

    # 11) Escribir el archivo
    try:
        with open(omega_output_path, "w", encoding="utf-8") as f:
            f.write(omega_content)
        logging.info(f"[generate_omega_file] Archivo 'omega' escrito en '{omega_output_path}'.")
        # logging.debug(f"Contenido final 'omega':\n{omega_content}")
    except Exception as e:
        logging.error(f"[generate_omega_file] Error al escribir '{omega_output_path}': {e}")

    logging.info("[generate_omega_file] Finalizó sin errores.")
