# ui/conf/constant/conf_reactingCloudproperties.py

import os
import logging

REACTING_CLOUD_TEMPLATE = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  {version}                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      {cloudName}Properties;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

solution
{{
    active          {active};
    coupled         {coupled};
    transient       {transient};
    cellValueSourceCorrection {cellCorr};
    maxCo           {maxCo};

    sourceTerms
    {{
        schemes
        {{
{sourceSchemes}
        }}
    }}

    interpolationSchemes
    {{
{interpolationSchemes}
    }}

    integrationSchemes
    {{
{integrationSchemes}
    }}
}}


constantProperties
{{
    rho0            {rho0};
    T0              {T0};
    Cp0             {Cp0};

    constantVolume  {constV};
}}


subModels
{{
    particleForces
    {{
{particleForces}
    }}

    injectionModels
    {{
{injectionModels}
    }}

    dispersionModel {dispersionModel};
    patchInteractionModel {patchInteractionModel};
    heatTransferModel {heatTransferModel};
    compositionModel {compositionModel};
    phaseChangeModel {phaseChangeModel};
    devolatilisationModel {devolatilisationModel};
    surfaceReactionModel {surfaceReactionModel};
    stochasticCollisionModel {stochasticCollisionModel};
    surfaceFilmModel {surfaceFilmModel};
    radiation       {radiation};

    standardWallInteractionCoeffs
    {{
        type            {stdWallInteraction};
    }}

    RanzMarshallCoeffs
    {{
        BirdCorrection  {birdCorrection};
    }}

    singleMixtureFractionCoeffs
    {{
        phases
        (
            gas    {{}}            
            liquid {{ {liquidPhase} }}   
            solid  {{}}            
        );
        YGasTot0        {YGasTot0};
        YLiquidTot0     {YLiquidTot0};
        YSolidTot0      {YSolidTot0};
    }}

    liquidEvaporationCoeffs
    {{
        enthalpyTransfer {enthalpyTransfer};
        activeLiquids   ( {activeLiquids} );
    }}
}}


cloudFunctions
{{
    particlePostProcessing1
    {{
        type                {cloudFuncType};
        maxStoredParcels    {maxStoredParcels};
        patches             ( {patches} );
    }}
}}


// ************************************************************************* //
"""

def generate_reactingCloudProperties(fase_cfg: dict, main_dir: str):
    """
    Genera (o elimina) reactingCloudProperties en temp/DP0/constant.
    - fase_cfg: dict con la estructura del Disperse_fase.json
    - main_dir: ruta raíz del caso
    """

    # 1) ¿Está activa la fase discreta?
    active_flag = fase_cfg.get("active", 
                   fase_cfg.get("discrete_phase_active", False))
    # nombre de la nube
    cloudName = fase_cfg.get("particleTrackProperties", {}) \
                     .get("cloudName", "reactingCloud1")

    target = os.path.join(main_dir, "temp", "DP0", "constant", f"{cloudName}Properties")

    # Si no está activa, borramos si existe y salimos
    if not active_flag:
        if os.path.exists(target):
            os.remove(target)
            logging.info(f"{cloudName}Properties eliminado en {target} (fase discreta inactiva).")
        return

    # 2) preparamos el directorio
    os.makedirs(os.path.dirname(target), exist_ok=True)

    # 3) sacamos los modelos de fase discreta
    models = fase_cfg.get("discrete_phase_models", {})

    dispersionModel       = models.get("dispersionModel", "none")
    pim                   = models.get("patchInteractionModel", {})
    patchInteractionModel = pim.get("model", pim.get("type", "standardWallInteraction"))
    htm                   = models.get("heatTransferModel", {})
    heatTransferModel     = htm.get("model", "RanzMarshall")
    cm                    = models.get("compositionModel", {})
    compositionModel      = cm.get("model", "singleMixtureFractionCoeffs")
    pcm                   = models.get("phaseChangeModel", {})
    phaseChangeModel      = pcm.get("model", "liquidEvaporationCoeffs")
    devolatilisationModel = models.get("devolatilisationModel", "none")
    surfaceReactionModel  = models.get("surfaceReactionModel", "none")
    stochasticCollisionModel = models.get("stochasticCollisionModel", "none")
    surfaceFilmModel      = models.get("surfaceFilmModel", "none")
    radiation             = models.get("radiation", "none")

    # 4) inyecciones
    injections = fase_cfg.get("injections", [])
    inj_lines = []
    for inj in injections:
        name = inj.get("name", "model1")
        inj_lines.append(f"        {name}")
        inj_lines.append("        {")
        for k,v in inj.get("parameters", {}).items():
            # arrays vs escalars
            val = v
            if isinstance(v, (list, tuple)):
                val = "(" + " ".join(map(str,v)) + ")"
            inj_lines.append(f"            {k:<20}{val};")
        inj_lines.append("        }")
    injectionModels = "\n".join(inj_lines)

    # 5) Otros bloques básicos (pueden salir de models o fijarse por defecto)
    # aquí pongo defaults razonables:
    def fmt_block(entries, indent="        "):
        return "\n".join(f"{indent}{e};" for e in entries)

    # sourceTerms.schemes
    source_cfg = models.get("sourceTermsSchemes", {
        "rho": ("explicit",1), "U":("explicit",1),
        "Yi":("explicit",1),"h":("explicit",1),"radiation":("explicit",1)
    })
    ss_lines = [f"{k:<16}{sch} {fc}" for k,(sch,fc) in source_cfg.items()]
    sourceSchemes = fmt_block(ss_lines, indent="            ")

    # interpolationSchemes
    interp_cfg = models.get("interpolationSchemes", {
        "rho":"cell","U":"cellPoint","thermo:mu":"cell",
        "T":"cell","Cp":"cell","kappa":"cell","p":"cell"
    })
    is_lines = [f"{k:<16}{m}" for k,m in interp_cfg.items()]
    interpolationSchemes = fmt_block(is_lines, indent="            ")

    # integrationSchemes
    integ_cfg = models.get("integrationSchemes", {"U":"Euler","T":"analytical"})
    int_lines = [f"{k:<16}{m}" for k,m in integ_cfg.items()]
    integrationSchemes = fmt_block(int_lines, indent="            ")

    # constantProperties
    ptp = fase_cfg.get("particleTrackProperties", {})
    rho0   = ptp.get("rho0", 422.6)
    T0     = ptp.get("T0", 350)
    Cp0    = ptp.get("Cp0", 2200)
    constV = "true" if ptp.get("constantVolume", False) else "false"

    # particleForces
    pf = models.get("particleForces", ["sphereDrag","gravity"])
    particleForces = fmt_block(pf, indent="            ")

    # singleMixtureFractionCoeffs: si hay detalles en models["compositionModel"]
    smf = cm.get("speciesType", {})
    liquidPhase = " ".join(f"{sp} {v}" for sp,v in smf.items())
    YGasTot0    = cm.get("YGasTot0",0)
    YLiquidTot0 = cm.get("YLiquidTot0",1)
    YSolidTot0  = cm.get("YSolidTot0",0)

    # liquidEvaporationCoeffs
    lec = pcm.get("activeLiquids", [])
    enthalpyTransfer = pcm.get("enthalpyTransfer","enthalpyDifference")
    activeLiquids    = " ".join(lec)

    # cloudFunctions
    cf = fase_cfg.get("particleTrackProperties", {})
    cloudFuncType     = cf.get("cloudFunctionType","particlePostProcessing")
    maxStoredParcels  = cf.get("maxStoredParcels",100)
    patches           = " ".join(cf.get("patches",[]))

    # 6) ensamblamos el contenido
    content = REACTING_CLOUD_TEMPLATE.format(
        version                  = fase_cfg.get("version","v2406"),
        cloudName                = cloudName,
        active                   = "true" if active_flag else "false",
        coupled                  = "true",
        transient                = "yes",
        cellCorr                 = "on",
        maxCo                    = models.get("maxCo",0.3),
        sourceSchemes            = sourceSchemes,
        interpolationSchemes     = interpolationSchemes,
        integrationSchemes       = integrationSchemes,
        rho0                     = rho0, T0=T0, Cp0=Cp0, constV=constV,
        particleForces           = particleForces,
        injectionModels          = injectionModels,
        dispersionModel          = dispersionModel,
        patchInteractionModel    = patchInteractionModel,
        heatTransferModel        = heatTransferModel,
        compositionModel         = compositionModel,
        phaseChangeModel         = phaseChangeModel,
        devolatilisationModel    = devolatilisationModel,
        surfaceReactionModel     = surfaceReactionModel,
        stochasticCollisionModel = stochasticCollisionModel,
        surfaceFilmModel         = surfaceFilmModel,
        radiation                = radiation,
        stdWallInteraction       = models.get("patchInteractionModel",{}).get("type","rebound"),
        birdCorrection           = models.get("heatTransferModel",{}).get("BirdCorrection","off"),
        liquidPhase              = liquidPhase,
        YGasTot0                 = YGasTot0,
        YLiquidTot0              = YLiquidTot0,
        YSolidTot0               = YSolidTot0,
        enthalpyTransfer         = enthalpyTransfer,
        activeLiquids            = activeLiquids,
        cloudFuncType            = cloudFuncType,
        maxStoredParcels         = maxStoredParcels,
        patches                  = patches
    )

    # 7) escribimos el archivo
    try:
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        logging.info(f"{cloudName}Properties generado en: {target}")
    except Exception as e:
        logging.error(f"Error al escribir {cloudName}Properties: {e}")
        raise
