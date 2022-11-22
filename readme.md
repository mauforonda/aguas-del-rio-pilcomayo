> Mediciones de la calidad de agua en el río Pilcomayo entre abril de 2007 y agosto de 2022

Fuente: [portal de la Comisión Trinacional para el Desarrollo de la Cuenca del Río Pilcomayo](https://www.pilcomayo.net/calidaddeaguas)

En este repositorio encuentras:

- [Todas las mediciones disponibles en la misma forma como son presentadas en el portal](data/mediciones.csv)
- [Las mismas mediciones luego de ser limpiadas para facilitar el análisis](data/mediciones_procesadas.csv)

El procesamiento consistió en:

- Convertir todas las mediciones a números reales. La decisión más cuestionable fue normalizar expresiones de la forma `< 0.1 ` como `0.1`. 

- Remover columnas redundantes: consolidar fechas en una sóla columna que contenga el día y la hora, sólo mantener coordenadas geográficas en el sistema WGS 84, y simplificar los nombres de columnas.

El código utilizado en la [descarga](retrieve.ipynb) y [procesamiento](limpieza.ipynb) de estos datos es parte de este repositorio y puede ser consultado.

