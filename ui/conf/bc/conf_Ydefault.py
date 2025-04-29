# ui/conf/bc/conf_Ydefault.py

import os
import logging

def generate_ydefault_file(boundary_conditions, target_dir):
    """
    Genera el archivo 'Ydefault' en 'target_dir', iterando sobre las fronteras definidas
    en boundary_conditions. El valor y type se establecen en 0 y uno de:
      - zeroGradient (para 'wall' o contornos desconocidos)
      - fixedValue (para 'inlet')
      - inletOutlet (para 'outlet')
    """
    logging.info("Iniciando generación del archivo 'Ydefault'.")

    ydefault_file_path = os.path.join(target_dir, "Ydefault")
    os.makedirs(target_dir, exist_ok=True)

    # Construir el texto de boundaryField según las fronteras
    boundary_entries = ""

    for bc_name, bc_data in boundary_conditions.items():
        btype = bc_data.get("type", "").lower()

        # Ajuste de type y valor
        if btype == "wall":
            boundary_entries += f"""
    {bc_name}
    {{
        type            zeroGradient;
    }}
"""
        elif btype == "inlet":
            boundary_entries += f"""
    {bc_name}
    {{
        type            fixedValue;
        value           uniform 0;
    }}
"""
        elif btype == "outlet":
            boundary_entries += f"""
    {bc_name}
    {{
        type            inletOutlet;
        inletValue      uniform 0;
        value           uniform 0;
    }}
"""
        else:
            # Cualquier otro => zeroGradient
            boundary_entries += f"""
    {bc_name}
    {{
        type            zeroGradient;
    }}
"""

    # Construir contenido final
    ydefault_content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
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
    object      Ydefault;
}}
// ************************************************************************* //

dimensions          [0 0 0 0 0 0 0];

internalField       uniform 0;

boundaryField
{{{boundary_entries}
}}

// ************************************************************************* //
"""

    # Escribir el archivo
    try:
        with open(ydefault_file_path, "w", encoding="utf-8") as f:
            f.write(ydefault_content)
        logging.info(f"Archivo 'Ydefault' generado con éxito en {ydefault_file_path}.")
    except Exception as e:
        logging.error(f"Error al generar 'Ydefault': {e}")
        raise e
