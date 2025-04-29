# ui/conf/bc/conf_alphat.py

import os
import logging

def generate_alphat_file(boundary_conditions, alpha_file_path, calculationType):
    """
    Genera el archivo 'alphat' basado en las condiciones de contorno y la configuración del solver.

    Args:
        boundary_conditions (dict): Diccionario de condiciones de contorno.
        alpha_file_path (str): Ruta completa al archivo 'alphat' a generar.
        calculationType (str): Tipo de cálculo ('Compresible' o 'Incompresible').
    """
    # Determinar si el cálculo es compresible
    compressible = calculationType.lower() == 'compresible'

    # Inicializar el contenido del archivo 'alphat'
    alphat_content = """/*--------------------------------*- C++ -*----------------------------------*\\
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
    object      alphat;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [1 -1 -1 0 0 0 0];

internalField   uniform 0;

boundaryField
{
"""

    # Iterar sobre todas las condiciones de contorno
    for bc_name, bc in boundary_conditions.items():
        bc_type = bc.get('type', '').lower()

        # Bloque para cada condición de contorno
        alphat_content += f"    {bc_name}\n    {{\n"

        if bc_type in ['inlet', 'outlet']:
            # Para condiciones de entrada y salida, el tipo siempre es 'calculated'
            alphat_content += f"        type            calculated;\n"
            alphat_content += f"        value           uniform 0;\n"
        elif bc_type == 'wall':
            # Para condiciones de pared, determinar el tipo basado en 'calculationType' y 'alphaType'
            alphaType = bc.get('alphaType', 'fixedValue')
            alphaValue = bc.get('alphaValue', 1.0)  # Valor por defecto si 'alphaValue' no está definido

            if compressible and alphaType == 'alphatWallFunction':
                wall_type = 'compressible::alphatWallFunction'
            elif alphaType == 'fixedValue':
                wall_type = 'fixedValue'
            else:
                # Manejar otros tipos de alphaType si es necesario
                wall_type = 'fixedValue'  # Valor por defecto

            # Asignar el tipo y Prt
            alphat_content += f"        type            {wall_type};\n"
            alphat_content += f"        Prt             {alphaValue};\n"
            alphat_content += f"        value           uniform 0;\n"
        else:
            # Manejar otros tipos de condiciones de contorno si es necesario
            alphat_content += f"        type            calculated;\n"
            alphat_content += f"        value           uniform 0;\n"

        alphat_content += f"    }}\n\n"

    # Cerrar el bloque boundaryField
    alphat_content += "}\n\n// ************************************************************************* //\n"

    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(alpha_file_path), exist_ok=True)

    # Escribir el contenido en el archivo 'alphat'
    try:
        with open(alpha_file_path, "w", encoding='utf-8') as f:
            f.write(alphat_content)
        logging.info(f"Archivo 'alphat' generado exitosamente en {alpha_file_path}.")
    except Exception as e:
        logging.error(f"Error al generar el archivo 'alphat': {e}")
        raise e  # Re-lanzar la excepción para manejarla externamente si es necesario
