# Changelog

## 1.4.3 metadata correction

- Corrected the GitHub repository and issue-tracker URLs to match the actual
  `purwantodwigeo10/Exel-To-Feature` repository.

## 1.4.3

- Improved CSV and XLSX coordinate-table reading.
- Added bounded XML parsing safeguards for the dependency-free XLSX fallback.
- Improved point, polyline, and polygon output validation.
- Added sample data and clearer usage documentation.

## 1.4.2

- Added minimize and maximize controls to plugin and activation windows.


## 1.4.3 — compatibility and reliability revision

- Use optional Z values in PointZ/LineStringZ/PolygonZ geometry; XY reprojection does not perform vertical-datum conversion.
- Reject non-finite coordinates; handle Indonesian and international numeric separators.
- Validate all selected geometry types before starting output writes.
- Reject invalid coordinate rows for line/polygon output and reject invalid polygon rings.
- Correct missing output extension and use the V3 vector writer with the correct error message.
- Harden the XLSX XML fallback against late/UTF-16 DTD declarations, invalid columns and missing shared strings.
