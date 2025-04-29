# ui/conf/constant/conf_chem.py
"""
Módulo para generar el archivo chemistryProperties para OpenFOAM
según la configuración de química definida en constant.json o case_config.

El archivo se generará con la siguiente estructura:

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
    object      chemistryProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

chemistryType
{
    solver            ode;
}

chemistry       on;

initialChemicalTimeStep 1.0e-07;

odeCoeffs
{
    solver          seulex;
    eps             0.05;
}

// ************************************************************************* //

Si la química no está activa, se escribirá 'chemistry off'.
"""

def generate_chemistryProperties(case_config, output_file):
    # Verificar si la química está activa (se asume que 'especiesActive' indica la activación)
    chemistry_active = case_config.get("especiesActive", False)
    if not chemistry_active:
        chemistry_status = "off"
        chemistry_type_block = "chemistryType\n{\n    solver            none;\n}"
        initial_time_step = ""
        ode_coeffs = ""
    else:
        chemistry_status = "on"
        # Se extraen las opciones de química del case_config (sección "especies_options")
        especies_options = case_config.get("especies_options", {})
        chem_solver = str(especies_options.get("chemSolver", "ode")).lower()
        chemistry_type_block = f"chemistryType\n{{\n    solver            {chem_solver};\n}}"
        chem_params = especies_options.get("chemSolverParams", {})
        # Usar la variable "initial_time" definida dentro de chemSolverParams
        try:
            initial_time = float(chem_params.get("initial_time", 1e-07))
        except (ValueError, TypeError):
            initial_time = 1e-07
        # Formatear el tiempo químico en notación científica con 1 dígito decimal
        initial_time_step = f"initialChemicalTimeStep {initial_time:1.1e};"
        ode_solver = chem_params.get("ode_solver", "seulex")
        try:
            eps = float(chem_params.get("eps", 0.05))
        except (ValueError, TypeError):
            eps = 0.05
        ode_coeffs = (
            "odeCoeffs\n"
            "{\n"
            f"    solver          {ode_solver};\n"
            f"    eps             {eps:1.2e};\n"
            "}"
        )

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
    object      chemistryProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
"""
    content = f"""{header}
{chemistry_type_block}

chemistry       {chemistry_status};

{initial_time_step}

{ode_coeffs}

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
            }
        }
    }
    import os
    output = os.path.abspath("chemistryProperties")
    generate_chemistryProperties(example_config, output)
