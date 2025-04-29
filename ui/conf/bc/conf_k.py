# ui/conf/bc/conf_k.py

import os
import json
import logging

def generate_k_file(root_temp_dir, k_output_path):
    """
    Genera el archivo 'k' tomando datos desde `root_temp_dir`/boundary_conditions.json
    y escribiéndolo en k_output_path (ej: .../temp/DP0/0/k).

    1. Abre boundary_conditions.json en `root_temp_dir`.
    2. Determina el internalField como la kIntensity de la primera frontera inlet (si existe),
       o un valor por defecto (3.75e-9).
    3. Para cada frontera:
       - Inlet =>   type = kType, intensity = kIntensity, value = kValue
       - Outlet =>  type = kType, inletValue = kValue
       - Wall =>    type = omegaType, value = (omegaValue o 0)
       - Otros =>   se ignoran
    """

    logging.debug("[generate_k_file] Iniciando generación de 'k'...")

    # 1) Verificar root_temp_dir existe
    if not isinstance(root_temp_dir, str):
        logging.error(f"[generate_k_file] 'root_temp_dir' debe ser str, no {type(root_temp_dir)}. Cancelado.")
        return

    bc_json_path = os.path.join(root_temp_dir, "boundary_conditions.json")
    bc_json_path = os.path.normpath(bc_json_path)

    if not os.path.exists(bc_json_path):
        logging.error(f"[generate_k_file] No se encontró '{bc_json_path}'. No se genera 'k'.")
        return

    # 2) Leer boundary_conditions.json
    try:
        with open(bc_json_path, "r", encoding="utf-8") as f:
            bc_data = json.load(f)
        logging.info(f"[generate_k_file] Cargado '{bc_json_path}' exitosamente.")
    except Exception as e:
        logging.error(f"[generate_k_file] Error al leer '{bc_json_path}': {e}")
        return

    # 3) boundaryConditions
    boundary_dict = bc_data.get("boundaryConditions", {})
    if not isinstance(boundary_dict, dict):
        logging.error("[generate_k_file] 'boundaryConditions' no es un dict. Abortando k.")
        return

    default_if_not_found = 3.75e-9
    chosen_internal = default_if_not_found

    # 4) Buscar la primera frontera inlet con kIntensity
    for name, info in boundary_dict.items():
        if info.get("type", "").lower() == "inlet":
            if "kIntensity" in info:
                chosen_internal = info["kIntensity"]
                logging.debug(f"[generate_k_file] Usando kIntensity={chosen_internal} de '{name}' como internalField.")
                break
    else:
        logging.debug(f"[generate_k_file] No se encontró inlet con kIntensity, usando {default_if_not_found}.")

    # 5) Encabezado
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
    object      k;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform {chosen_internal};

boundaryField
{{
"""

    boundary_entries = []

    # 6) Construir boundaryField
    for bc_name, info in boundary_dict.items():
        btype = info.get("type", "").lower()

        if btype == "inlet":
            # kType, kIntensity, kValue
            k_type = info.get("kType", "turbulentIntensityKineticEnergyInlet")
            k_intensity = info.get("kIntensity", 0.16)
            k_value = info.get("kValue", chosen_internal)

            entry = f"""
    {bc_name}
    {{
        type            {k_type};
        intensity       {k_intensity};
        value           uniform {k_value};
    }}
"""
            boundary_entries.append(entry)

        elif btype == "outlet":
            # kType, kValue
            k_type = info.get("kType", "inletOutlet")
            k_value = info.get("kValue", chosen_internal)

            entry = f"""
    {bc_name}
    {{
        type            {k_type};
        inletValue      uniform {k_value};
    }}
"""
            boundary_entries.append(entry)

        elif btype == "wall":
            # Se dijo usar "omegaType" y "omegaValue" para la 'wall' => un
            # "kqRWallFunction" => value=0 ??? 
            # O se mantiene la convención inicial:
            #   type => "omegaType"    (opcional)
            #   value => "omegaValue" o 0
            # Siguiendo el enunciado: "El type se selecciona de la variable omegaType"
            #   "en caso de que omegaValue sea null => 0"
            # => Si esto no aplica a 'k', adaptarlo si se desea "kqRWallFunction"
            #   y "value => uniform 0".
            # O si quieres reusar kType => "kqRWallFunction"
            # Lo pongo tal y como pediste en la descripción.
            kqrf_type = info.get("omegaType", "kqRWallFunction")  # Or "kqRWallFunction"
            raw_val = info.get("omegaValue", 0)
            if raw_val is None:
                raw_val = 0

            entry = f"""
    {bc_name}
    {{
        type            {kqrf_type};
        value           uniform {raw_val};
    }}
"""
            boundary_entries.append(entry)
        else:
            logging.debug(f"[generate_k_file] Se ignora '{bc_name}' de tipo '{btype}' en 'k'.")

    # 7) Pie
    footer = """
}

// ************************************************************************* //
"""

    k_content = header + "".join(boundary_entries) + footer

    # 8) Asegurar directorio de salida
    out_dir = os.path.dirname(k_output_path)
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception as e:
        logging.error(f"[generate_k_file] Error creando carpeta '{out_dir}': {e}")
        return

    # 9) Escribir el archivo
    try:
        with open(k_output_path, "w", encoding="utf-8") as f:
            f.write(k_content)
        logging.info(f"[generate_k_file] Archivo 'k' escrito en '{k_output_path}'.")
        # logging.debug(f"Contenido final de 'k':\n{k_content}")
    except Exception as e:
        logging.error(f"[generate_k_file] Error al escribir '{k_output_path}': {e}")


    logging.info("[generate_k_file] Finalizó sin errores.")
