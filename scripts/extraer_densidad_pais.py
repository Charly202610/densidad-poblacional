"""
Extrae de la API del Banco Mundial la serie anual de Argentina:
  - EN.POP.DNST  : densidad de poblacion (hab/km2)
  - SP.POP.TOTL  : poblacion total
  - AG.LND.TOTL.K2 : superficie (km2)

Salida: datos_crudos/densidad_pais.csv
"""

import sys
import time
from pathlib import Path

import pandas as pd
import requests

PAIS = "ARG"
INDICADORES = {
    "EN.POP.DNST": "densidad_hab_km2",
    "SP.POP.TOTL": "poblacion_total",
    "AG.LND.TOTL.K2": "superficie_km2",
}
DESDE = 1960
HASTA = 2025
URL = "https://api.worldbank.org/v2/country/{pais}/indicator/{codigo}"

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "datos_crudos" / "densidad_pais.csv"


def pedir_con_reintentos(url, params, intentos=5, espera_base=30):
    """Pide a la API y reintenta con espera creciente si la respuesta no sirve."""
    for intento in range(1, intentos + 1):
        try:
            r = requests.get(url, params=params, timeout=60)
            if r.status_code == 200:
                datos = r.json()
                # La API devuelve [metadatos, filas]; si hay error devuelve otra forma
                if isinstance(datos, list) and len(datos) == 2:
                    return datos
        except (requests.RequestException, ValueError) as e:
            print(f"  error de red/JSON: {e}")
        espera = espera_base * intento
        print(f"  intento {intento}/{intentos} fallido, espero {espera} s...")
        time.sleep(espera)
    return None


def traer_indicador(codigo):
    params = {
        "format": "json",
        "per_page": 200,
        "date": f"{DESDE}:{HASTA}",
    }
    respuesta = pedir_con_reintentos(URL.format(pais=PAIS, codigo=codigo), params)
    if respuesta is None:
        return None
    filas = respuesta[1] or []
    registros = [
        {"anio": int(f["date"]), "valor": f["value"]}
        for f in filas
        if f.get("value") is not None
    ]
    return pd.DataFrame(registros)


def main():
    tablas = []
    fallidos = []

    for codigo, nombre in INDICADORES.items():
        print(f"Pidiendo {codigo} ({nombre})...")
        df = traer_indicador(codigo)
        if df is None or df.empty:
            fallidos.append(codigo)
            continue
        df = df.rename(columns={"valor": nombre}).set_index("anio")
        tablas.append(df)
        print(f"  OK: {df.index.min()} a {df.index.max()} ({len(df)} anios)")
        time.sleep(2)

    if fallidos:
        print(f"\nATENCION: no se pudieron traer: {', '.join(fallidos)}")
        if not tablas:
            sys.exit(1)

    resultado = pd.concat(tablas, axis=1).sort_index().reset_index()
    resultado = resultado.rename(columns={"index": "anio"})

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(SALIDA, index=False)
    print(f"\nGuardado: {SALIDA} ({len(resultado)} filas)")
    print(resultado.head(3).to_string(index=False))
    print(resultado.tail(3).to_string(index=False))

    if not fallidos:
        print("\nListo, los tres indicadores se trajeron completos.")


if __name__ == "__main__":
    main()