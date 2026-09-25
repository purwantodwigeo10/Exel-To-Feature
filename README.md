# Excel to Feature (Coordinate Transformation)

Excel to Feature creates point, polyline, and polygon layers from coordinate
tables. Users select X and Y fields, an optional Z field, an optional point-order
field, source and destination coordinate systems, and one or more output
geometry types.

The public plugin title is **Excel to Feature**. Its established activation
identity (`ETFAR`) and legacy License Hub product identifier remain unchanged.

## Supported input and output

- Output: Shapefile or GeoPackage.
- Geometry: points, one polyline, and/or one polygon from the valid ordered rows.

## Installation

1. Download the release ZIP without extracting it.
2. In QGIS, open **Plugins > Manage and Install Plugins > Install from ZIP**.
3. Select the ZIP, install it, and enable **Excel to Feature**.
4. Open it from **Vector > RUANG SPASIAL** or its toolbar button.

## Quick test

1. Choose `sample_data/coordinates.csv`.
2. Select `X` and `Y`; select `ORDER` as the point/order field.
3. Set the input and output CRS to EPSG:4326.
4. Choose Point, Polyline, and Polygon and save to a new GeoPackage path.
5. Confirm that all selected outputs are created and added to QGIS.

All sample coordinates are synthetic.

## Activation

- Product code: `ETFAR`
- Trial: 2 successful processing runs

Trial use is recorded only after output creation succeeds.

## Source, help, and support

- Help: <https://aktivasi.ruangspasial.my.id/help/exel-to-feature-coordinate-transformation-qgis>
- Source: <https://github.com/purwantodwigeo10/Exel-To-Feature>
- Issues: <https://github.com/purwantodwigeo10/Exel-To-Feature/issues>

Copyright (C) 2026 Dwi Purwanto / Ruang Spasial. Licensed under
GPL-3.0-or-later; see `LICENSE`.

Existing output filenames are refused; choose a new name for each run.
