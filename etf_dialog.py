from .run_guard import single_run
from .number_utils import parse_number
from .output_safety import ensure_new_output
from qgis.core import QgsPoint, QgsLineString, QgsPolygon
from .qt_compat import FIELD_STRING, FIELD_INT
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import traceback

from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QComboBox, QCheckBox, QMessageBox, QGroupBox, QTextEdit,
    QApplication
)
from qgis.PyQt.QtGui import QPixmap, QDesktopServices

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsPointXY,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsVectorFileWriter
)
from qgis.gui import QgsProjectionSelectionWidget

from .licensehub_etf_qgis import LicenseManager, PRODUCT_CODE, PRODUCT_NAME, TRIAL_LIMIT
from .excel_reader import list_sheets, read_table

HELP_URL = "https://aktivasi.ruangspasial.my.id/help/exel-to-feature-coordinate-transformation-qgis"


class ActivationDialog(QDialog):
    def __init__(self, lm, parent=None):
        super(ActivationDialog, self).__init__(parent)
        self.lm = lm
        self.setWindowTitle("License Activation")
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setSizeGripEnabled(True)
        self.resize(720, 180)
        self._build_ui()
        self.refresh_status(quiet=True)

    def _build_ui(self):
        main = QVBoxLayout(self)

        grid = QGridLayout()
        self.lbl_status = QLabel("-")
        self.lbl_status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.txt_device_id = QLineEdit()
        self.txt_device_id.setReadOnly(True)

        self.btn_copy = QPushButton("Copy Device ID")
        self.btn_copy.clicked.connect(self.copy_device_id)

        self.lbl_trial = QLabel("-")

        self.txt_code = QLineEdit()
        self.txt_code.setPlaceholderText(
            "Enter activation code from License Hub")

        grid.addWidget(QLabel("Activation Status"), 0, 0)
        grid.addWidget(self.lbl_status, 0, 1, 1, 2)
        grid.addWidget(QLabel("Device ID"), 1, 0)
        grid.addWidget(self.txt_device_id, 1, 1)
        grid.addWidget(self.btn_copy, 1, 2)
        grid.addWidget(QLabel("Trial Usage"), 2, 0)
        grid.addWidget(self.lbl_trial, 2, 1, 1, 2)
        grid.addWidget(QLabel("Activation Code"), 3, 0)
        grid.addWidget(self.txt_code, 3, 1, 1, 2)
        main.addLayout(grid)

        btn_row = QHBoxLayout()
        self.btn_request = QPushButton("Submit Request")
        self.btn_request.clicked.connect(self.open_request_page)
        self.btn_activate = QPushButton("Activate")
        self.btn_activate.clicked.connect(self.activate_license)
        self.btn_refresh = QPushButton("Refresh Status")
        self.btn_refresh.clicked.connect(
            lambda: self.refresh_status(quiet=False))
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_request)
        btn_row.addWidget(self.btn_activate)
        btn_row.addWidget(self.btn_refresh)
        btn_row.addWidget(self.btn_close)
        main.addLayout(btn_row)

    def refresh_status(self, quiet=True):
        self.txt_device_id.setText(self.lm.get_device_id())
        status = self.lm.status_text()
        self.lbl_status.setText(status)
        remaining = self.lm.trial_remaining()
        used = TRIAL_LIMIT - remaining
        self.lbl_trial.setText("%s/%s used, %s remaining" %
                               (used, TRIAL_LIMIT, remaining))
        if status.startswith("Active"):
            self.lbl_status.setStyleSheet("font-weight: bold; color: #0B7A2A;")
        elif status.startswith("Trial"):
            self.lbl_status.setStyleSheet("font-weight: bold; color: #B35C00;")
        elif status.startswith("Expired"):
            self.lbl_status.setStyleSheet("font-weight: bold; color: #B00020;")
        elif status.startswith("Deactivated"):
            self.lbl_status.setStyleSheet("font-weight: bold; color: #7A003C;")
        else:
            self.lbl_status.setStyleSheet("font-weight: bold; color: #B00020;")
        if not quiet:
            ok, msg = self.lm.refresh_activation_from_server()
            self.txt_device_id.setText(self.lm.get_device_id())
            self.lbl_status.setText(self.lm.status_text())
            remaining = self.lm.trial_remaining()
            used = TRIAL_LIMIT - remaining
            self.lbl_trial.setText("%s/%s used, %s remaining" %
                                   (used, TRIAL_LIMIT, remaining))
            if ok is True:
                QMessageBox.information(
                    self, PRODUCT_NAME, "License status was refreshed from the website.")
            else:
                QMessageBox.warning(
                    self,
                    PRODUCT_NAME,
                    msg or "License status could not be confirmed from the website.")

    def copy_device_id(self):
        try:
            QApplication.clipboard().setText(self.txt_device_id.text().strip())
            QMessageBox.information(
                self, PRODUCT_NAME, "Device ID copied successfully.")
        except Exception as e:
            QMessageBox.warning(self, PRODUCT_NAME,
                                "Failed to copy Device ID: %s" % e)

    def open_request_page(self):
        try:
            self.lm.open_request_url()
            QMessageBox.information(
                self, PRODUCT_NAME, "The activation request page has been opened.\n\n"
                "Please submit the activation request on the opened web page. "
                "Make sure the Device ID and ETFAR product code are correct. "
                "After the request is approved, enter the activation code in the field provided and click Activate.")
        except Exception as e:
            QMessageBox.critical(self, PRODUCT_NAME,
                                 "Failed to open request page: %s" % e)

    def activate_license(self):
        code = self.txt_code.text().strip()
        ok, msg = self.lm.activate(code)
        self.refresh_status(quiet=True)
        if ok:
            QMessageBox.information(self, PRODUCT_NAME, msg)
            self.accept()
        else:
            QMessageBox.warning(self, PRODUCT_NAME, msg)


class ExelToFeatureDialog(QDialog):
    def __init__(self, iface, parent=None):
        super(ExelToFeatureDialog, self).__init__(parent)
        self.iface = iface
        self.lm = LicenseManager()
        self.headers = []
        self.records = []
        self.setWindowTitle("Exel to Feature (Coordinate Transformation)")
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setSizeGripEnabled(True)
        self.resize(900, 720)
        self._build_ui()
        self.refresh_license_status()

    def _build_ui(self):
        main = QVBoxLayout(self)

        hero = QGroupBox()
        hero_layout = QHBoxLayout(hero)

        self.lbl_logo = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path)
            self.lbl_logo.setPixmap(pix.scaled(
                150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.lbl_logo.setMinimumWidth(180)
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(self.lbl_logo)

        center = QVBoxLayout()
        self.lbl_title = QLabel(
            "<span style='font-size:24px; font-weight:700;'>Exel to Feature</span><br><span style='font-size:16px; font-weight:600;'>(Coordinate Transformation)</span>")
        self.lbl_title.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_desc = QLabel(
            "Exel to Feature helps users convert coordinate data from Excel or CSV files into "
            "Point, Polyline, and Polygon layers quickly and efficiently. This plugin supports sheet selection, "
            "coordinate fields, input and output coordinate systems, and saving results to Shapefile or GeoPackage.")
        self.lbl_desc.setWordWrap(True)
        center.addWidget(self.lbl_title)
        center.addWidget(self.lbl_desc)
        center.addStretch(1)
        hero_layout.addLayout(center, 1)

        right = QVBoxLayout()
        self.lbl_plugin_status = QLabel()
        self.lbl_plugin_status.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_activation = QLabel()
        self.lbl_activation.setTextFormat(Qt.TextFormat.RichText)
        self.btn_manage = QPushButton("Manage Activation")
        self.btn_manage.clicked.connect(self.show_activation_dialog)
        self.btn_help_main = QPushButton("User Guide and Activation")
        self.btn_help_main.clicked.connect(self.open_help_page)
        right.addWidget(self.lbl_plugin_status, 0, Qt.AlignmentFlag.AlignRight)
        right.addWidget(self.lbl_activation, 0, Qt.AlignmentFlag.AlignRight)
        right.addWidget(self.btn_manage, 0, Qt.AlignmentFlag.AlignRight)
        right.addWidget(self.btn_help_main, 0, Qt.AlignmentFlag.AlignRight)
        right.addStretch(1)
        hero_layout.addLayout(right)

        main.addWidget(hero)

        tool_box = QGroupBox("Tool")
        layout = QVBoxLayout(tool_box)

        input_box = QGroupBox("Input and Output")
        grid = QGridLayout(input_box)
        self.txt_excel = QLineEdit()
        self.btn_excel = QPushButton("Browse...")
        self.btn_excel.clicked.connect(self.choose_excel)
        self.cmb_sheet = QComboBox()
        self.btn_reload_sheet = QPushButton("Read Sheet/Fields")
        self.btn_reload_sheet.clicked.connect(self.load_sheet_and_fields)
        self.txt_output = QLineEdit()
        self.btn_output = QPushButton("Save...")
        self.btn_output.clicked.connect(self.choose_output)
        grid.addWidget(QLabel("Input File (.xlsx/.xls/.csv)"), 0, 0)
        grid.addWidget(self.txt_excel, 0, 1)
        grid.addWidget(self.btn_excel, 0, 2)
        grid.addWidget(QLabel("Sheet"), 1, 0)
        grid.addWidget(self.cmb_sheet, 1, 1)
        grid.addWidget(self.btn_reload_sheet, 1, 2)
        grid.addWidget(QLabel("Output Feature Class (base)"), 2, 0)
        grid.addWidget(self.txt_output, 2, 1)
        grid.addWidget(self.btn_output, 2, 2)
        layout.addWidget(input_box)

        field_box = QGroupBox("Coordinate Fields")
        grid2 = QGridLayout(field_box)
        self.cmb_point = QComboBox()
        self.cmb_x = QComboBox()
        self.cmb_y = QComboBox()
        self.cmb_z = QComboBox()
        grid2.addWidget(QLabel("Point / Order Field"), 0, 0)
        grid2.addWidget(self.cmb_point, 0, 1)
        grid2.addWidget(QLabel("X Field"), 1, 0)
        grid2.addWidget(self.cmb_x, 1, 1)
        grid2.addWidget(QLabel("Y Field"), 2, 0)
        grid2.addWidget(self.cmb_y, 2, 1)
        grid2.addWidget(QLabel("Z Field (Optional)"), 3, 0)
        grid2.addWidget(self.cmb_z, 3, 1)
        layout.addWidget(field_box)

        crs_box = QGroupBox("Coordinate System")
        grid3 = QGridLayout(crs_box)
        self.crs_input = QgsProjectionSelectionWidget()
        self.crs_output = QgsProjectionSelectionWidget()
        self.crs_input.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
        self.crs_output.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
        grid3.addWidget(QLabel("Input Coordinate System"), 0, 0)
        grid3.addWidget(self.crs_input, 0, 1)
        grid3.addWidget(QLabel("Output Coordinate System"), 1, 0)
        grid3.addWidget(self.crs_output, 1, 1)
        layout.addWidget(crs_box)

        geom_box = QGroupBox("Output Geometry")
        geom_row = QHBoxLayout(geom_box)
        self.chk_point = QCheckBox("Point")
        self.chk_line = QCheckBox("Polyline")
        self.chk_polygon = QCheckBox("Polygon")
        self.chk_point.setChecked(True)
        geom_row.addWidget(self.chk_point)
        geom_row.addWidget(self.chk_line)
        geom_row.addWidget(self.chk_polygon)
        geom_row.addStretch(1)
        layout.addWidget(geom_box)

        run_row = QHBoxLayout()
        self.btn_run = QPushButton("Run Tool")
        self.btn_run.clicked.connect(self.run_tool)
        run_row.addStretch(1)
        run_row.addWidget(self.btn_run)
        layout.addLayout(run_row)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(140)
        layout.addWidget(self.log)
        main.addWidget(tool_box)

        bottom = QHBoxLayout()
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        bottom.addStretch(1)
        bottom.addWidget(self.btn_close)
        main.addLayout(bottom)

    def open_help_page(self):
        try:
            opened = QDesktopServices.openUrl(QUrl(HELP_URL))
            if not opened:
                QMessageBox.warning(
                    self,
                    PRODUCT_NAME,
                    "The help page could not be opened automatically. Please open this link manually:\n%s" %
                    HELP_URL)
        except Exception as e:
            QMessageBox.warning(self, PRODUCT_NAME,
                                "Failed to open help page: %s\n%s" % (e, HELP_URL))

    def show_activation_dialog(self):
        dlg = ActivationDialog(self.lm, self)
        dlg.exec()
        self.refresh_license_status()

    def refresh_license_status(self):
        self.lbl_plugin_status.setText(
            "<b><span style='color:#0B7A2A;'>Plugin Status : Ready</span></b> | "
            "<span style='color:#2D6A4F;'>Background Mode: Enabled</span>"
        )
        status = self.lm.status_text()
        if status.startswith("Active"):
            text = "<b><span style='color:#0B7A2A;'>Activation : Active</span></b>"
        elif status.startswith("Trial"):
            text = "<b><span style='color:#B35C00;'>Activation : Trial</span></b>"
        elif status.startswith("Expired"):
            text = "<b><span style='color:#B00020;'>Activation : Expired</span></b>"
        elif status.startswith("Deactivated"):
            text = "<b><span style='color:#7A003C;'>Activation : Deactivated</span></b>"
        else:
            text = "<b><span style='color:#B00020;'>Activation : Unknown</span></b>"
        self.lbl_activation.setText(text)

    # =====================================================
    # Tool actions
    # =====================================================
    def choose_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel/CSV file", "", "Excel/CSV (*.xlsx *.xls *.csv);;All Files (*.*)")
        if path:
            self.txt_excel.setText(path)
            self.load_sheet_names()
            self.load_sheet_and_fields()

    def choose_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save output", "", "Shapefile (*.shp);;GeoPackage (*.gpkg)"
        )
        if path:
            if not os.path.splitext(path)[1]:
                path += ".shp"
            self.txt_output.setText(path)

    def load_sheet_names(self):
        path = self.txt_excel.text().strip()
        self.cmb_sheet.clear()
        if not path or not os.path.exists(path):
            return
        try:
            names = list_sheets(path)
            if not names:
                names = ["Sheet1"]
            self.cmb_sheet.addItems(names)
        except Exception as e:
            self.warn("Failed to read sheet list: %s" % e)

    def load_sheet_and_fields(self):
        path = self.txt_excel.text().strip()
        if not path or not os.path.exists(path):
            self.warn("Please select an input file first.")
            return
        sheet = self.cmb_sheet.currentText().strip() if self.cmb_sheet.count() else None
        try:
            headers, records = read_table(path, sheet)
            self.headers = headers
            self.records = records
            self.populate_field_combos(headers)
            self.log_msg("Fields loaded successfully: %s" % ", ".join(headers))
            self.log_msg("Number of data rows: %s" % len(records))
        except Exception as e:
            self.error("Failed to read fields: %s" % e)

    def populate_field_combos(self, headers):
        combos = [self.cmb_point, self.cmb_x, self.cmb_y, self.cmb_z]
        for c in combos:
            c.clear()
        self.cmb_point.addItem("<none>")
        self.cmb_z.addItem("<none>")
        for h in headers:
            self.cmb_point.addItem(h)
            self.cmb_x.addItem(h)
            self.cmb_y.addItem(h)
            self.cmb_z.addItem(h)
        self._auto_pick(self.cmb_x, ["x", "longitude", "long",
                        "lon", "easting", "east", "koordinat_x"])
        self._auto_pick(self.cmb_y, ["y", "latitude", "lat",
                        "northing", "north", "koordinat_y"])
        self._auto_pick(
            self.cmb_z, ["z", "elev", "elevation", "tinggi"], none_first=True)
        self._auto_pick(self.cmb_point, ["point", "titik",
                        "no", "id", "nomor"], none_first=True)

    def _auto_pick(self, combo, candidates, none_first=False):
        if combo.count() == 0:
            return
        for cand in candidates:
            for i in range(combo.count()):
                text = combo.itemText(i).strip().lower().replace(" ", "_")
                if text == cand or cand in text:
                    combo.setCurrentIndex(i)
                    return
        if none_first:
            combo.setCurrentIndex(0)

    @single_run
    def run_tool(self):
        can_run, msg = self.lm.can_run()
        if not can_run:
            self.refresh_license_status()
            self.error(msg)
            return
        trial_mode = not self.lm.is_activated_local()
        if trial_mode:
            self.warn(
                "Trial mode is being used. One trial use will be recorded only "
                "after output is created successfully."
            )

        try:
            outputs = self._process()
            if trial_mode:
                self.lm.consume_trial_for_run()
            self.info("Process completed. Output created:\n" + \
                      "\n".join(outputs))
            self.refresh_license_status()
        except Exception as e:
            self.error("Failed to run tool:\n%s\n\n%s" %
                       (e, traceback.format_exc()))

    # =====================================================
    # Processing
    # =====================================================
    def _process(self):
        path = self.txt_excel.text().strip()
        out_base = self.txt_output.text().strip()
        if not path or not os.path.exists(path):
            raise RuntimeError(
                "Input file has not been selected or cannot be found.")
        if not out_base:
            raise RuntimeError("Output has not been specified.")
        if not (self.chk_point.isChecked() or self.chk_line.isChecked()
                or self.chk_polygon.isChecked()):
            raise RuntimeError(
                "Select at least one output: Point, Polyline, or Polygon.")
        sheet = self.cmb_sheet.currentText().strip() if self.cmb_sheet.count() else None
        headers, records = read_table(path, sheet)
        if not records:
            raise RuntimeError("There are no data rows to process.")
        x_field = self.cmb_x.currentText().strip()
        y_field = self.cmb_y.currentText().strip()
        z_field = self.cmb_z.currentText().strip()
        point_field = self.cmb_point.currentText().strip()
        if not x_field or not y_field:
            raise RuntimeError("X and Y fields are required.")
        if x_field == y_field:
            raise RuntimeError("X and Y must use different coordinate fields.")
        if z_field == "<none>":
            z_field = ""
        if point_field == "<none>":
            point_field = ""
        in_crs = self.crs_input.crs()
        out_crs = self.crs_output.crs()
        if not in_crs.isValid() or not out_crs.isValid():
            raise RuntimeError("Input/Output Coordinate System is not valid.")
        points, clean_records, invalid = self._records_to_points(
            records, x_field, y_field, in_crs, out_crs, point_field, z_field)
        if invalid:
            self.warn(
                "%s rows were skipped because the coordinates are invalid." %
                invalid)
        if len(points) == 0:
            raise RuntimeError("No valid coordinates were found.")

        outputs = []
        derived = self._derive_outputs(out_base, self.chk_point.isChecked(
        ), self.chk_line.isChecked(), self.chk_polygon.isChecked())
        if self.chk_line.isChecked() and len({(p.x(), p.y()) for p in points}) < 2:
            raise RuntimeError("Polyline requires at least two distinct coordinates.")
        if self.chk_polygon.isChecked() and len({(p.x(), p.y()) for p in points}) < 3:
            raise RuntimeError("Polygon requires at least three distinct coordinates.")
        if invalid and (self.chk_line.isChecked() or self.chk_polygon.isChecked()):
            raise RuntimeError("Invalid rows would change boundary topology. Correct those rows before creating lines or polygons.")
        layers = []
        for key, maker in (("point", self._make_point_layer), ("line", self._make_line_layer),
                           ("polygon", self._make_polygon_layer)):
            if derived[key]:
                ensure_new_output(derived[key])
                layers.append((maker(headers, clean_records, points, out_crs), derived[key]))
        for layer, destination in layers:
            self._write_layer(layer, destination)
            loaded = QgsVectorLayer(destination, os.path.basename(destination), "ogr")
            if not loaded.isValid() or loaded.featureCount() != layer.featureCount():
                raise RuntimeError("Output validation failed: %s" % destination)
            QgsProject.instance().addMapLayer(loaded)
            outputs.append(destination)
        return outputs

    def _parse_float(self, value):
        return parse_number(value)

    def _records_to_points(
            self,
            records,
            x_field,
            y_field,
            in_crs,
            out_crs,
            point_field="", z_field=""):
        transformer = None
        if in_crs.authid() != out_crs.authid() or in_crs.toWkt() != out_crs.toWkt():
            transformer = QgsCoordinateTransform(
                in_crs, out_crs, QgsProject.instance())
        if point_field:
            try:
                records = sorted(
                    records, key=lambda r: self._parse_float(r.get(point_field)))
            except (TypeError, ValueError) as error:
                self.warn(
                    "The point/order field could not be sorted; input row "
                    "order will be used. Detail: %s" % error
                )
        pts = []
        clean = []
        invalid = 0
        for rec in records:
            try:
                x = self._parse_float(rec.get(x_field))
                y = self._parse_float(rec.get(y_field))
                if in_crs.isGeographic() and (abs(x) > 180 or abs(y) > 90):
                    raise ValueError("Longitude/latitude is outside its valid range.")
                z = self._parse_float(rec.get(z_field)) if z_field else None
                pt = QgsPointXY(x, y)
                if transformer:
                    pt = transformer.transform(pt)
                self._parse_float(pt.x())
                self._parse_float(pt.y())
                pts.append(QgsPoint(pt.x(), pt.y(), z) if z_field else pt)
                clean.append(rec)
            except Exception:
                invalid += 1
        return pts, clean, invalid

    def _make_fields(self, headers):
        fields = []
        seen = set()
        for h in headers:
            name = str(h or "FIELD")[:10]
            if not name:
                name = "FIELD"
            base = name
            i = 2
            while name.upper() in seen:
                suffix = str(i)
                name = (base[:10 - len(suffix)] + suffix)[:10]
                i += 1
            seen.add(name.upper())
            fields.append((h, name))
        return fields

    def _make_point_layer(self, headers, records, points, crs):
        layer = QgsVectorLayer("PointZ" if isinstance(points[0], QgsPoint) else "Point", "ETFAR_Point", "memory")
        layer.setCrs(crs)
        provider = layer.dataProvider()
        fmap = self._make_fields(headers)
        provider.addAttributes([QgsField(out_name, FIELD_STRING)
                               for _, out_name in fmap])
        layer.updateFields()
        feats = []
        for rec, pt in zip(records, points):
            f = QgsFeature(layer.fields())
            f.setGeometry(QgsGeometry(pt) if isinstance(pt, QgsPoint) else QgsGeometry.fromPointXY(pt))
            f.setAttributes([str(rec.get(src, "")) for src, _ in fmap])
            feats.append(f)
        ok, _ = provider.addFeatures(feats)
        if not ok or layer.featureCount() != len(feats):
            raise RuntimeError("Some points could not be added to the output.")
        layer.updateExtents()
        return layer

    def _make_line_layer(self, headers, records, points, crs):
        layer = QgsVectorLayer("LineStringZ" if isinstance(points[0], QgsPoint) else "LineString", "ETFAR_Polyline", "memory")
        layer.setCrs(crs)
        provider = layer.dataProvider()
        provider.addAttributes([QgsField("JUMLAH", FIELD_INT),
                               QgsField("SUMBER", FIELD_STRING)])
        layer.updateFields()
        f = QgsFeature(layer.fields())
        f.setGeometry(QgsGeometry.fromPolyline(points) if isinstance(points[0], QgsPoint) else QgsGeometry.fromPolylineXY(points))
        f.setAttributes([len(points), PRODUCT_CODE])
        if not provider.addFeature(f):
            raise RuntimeError("The geometry could not be added to the output.")
        layer.updateExtents()
        return layer

    def _make_polygon_layer(self, headers, records, points, crs):
        ring = list(points)
        if ring[0] != ring[-1]:
            ring.append(ring[0])
        layer = QgsVectorLayer("PolygonZ" if isinstance(points[0], QgsPoint) else "Polygon", "ETFAR_Polygon", "memory")
        layer.setCrs(crs)
        provider = layer.dataProvider()
        provider.addAttributes([QgsField("JUMLAH", FIELD_INT),
                               QgsField("SUMBER", FIELD_STRING)])
        layer.updateFields()
        f = QgsFeature(layer.fields())
        geometry = (QgsGeometry(QgsPolygon(QgsLineString(ring)))
                    if isinstance(points[0], QgsPoint) else QgsGeometry.fromPolygonXY([ring]))
        if geometry.isEmpty() or geometry.area() <= 0 or not geometry.isGeosValid():
            raise RuntimeError("Polygon is invalid. Check point order, duplicate vertices and self-intersections.")
        f.setGeometry(geometry)
        f.setAttributes([len(points), PRODUCT_CODE])
        if not provider.addFeature(f):
            raise RuntimeError("The geometry could not be added to the output.")
        layer.updateExtents()
        return layer

    def _derive_outputs(self, out_base, do_point, do_line, do_poly):
        folder = os.path.dirname(out_base)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder, exist_ok=True)
        base, ext = os.path.splitext(out_base)
        if not ext:
            ext = ".shp"
            base = out_base
            out_base = base + ext
        if ext.lower() not in (".shp", ".gpkg"):
            raise RuntimeError("Output must use .shp or .gpkg extension.")
        selected = sum(
            [1 if do_point else 0, 1 if do_line else 0, 1 if do_poly else 0])
        if selected == 1:
            return {
                "point": out_base if do_point else None,
                "line": out_base if do_line else None,
                "polygon": out_base if do_poly else None
            }
        return {
            "point": base + "_Point" + ext if do_point else None,
            "line": base + "_Polyline" + ext if do_line else None,
            "polygon": base + "_Polygon" + ext if do_poly else None
        }

    def _write_layer(self, layer, path):
        ensure_new_output(path)
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG" if path.lower().endswith(".gpkg") else "ESRI Shapefile"
        options.fileEncoding = "UTF-8"
        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer, path, QgsProject.instance().transformContext(), options)
        if result[0] != QgsVectorFileWriter.WriterError.NoError:
            raise RuntimeError("Failed to write %s: %s" % (path, result[1]))

    def _delete_existing_vector(self, path):
        base, ext = os.path.splitext(path)
        if ext.lower() == ".shp":
            for e in (".shp", ".shx", ".dbf", ".prj", ".cpg", ".qpj"):
                p = base + e
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError as error:
                        self.log_msg("Could not remove %s: %s" % (p, error))
        elif os.path.exists(path):
            try:
                os.remove(path)
            except OSError as error:
                self.log_msg("Could not remove %s: %s" % (path, error))

    def log_msg(self, msg):
        self.log.append(str(msg))

    def info(self, msg):
        self.log_msg(msg)
        QMessageBox.information(self, PRODUCT_NAME, msg)

    def warn(self, msg):
        self.log_msg("WARNING: " + str(msg))
        QMessageBox.warning(self, PRODUCT_NAME, str(msg))

    def error(self, msg):
        self.log_msg("ERROR: " + str(msg))
        QMessageBox.critical(self, PRODUCT_NAME, str(msg))
