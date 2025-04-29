# ui/conf/bc/conf_p_rgh.py

import os
import json
import logging

def generate_p_rgh_file(temp_dir, p_rgh_file_path):
    """
    Genera el archivo 'p_rgh' tomando datos desde boundary_conditions.json (en 'temp_dir')
    y lo escribe en 'p_rgh_file_path'.

    Lógica:
      1) Leer ambientPressure (o 100000 por defecto).
      2) Para cada frontera del JSON:
         - si es 'outlet', type = prghPressure y p = uniform <pressureValue o ambient>
         - si no, type = fixedFluxPressure

    Parametros:
      - temp_dir (str)        : Ruta a la carpeta con boundary_conditions.json (por ejemplo: 'temp')
      - p_rgh_file_path (str) : Ruta donde se escribirá p_rgh (por ejemplo: 'temp/DP0/0/p_rgh').

    Ejemplo de escritura final:
        p_rgh
        {
            internalField ...
            boundaryField
            {
                outlet
                {
                    type        prghPressure;
                    p           uniform <X>;
                }
                inlet
                {
                    type        fixedFluxPressure;
                }
                ...
            }
        }
    """

    logging.debug("[generate_p_rgh_file] Iniciando generación de 'p_rgh'.")

    # 1) Verificar parámetros
    if not isinstance(temp_dir, str):
        logging.error("[generate_p_rgh_file] 'temp_dir' debe ser str. Abortando.")
        return
    if not isinstance(p_rgh_file_path, str):
        logging.error("[generate_p_rgh_file] 'p_rgh_file_path' debe ser str. Abortando.")
        return

    # 2) Ubicar boundary_conditions.json
    bc_json_path = os.path.join(temp_dir, "boundary_conditions.json")
    bc_json_path = os.path.normpath(bc_json_path)

    if not os.path.exists(bc_json_path):
        logging.error(f"[generate_p_rgh_file] No se encontró {bc_json_path}. No se generará 'p_rgh'.")
        return

    # 3) Leer boundary_conditions.json
    try:
        with open(bc_json_path, "r", encoding="utf-8") as f:
            bc_data = json.load(f)
        logging.info(f"[generate_p_rgh_file] Cargado '{bc_json_path}' exitosamente.")
    except Exception as e:
        logging.error(f"[generate_p_rgh_file] Error al leer '{bc_json_path}': {e}")
        return

    # 4) Obtener ambientPressure y boundaryConditions
    boundary_conditions = bc_data.get("boundaryConditions", {})
    ambient_pressure = bc_data.get("ambientPressure", 100000.0)
    logging.debug(f"[generate_p_rgh_file] Presión Ambiente (Pa): {ambient_pressure}")

    # 5) Construir encabezado
    header = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2406                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\//     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      p_rgh;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [1 -1 -2 0 0 0 0];

internalField   uniform {ambient_pressure};

boundaryField
{{
"""

    boundary_entries = []

    # 6) Recorrer cada frontera y armar la sección
    for bc_name, bc_info in boundary_conditions.items():
        btype = bc_info.get("type", "").lower()
        logging.debug(f"[generate_p_rgh_file] Procesando '{bc_name}' (tipo '{btype}') para 'p_rgh'.")

        # Valor de presión a usar en caso de type=outlet => p uniform <X>
        # (si no existe pressureValue, se usa ambient_pressure)
        pressure_value = bc_info.get("pressureValue", ambient_pressure)

        if btype == "outlet":
            entry = f"""
    {bc_name}
    {{
        type            prghPressure;
        p               uniform {pressure_value};
    }}
"""
        else:
            # Para otras fronteras => type = fixedFluxPressure
            entry = f"""
    {bc_name}
    {{
        type            fixedFluxPressure;
    }}
"""

        boundary_entries.append(entry)

    # 7) Pie
    footer = """
}

// ************************************************************************* //
"""

    # 8) Unir contenido
    p_rgh_content = header + "".join(boundary_entries) + footer
    logging.debug("[generate_p_rgh_file] Contenido construido para 'p_rgh':\n" + p_rgh_content)

    # 9) Asegurar directorio de salida
    try:
        os.makedirs(os.path.dirname(p_rgh_file_path), exist_ok=True)
    except Exception as e:
        logging.error(f"[generate_p_rgh_file] No se pudo crear directorio de salida: {e}")
        return

    # 10) Escribir el archivo
    try:
        with open(p_rgh_file_path, "w", encoding="utf-8") as p_rgh_file:
            p_rgh_file.write(p_rgh_content)
        logging.info(f"[generate_p_rgh_file] Archivo 'p_rgh' escrito exitosamente en '{p_rgh_file_path}'.")
    except Exception as e:
        logging.error(f"[generate_p_rgh_file] Error al escribir '{p_rgh_file_path}': {e}")
        return

    logging.info("[generate_p_rgh_file] Finalizó sin errores.")
