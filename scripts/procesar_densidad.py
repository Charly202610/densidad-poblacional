"""
Procesa la serie nacional de densidad poblacional de Argentina.

Entrada : datos_crudos/densidad_pais.csv
Salida  : datos_procesados/densidad_pais_anual.csv

Pasos:
  - La superficie es constante en la serie del Banco Mundial: se completa
    en los anios que vienen vacios (1960 y 2025).
  - La densidad vacia se calcula como poblacion_total / superficie_km2
    y se marca en fuente_densidad ("banco_mundial" o "calculada").
  - Se agregan la variacion anual de poblacion y de densidad (%).
Todo redondeado a 2 decimales.
"""

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "datos_crudos" / "densidad_pais.csv"
SALIDA = RAIZ / "datos_procesados" / "densidad_pais_anual.csv"


def main():
    df = pd.read_csv(ENTRADA).sort_values("anio").reset_index(drop=True)

    # Superficie: debe ser un unico valor; se completa donde falta
    valores_superficie = df["superficie_km2"].dropna().unique()
    if len(valores_superficie) != 1:
        raise ValueError(
            f"La superficie no es constante: {valores_superficie}. "
            "Revisar antes de completar."
        )
    df["superficie_km2"] = valores_superficie[0]

    # Densidad: oficial si existe, calculada si falta
    df["fuente_densidad"] = df["densidad_hab_km2"].apply(
        lambda v: "calculada" if pd.isna(v) else "banco_mundial"
    )
    calculada = df["poblacion_total"] / df["superficie_km2"]
    df["densidad_hab_km2"] = df["densidad_hab_km2"].fillna(calculada)

    # Variaciones anuales en %
    df["variacion_poblacion_pct"] = df["poblacion_total"].pct_change() * 100
    df["variacion_densidad_pct"] = df["densidad_hab_km2"].pct_change() * 100

    df["poblacion_total"] = df["poblacion_total"].astype("int64")
    df = df.round(2)

    columnas = [
        "anio",
        "poblacion_total",
        "superficie_km2",
        "densidad_hab_km2",
        "fuente_densidad",
        "variacion_poblacion_pct",
        "variacion_densidad_pct",
    ]
    df = df[columnas]

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SALIDA, index=False)

    print(f"Guardado: {SALIDA} ({len(df)} filas)")
    print(df.head(3).to_string(index=False))
    print(df.tail(3).to_string(index=False))
    print(
        f"\nDensidad: {df['densidad_hab_km2'].iloc[0]} hab/km2 en {df['anio'].iloc[0]} "
        f"-> {df['densidad_hab_km2'].iloc[-1]} hab/km2 en {df['anio'].iloc[-1]}"
    )


if __name__ == "__main__":
    main()