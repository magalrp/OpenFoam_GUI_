# ui/conf/constant/conf_combustion.py
"""
Módulo para generar el archivo combustionProperties para OpenFOAM
según la configuración de combustión definida en constant.json o case_config.

El archivo se generará solo si la combustión está activa, es decir, si en
especies_options la clave "modelo" es "combustionSinPremezcla" o "combustionPremezclada".
Si la combustión no está activa y existe el archivo, éste se eliminará.

Ejemplo de archivo:
-----------------------------------------------
/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                 |
| \      /  Field         | OpenFOAM: The Open Source CFD Toolbox           |
|  \    /   Operation     | Version:  v2406                                 |
|   \  /    And           | Website:  www.openfoam.com                      |
|    \/     Manipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      combustionProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

combustionModel PaSR;

active          yes;

PaSRCoeffs
{
    Cmix                1.0;
}

// ************************************************************************* //
-----------------------------------------------
"""

def generate_combustionProperties(case_config, output_file):
    # Extraer la configuración de combustión de especies_options
    especies_options = case_config.get("especies_options", {})
    modelo = especies_options.get("modelo", "None")
    # Sólo se genera el archivo si el modelo es de combustión activo
    if modelo not in ["combustionSinPremezcla", "combustionPremezclada"]:
        return  # No se genera el archivo
    
    # Para este ejemplo, usamos el modelo PaSR para la combustión
    combustion_model = "PaSR"
    active = "yes"  # Se asume que la combustión está activa
    cp = especies_options.get("combustionParams", {})
    try:
        Cmix = float(cp.get("Cmix", 1.0))
    except (ValueError, TypeError):
        Cmix = 1.0

    header = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  Field         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   Operation     | Version:  v2406                                 |
|   \\  /    And           | Website:  www.openfoam.com                      |
|    \\/     Manipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      combustionProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
"""
    content = f"""{header}
combustionModel {combustion_model};

active          {active};

PaSRCoeffs
{{
    Cmix                {Cmix};
}}

// ************************************************************************* //
"""
    with open(output_file, "w") as f:
        f.write(content)

if __name__ == "__main__":
    # Ejemplo de uso
    example_config = {
        "especiesActive": True,
        "especies_options": {
            "chemSolver": "ODE",
            "chemSolverParams": {
                "initial_time": 1e-07,
                "ode_solver": "seulex",
                "eps": 0.05
            },
            "modelo": "combustionSinPremezcla",
            "combustionParams": {
                "Cmix": 1.0,
                "A": 4.0,
                "B": 0.5,
                "ZFen": 0.2,
                "tauRes": 0.01,
                "reactionRateFactor": 1.0
            }
        }
    }
    import os
    output = os.path.abspath("combustionProperties")
    generate_combustionProperties(example_config, output)
