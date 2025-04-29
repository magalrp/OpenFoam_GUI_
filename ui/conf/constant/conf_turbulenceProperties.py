# ui/conf/constant/conf_turbulenceProperties.py
"""
Módulo para generar el archivo turbulenceProperties para OpenFOAM
según la configuración de turbulencia definida en constant.json o case_config.
"""

def generate_turbulenceProperties(turbulence_config, output_file):
    """
    Genera el archivo turbulenceProperties en 'output_file' a partir de la configuración
    en 'turbulence_config'.

    turbulence_config es un diccionario que debe contener:
      - 'turbulenceModel': string con el modelo de turbulencia (por ejemplo, "kEpsilon", "kOmega", "laminar")
      - 'turbulence': "on" o "off"
      - 'printCoeffs': "on" o "off"

    Se escribe:
      - simulationType laminar; en caso de modelo laminar.
      - simulationType RAS; y un bloque RAS { ... } en caso de modelos RANS (RAS).
      - simulationType DNS; en caso de DNS.
      - simulationType LES; y un bloque LES { ... } en caso de LES.
    """
    header = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  Field         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   Operation     |                                                 |
|   \\  /    And           |                                                 |
|    \\/     Manipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      turbulenceProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
"""

    # Extraer el modelo final ya procesado (string)
    model = turbulence_config.get("turbulenceModel", "laminar")
    turbulence_state = turbulence_config.get("turbulence", "off")
    printCoeffs = turbulence_config.get("printCoeffs", "off")

    if model.lower() == "laminar":
        content = f"{header}\nsimulationType  laminar;\n\n// ************************************************************************* //\n"
    elif model.lower() in ["dns"]:
        content = f"{header}\nsimulationType  DNS;\n\n// DNS: todas las escalas se resuelven directamente.\n\n// ************************************************************************* //\n"
    elif model.lower() in ["smagorinsky", "dynsmagorinsky", "oneeqeddy", "dynamickeqn", "wale"]:
        # Para LES, se asume que se deben incluir parámetros LES específicos.
        content = f"""{header}
simulationType  LES;

LES
{{
    LESModel          {model};
    delta             cubeRootVol;
    printCoeffs       {printCoeffs};
}}

 // ************************************************************************* //
"""
    else:
        # Se asume RAS para el resto
        content = f"""{header}
simulationType  RAS;

RAS
{{
    RASModel            {model};
    turbulence          {turbulence_state};
    printCoeffs         {printCoeffs};
}}

// ************************************************************************* //
"""
    with open(output_file, "w") as f:
        f.write(content)
