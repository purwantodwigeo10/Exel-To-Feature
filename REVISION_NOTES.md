# Revision notes — axel_to_feature_etf 1.4.3

Version retained at the author's request.

## Changes

- Correct the public title to **Excel to Feature** while preserving the established `ETFAR` License Hub identity.

- Use scoped Qt enums, exec(), Qt-compatible QAction imports and explicit Qt5/Qt6 field types.
- Use bounded License Hub HTTPS requests, manual redirect policy, HTTP/network error checks and an already-finished reply guard.
- Give explicit inactive/revoked/expired/pending states priority over conflicting success flags.
- Prevent reentrant Run operations during nested event loops.
- Require new output filenames to protect existing data; partial new output may remain if a later write fails.
- Use optional Z values in PointZ/LineStringZ/PolygonZ geometry; XY reprojection does not perform vertical-datum conversion.
- Reject non-finite coordinates; handle Indonesian and international numeric separators.
- Validate all selected geometry types before starting output writes.
- Reject invalid coordinate rows for line/polygon output and reject invalid polygon rings.
- Correct missing output extension and use the V3 vector writer with the correct error message.
- Harden the XLSX XML fallback against late/UTF-16 DTD declarations, invalid columns and missing shared strings.

## Required QGIS test

Test coordinates.csv first. Test X/Y in EPSG:4326 and transform to the correct local projected CRS. Add a Z column with different values: verify geometry Z in QGIS. Test a self-intersecting polygon, NaN, a duplicate point, Indonesian decimal comma and international thousands separators. A single separator means decimal, so write 1000 instead of 1.000 when intending one thousand.

## Validation limits

Offline regression tests, actual standalone PyQt5/PyQt6 enum checks, and Python lint/syntax checks were run. Full QGIS/GDAL processing, Windows file locking, live activation and the official repository scanners were not run. The package retains QGIS 3.22–3.99 compatibility metadata; no QGIS 4 support is claimed. Standalone Qt tests do not establish complete QGIS compatibility.

## Publishing

Install this ZIP in QGIS without extracting it. For GitHub, extract and upload the contents of this plugin folder at the existing repository root. Do not upload another plugin's files. Check public repository, issue tracker and help URLs before uploading to QGIS. Changing GitHub source or version text does not replace the ZIP stored on the QGIS plugin site. If the version already exists, inspect its Manage/Edit options before replacing it; do not delete the whole plugin.
