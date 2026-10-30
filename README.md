# Densidad poblacional de Argentina

Análisis de cómo cambió la densidad de población de Argentina a través de los años, a nivel país (1960–2025) y por provincia (censos de 1914 a 2022). Es un proyecto personal de análisis de datos con el circuito completo: extracción por API, procesamiento en Python y dashboard en Power BI.

## Qué responde

- ¿Cuánto creció la densidad del país desde 1960 y a qué ritmo?
- ¿Cómo se distribuye hoy la población entre las 24 jurisdicciones?
- ¿Qué provincias multiplicaron más su densidad desde 1914?

## Resultados principales

- **País:** la densidad pasó de 7,45 hab/km² en 1960 a 16,75 en 2025 (2,25 veces). El crecimiento anual de la población bajó de cerca de 1,7% a comienzos de los años 60 a menos de 0,4% entre 2023 y 2025.
- **Provincias en 2022:** la Ciudad de Buenos Aires tiene 15.161 hab/km², muy por encima del resto. Le siguen Tucumán (76,7), Buenos Aires (57,3) y Misiones (42,8). Santa Cruz (1,4) y La Pampa (2,5) son las menos densas.
- **Crecimiento 1914–2022:** Tierra del Fuego multiplicó su densidad 74,2 veces, seguida de Santa Cruz (33,9), Formosa (31,5), Chubut (25,7) y Neuquén (24,6). En el otro extremo están Entre Ríos (3,4), Corrientes (3,5), La Pampa (3,6) y CABA (2,0).

## Fuentes de datos

| Dato | Fuente | Cómo se obtiene |
| --- | --- | --- |
| Población total, superficie y densidad del país, 1960–2025 | [API del Banco Mundial](https://api.worldbank.org/v2/country/ARG/indicator/EN.POP.DNST) (indicadores `EN.POP.DNST`, `SP.POP.TOTL`, `AG.LND.TOTL.K2`) | Script `extraer_densidad_pais.py` |
| Población por provincia, censos 1914 a 2001 | [Evolución de la población por provincia (Ministerio del Interior, con datos de INDEC)](https://mininterior.gob.ar/poblacion/archivos_estadisticas/EvolucionPoblacionProvincias1914.pdf) | Tabla armada a mano |
| Población 2010 y 2022 y superficie por provincia | INDEC, Censo 2022, resultados definitivos: Cuadro 1 (`c2022_tp_est_c1.xlsx`) y Cuadro 2 (`c2022_tp_est_c2.xlsx`), sección "Total del país" en [censo.gob.ar](https://censo.gob.ar/index.php/datos_definitivos_total_pais/) | Descarga manual |
| Coordenadas de las provincias (para el mapa) | API Georef (apis.datos.gob.ar), del proyecto [clima-provincias](https://github.com/Charly202610/clima-provincias) | Archivo `provincias_coordenadas.csv` |

## Estructura del proyecto

```
densidad-poblacional/
├── datos_crudos/        # datos descargados (no se suben a Git)
├── datos_procesados/    # CSV listos para Power BI (no se suben a Git)
├── scripts/
│   ├── extraer_densidad_pais.py
│   ├── procesar_densidad.py
│   └── procesar_densidad_provincias.py
├── resultados/          # informe de Power BI (no se sube a Git)
├── documentacion/
└── requirements.txt
```

## Cómo reproducirlo

1. Crear y activar el entorno virtual e instalar las dependencias:
   ```
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Nivel país**, con acceso a internet:
   ```
   python scripts\extraer_densidad_pais.py
   python scripts\procesar_densidad.py
   ```
   Genera `datos_procesados/densidad_pais_anual.csv`.
3. **Nivel provincial.** Antes hay que dejar en `datos_crudos/` tres archivos que no están en el repositorio:
   - `c2022_tp_est_c1.xlsx` y `c2022_tp_est_c2.xlsx`, descargados de INDEC (ver tabla de fuentes).
   - `poblacion_provincias_1914_2001.tsv`: tabla separada por tabuladores con la población de cada provincia en los censos 1914 a 2001, transcripta de la fuente del Ministerio del Interior. Las columnas son `Provincia`, `1914`, `1947`, `1960`, `1970`, `1980`, `1991`, `2001`, con una fila `Total` y la provincia de Buenos Aires dividida en "Partidos del Gran Buenos Aires" y "Resto de la Provincia de Buenos Aires". Los miles se escriben con punto.

   Después:
   ```
   python scripts\procesar_densidad_provincias.py
   ```
   Genera `datos_procesados/densidad_provincias_censos.csv`.
4. Abrir el informe de Power BI y actualizar los datos.

Los scripts frenan con un error si algún control falla, por ejemplo si las provincias no suman el total nacional de un censo.

## Decisiones y correcciones sobre los datos

- **Años sin dato del Banco Mundial.** En 1960 y 2025 la serie de densidad y superficie viene vacía. Como la superficie es constante, la densidad se calcula como población ÷ superficie y se marca como `calculada` en la columna `fuente_densidad`.
- **Dos valores corregidos en la tabla histórica.** Con la tabla del Ministerio tal cual, las provincias no sumaban el total nacional en los censos de 1947 y 1980. Se corrigieron dos valores y quedan marcados con `corregido = si` en el CSV provincial:
  - *Tucumán 1947:* 293.371 pasó a 593.371 (la diferencia era de exactamente 300.000, y el valor nuevo queda entre 1914 y 1960).
  - *Resto de la provincia de Buenos Aires 1980:* el valor repetía el de CABA (2.922.829) y se reemplazó por 4.022.207. Con esa corrección, la provincia de Buenos Aires da 10.865.408 en 1980, que coincide con la serie publicada por la Dirección Provincial de Estadística de la provincia. La serie completa de Buenos Aires (nueve censos) también coincide.
- **Superficie de Tierra del Fuego.** La superficie oficial de la provincia (910.324 km²) incluye el sector antártico y las islas del Atlántico Sur, y deja la densidad en 0,2 hab/km². Se usa la superficie de la Isla Grande (21.571 km², departamentos Ushuaia y Río Grande), donde vive casi toda la población, según la nota 3 del Cuadro 2 de INDEC. La constante `SUPERFICIE_TDF_KM2` del script permite cambiar el criterio.
- **Las densidades país y provincial no coinciden.** El Banco Mundial usa una superficie de 2.736.690 km² (16,7 hab/km² en 2024), mientras que INDEC suma 3.669.710 km² con la Antártida y las islas (12,5 hab/km² en 2022). Por eso el dashboard presenta las dos series por separado.
- **Densidad redondeada.** En el CSV provincial la densidad se guarda con 2 decimales. Para comparar crecimiento entre censos conviene usar la población (la superficie no cambia), que es lo que hace la medida `Veces_1914_2022`.
- **Censos desparejos.** Los intervalos entre censos van de 9 a 33 años, así que para comparar ritmos se incluye la tasa de crecimiento anual compuesta.

## Dashboard de Power BI

El informe tiene cinco páginas:

1. **País:** curva de densidad 1960–2025 y tarjetas con la densidad inicial, la final y las veces que se multiplicó.
2. **Crecimiento del país:** columnas con el crecimiento anual de la población, que baja de cerca de 1,7% a menos de 0,4%.
3. **Provincias en un censo:** segmentador de censo, mapa de burbujas con color en escala fija de 0 a 80 hab/km² (sin CABA), barras de densidad por provincia y tarjeta aparte con CABA.
4. **Evolución:** líneas de las cinco provincias más densas entre 1914 y 2022.
5. **Crecimiento:** cuántas veces creció la densidad de cada provincia entre 1914 y 2022.

El archivo `.pbix` no se sube al repositorio.

## Limitaciones

- La tabla de 1914 a 2001 es una fuente secundaria transcripta a mano; no se contrastó contra los cuadros originales de cada censo, salvo la serie de Buenos Aires.
- La población de 2025 del Banco Mundial es una estimación.
- Los datos de provincias son censales (nueve puntos por provincia), no una serie anual.
- Los límites provinciales y la superficie se toman como constantes en todo el período, aunque los territorios nacionales de 1914 (como Tierra del Fuego, Santa Cruz o Chubut) se convirtieron en provincias más tarde.