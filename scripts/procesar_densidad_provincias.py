"""
Arma la serie de densidad poblacional por provincia (24 jurisdicciones) para
los censos 1914, 1947, 1960, 1970, 1980, 1991, 2001, 2010 y 2022.

Entradas (en datos_crudos/):
  - poblacion_provincias_1914_2001.tsv : tabla del Ministerio del Interior
                                         (datos de INDEC), censos 1914 a 2001
  - c2022_tp_est_c1.xlsx               : INDEC, Censo 2022, Cuadro 1 (poblacion 2010 y 2022)
  - c2022_tp_est_c2.xlsx               : INDEC, Censo 2022, Cuadro 2 (superficie)

Salida: datos_procesados/densidad_provincias_censos.csv

Controles que corre el script (si alguno falla, se corta con un error):
  - 1914 a 2001: la suma de las provincias debe dar el total nacional de la tabla.
  - 2010 y 2022: la suma debe dar el total nacional del cuadro 1.
  - Deben quedar exactamente 24 jurisdicciones, todas con superficie.
"""

import csv
from pathlib import Path

import openpyxl
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CRUDOS = RAIZ / "datos_crudos"
SALIDA = RAIZ / "datos_procesados" / "densidad_provincias_censos.csv"

HISTORICA = CRUDOS / "poblacion_provincias_1914_2001.tsv"
CUADRO_1 = CRUDOS / "c2022_tp_est_c1.xlsx"
CUADRO_2 = CRUDOS / "c2022_tp_est_c2.xlsx"

# --- Correcciones a la tabla del Ministerio -------------------------------
# Con la tabla tal cual, los censos de 1947 y 1980 no suman el total nacional.
# Cada valor se corrige con lo que hace falta para que la suma cierre, y se
# verifica que el resultado sea coherente con los censos vecinos:
#   Tucuman 1947: 293.371 -> 593.371 (1914: 332.933 | 1960: 773.972)
#   Resto de BA 1980: 2.922.829 (repetia el valor de CABA) -> 4.022.207
#                     (1970: 3.394.082 | 1991: 4.642.350)
CORRECCIONES = {
    ("Tucumán", 1947): 593371,
    ("Resto de la Provincia de Buenos Aires", 1980): 4022207,
}

# --- Superficie de Tierra del Fuego ---------------------------------------
# La superficie oficial de la provincia incluye la Antartida (964.847 km2) y las
# islas del Atlantico Sur, y deja la densidad en 0,2 hab/km2. Se usa la Isla
# Grande (departamentos Ushuaia y Rio Grande), donde vive casi toda la
# poblacion (INDEC, nota 3 del cuadro 2). Cambiar aca si se prefiere otro criterio.
SUPERFICIE_TDF_KM2 = 21571
NOMBRE_TDF = "Tierra del Fuego"


def numero(texto):
    return int(texto.replace(".", ""))


def leer_historica():
    with open(HISTORICA, encoding="utf-8") as f:
        filas = list(csv.reader(f, delimiter="\t"))
    anios = [int(a) for a in filas[0][1:]]
    datos = {f[0]: [numero(x) for x in f[1:]] for f in filas[1:]}

    for (jurisdiccion, anio), valor in CORRECCIONES.items():
        datos[jurisdiccion][anios.index(anio)] = valor

    total = datos.pop("Total")
    for i, anio in enumerate(anios):
        suma = sum(v[i] for v in datos.values())
        if suma != total[i]:
            raise ValueError(
                f"Censo {anio}: las provincias suman {suma} y el total es {total[i]}."
            )

    # Buenos Aires = GBA + resto de la provincia
    gba = datos.pop("Partidos del Gran Buenos Aires")
    resto = datos.pop("Resto de la Provincia de Buenos Aires")
    datos["Buenos Aires"] = [a + b for a, b in zip(gba, resto)]
    datos[NOMBRE_TDF] = datos.pop("Tierra del Fuego, Antártida e Islas del Atlántico Sur")

    registros = []
    for jurisdiccion, valores in datos.items():
        for anio, poblacion in zip(anios, valores):
            registros.append(
                {
                    "provincia": jurisdiccion,
                    "anio_censo": anio,
                    "poblacion": poblacion,
                    "corregido": (jurisdiccion, anio) in CORRECCIONES
                    or (jurisdiccion == "Buenos Aires" and anio == 1980),
                }
            )
    return pd.DataFrame(registros)


def filas_con_codigo(ruta, hoja):
    libro = openpyxl.load_workbook(ruta, data_only=True)
    nombre_hoja = next(n for n in libro.sheetnames if n.strip() == hoja)
    ws = libro[nombre_hoja]
    todas = list(ws.iter_rows(values_only=True))
    total = next(r for r in todas if r[1] == "Total")
    jurisdicciones = [r for r in todas if r[0] is not None and str(r[0]).strip().isdigit()]
    return total, jurisdicciones


def limpiar_nombre(nombre):
    nombre = " ".join(str(nombre).split())
    if nombre.startswith("Tierra del Fuego"):
        return NOMBRE_TDF
    return nombre


def leer_2010_2022():
    total1, juris1 = filas_con_codigo(CUADRO_1, "Cuadro 1")
    registros = []
    for r in juris1:
        nombre = limpiar_nombre(r[1])
        registros.append({"provincia": nombre, "anio_censo": 2010, "poblacion": int(r[2])})
        registros.append({"provincia": nombre, "anio_censo": 2022, "poblacion": int(r[3])})
    df = pd.DataFrame(registros)
    for anio, columna in ((2010, 2), (2022, 3)):
        suma = df.loc[df["anio_censo"] == anio, "poblacion"].sum()
        if suma != int(total1[columna]):
            raise ValueError(f"Censo {anio}: suma {suma} distinta del total {total1[columna]}.")
    df["corregido"] = False

    _, juris2 = filas_con_codigo(CUADRO_2, "Cuadro 2")
    superficie = {limpiar_nombre(r[1]): float(r[2]) for r in juris2}
    superficie[NOMBRE_TDF] = SUPERFICIE_TDF_KM2
    return df, superficie


def main():
    historica = leer_historica()
    recientes, superficie = leer_2010_2022()

    df = pd.concat([historica, recientes], ignore_index=True)

    faltan = set(df["provincia"]) - set(superficie)
    if faltan:
        raise ValueError(f"Provincias sin superficie: {sorted(faltan)}")
    if df["provincia"].nunique() != 24:
        raise ValueError(f"Se esperaban 24 jurisdicciones y hay {df['provincia'].nunique()}.")

    df["superficie_km2"] = df["provincia"].map(superficie)
    df["densidad_hab_km2"] = df["poblacion"] / df["superficie_km2"]

    df = df.sort_values(["provincia", "anio_censo"]).reset_index(drop=True)
    grupo = df.groupby("provincia")
    anios_entre = grupo["anio_censo"].diff()
    df["variacion_intercensal_pct"] = grupo["poblacion"].pct_change() * 100
    df["tasa_crecimiento_anual_pct"] = (
        (df["poblacion"] / grupo["poblacion"].shift()) ** (1 / anios_entre) - 1
    ) * 100

    df["poblacion"] = df["poblacion"].astype("int64")
    df["corregido"] = df["corregido"].map({True: "si", False: "no"})
    df = df.round(2)[
        [
            "provincia",
            "anio_censo",
            "poblacion",
            "superficie_km2",
            "densidad_hab_km2",
            "variacion_intercensal_pct",
            "tasa_crecimiento_anual_pct",
            "corregido",
        ]
    ]

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SALIDA, index=False)

    print(f"Guardado: {SALIDA} ({len(df)} filas, {df['provincia'].nunique()} provincias)")
    print("Controles de suma: OK (todos los censos cierran con el total nacional)")
    ult = df[df["anio_censo"] == 2022].sort_values("densidad_hab_km2", ascending=False)
    print("\nDensidad 2022, mayores y menores:")
    print(ult[["provincia", "densidad_hab_km2"]].head(3).to_string(index=False))
    print(ult[["provincia", "densidad_hab_km2"]].tail(3).to_string(index=False))


if __name__ == "__main__":
    main()
