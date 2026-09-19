# Exel to Feature (Coordinate Transformation)

Exel to Feature creates point, polyline, and polygon layers from coordinate
tables. Users select X and Y fields, an optional Z field, an optional point-order
field, source and destination coordinate systems, and one or more output
geometry types.

The public product name intentionally remains **Exel to Feature** to preserve
its established activation identity (`ETFAR`).

## Supported input and output

- Input: CSV and XLSX without an additional Python package.
- Legacy XLS: requires the optional `xlrd` module in QGIS Python.
- Output: Shapefile or GeoPackage.
- Geometry: points, one polyline, and/or one polygon from the valid ordered rows.

## Installation

1. Download the release ZIP without extracting it.
2. In QGIS, open **Plugins > Manage and Install Plugins > Install from ZIP**.
3. Select the ZIP, install it, and enable **Exel to Feature**.
4. Open it from **Vector > RUANG SPASIAL** or its toolbar button.

## Quick test

1. Choose `sample_data/coordinates.csv`.
2. Select `X` and `Y`; select `ORDER` as the point/order field.
3. Set the input and output CRS to EPSG:4326.
4. Choose Point, Polyline, and Polygon and save to a new GeoPackage path.
5. Confirm that all selected outputs are created and added to QGIS.

All sample coordinates are synthetic.

## Activation and privacy

- Product code: `ETFAR`
- Trial: 2 successful processing runs

Trial use is recorded only after output creation succeeds. Activation and
active-license checks use QGIS' network manager and HTTPS at
`aktivasi.ruangspasial.my.id`. Only the product identity, activation code, and a
pseudonymous Device ID are sent. Spreadsheet rows, coordinates, GIS output,
and paths are never transmitted. Local license state is stored in the current
user's application-data directory.

## Source, help, and support

- Help: <https://aktivasi.ruangspasial.my.id/help/exel-to-feature-coordinate-transformation-qgis>
- Source: <https://github.com/purwantodwigeo10/exel-to-feature-qgis>
- Issues: <https://github.com/purwantodwigeo10/exel-to-feature-qgis/issues>

Copyright (C) 2026 Dwi Purwanto / Ruang Spasial. Licensed under
GPL-3.0-or-later; see `LICENSE`.
