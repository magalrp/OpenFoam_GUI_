# ui/conf/constant/conf_g.py
"""
Módulo para generar el archivo 'g' en el directorio constant de OpenFOAM,
según la configuración de gravedad definida en constant.json o case_config.

Se utiliza el vector definido en "gravity_vector" y se normaliza para que su módulo sea 9.81.
Si la gravedad no está activa, se escribe un vector cero.
"""

import os
import math

def generate_g_file(case_config, output_file):
    # Verificar si la gravedad está activa
    if not case_config.get("gravity_active", False):
        g_vector = [0.0, 0.0, 0.0]
    else:
        vec = case_config.get("gravity_vector", [0.0, 0.0, -1.0])
        norm = math.sqrt(sum(x**2 for x in vec))
        if norm == 0:
            unit_vec = [0.0, 0.0, -1.0]
        else:
            unit_vec = [x / norm for x in vec]
        g_value = 9.81
        g_vector = [round(unit_vec[i] * g_value, 6) for i in range(3)]
    
    content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  Field         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   Operation     | Version:  v2406                                 |
|   \\  /    And           | Website:  www.openfoam.com                      |
|    \\/     Manipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       uniformDimensionedVectorField;
    object      g;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 1 -2 0 0 0 0];
value           ({g_vector[0]} {g_vector[1]} {g_vector[2]});


// ************************************************************************* //
"""
    with open(output_file, "w") as f:
        f.write(content)
