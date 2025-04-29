# ui/conf/bc/conf_nut.py

import os
import logging

def generate_nut_file(boundary_conditions, nut_file_path):
    """
    Genera el archivo 'nut' basado en las condiciones de contorno.

    Args:
        boundary_conditions (dict): Diccionario de condiciones de contorno.
        nut_file_path (str): Ruta completa al archivo 'nut' a generar.
    """
    # Inicializar el contenido del archivo 'nut'
    nut_content = """/*--------------------------------*- C++ -*----------------------------------*\\
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
    class       volScalarField;
    object      nut;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -1 0 0 0 0];

internalField   uniform 0;

boundaryField
{
"""

    # Iterar sobre todas las condiciones de contorno
    for bc_name, bc in boundary_conditions.items():
        bc_type = bc.get('type', '').lower()

        # Bloque para cada condición de contorno
        nut_content += f"    {bc_name}\n    {{\n"

        if bc_type in ['inlet', 'outlet']:
            # Para condiciones de entrada y salida, el tipo siempre es 'calculated'
            nut_content += f"        type            calculated;\n"
            nut_content += f"        value           uniform 0;\n"
        elif bc_type == 'wall':
            # Para condiciones de pared, establecer tipo y parámetros de turbulencia
            # Obtener las variables Cmu, kappa y E desde la condición de contorno
            Cmu = bc.get('Cmu', 0.09)      # Valor por defecto: 0.09
            kappa = bc.get('kappa', 0.41)  # Valor por defecto: 0.41
            E = bc.get('E', 9.8)           # Valor por defecto: 9.8

            nut_content += f"        type            nutkWallFunction;\n"
            nut_content += f"        Cmu             {Cmu};\n"
            nut_content += f"        kappa           {kappa};\n"
            nut_content += f"        E               {E};\n"
            nut_content += f"        value           uniform 0;\n"
        else:
            # Manejar otros tipos de condiciones de contorno si es necesario
            nut_content += f"        type            calculated;\n"
            nut_content += f"        value           uniform 0;\n"

        nut_content += f"    }}\n\n"

    # Cerrar el bloque boundaryField
    nut_content += "}\n\n// ************************************************************************* //\n"

    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(nut_file_path), exist_ok=True)

    # Escribir el contenido en el archivo 'nut'
    try:
        with open(nut_file_path, "w", encoding='utf-8') as f:
            f.write(nut_content)
        logging.info(f"Archivo 'nut' generado exitosamente en {nut_file_path}.")
    except Exception as e:
        logging.error(f"Error al generar el archivo 'nut': {e}")
        raise e  # Re-lanzar la excepción para manejarla externamente si es necesario
