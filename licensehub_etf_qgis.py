from .license_response import has_denial
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
"""
licensehub_etf_qgis.py
RUANG SPASIAL License Hub module for QGIS 3.x.

Concept aligned with ArcMap/TBX and previous RUANG SPASIAL plugins:
- Product Code: ETFAR
- Product Name: Exel to Feature (Coordinate Transformation)
- Trial limit: 2 uses
- Device ID compatible with ArcMap/Quirreva/ZoneSculpt/RasterReach
- ETFAR activation codes can be used across ArcMap and QGIS on the same laptop
- Local license file uses the same ArcMap folder:
  %APPDATA%\\RuangSpasial\\LicenseHub\\EXEL_TO_FEATURE_QGIS_ETFAR\\license.json
"""

import os
import re
import json
import hashlib
import socket
import sys
import uuid
import webbrowser
import getpass
import urllib.parse

from .license_network import request_json

try:
    import winreg
except Exception:
    winreg = None

REQUEST_URL = "https://aktivasi.ruangspasial.my.id/request"
LICENSE_API_BASE = "https://aktivasi.ruangspasial.my.id"
PRODUCT_NAME = "Exel to Feature (Coordinate Transformation)"
PRODUCT_CODE = "ETFAR"
FIXED_CODE = ""
LEGACY_PRODUCT_CODES = ()
LICENSE_FOLDER = "EXEL_TO_FEATURE_QGIS_ETFAR"
TRIAL_LIMIT = 2
PLUGIN_VERSION = "1.4.3"


class LicenseManager(object):
    def __init__(self):
        if os.name == "nt":
            appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        elif sys.platform == "darwin":
            appdata = os.path.expanduser("~/Library/Application Support")
        else:
            appdata = os.environ.get("XDG_DATA_HOME") or os.path.expanduser(
                "~/.local/share"
            )
        self.app_dir = os.path.join(appdata, "RuangSpasial",
                                    "LicenseHub", LICENSE_FOLDER)
        os.makedirs(self.app_dir, exist_ok=True)
        self.license_file = os.path.join(self.app_dir, "license.json")

    def _safe_text(self, value):
        if value is None:
            return ""
        return str(value)

    def _sha256(self, text):
        raw = self._safe_text(text).encode("utf-8")
        return hashlib.sha256(raw).hexdigest().upper()

    def _read_machine_guid(self):
        if winreg is None:
            return ""
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Microsoft\Cryptography")
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
            return str(value).strip()
        except Exception:
            return ""

    def _looks_like_device_id(self, value):
        if value is None:
            return False
        s = str(value).strip()
        if len(s) < 8 or len(s) > 128:
            return False
        if s.upper() in ("NONE", "NULL", "UNKNOWN", "DEVICE_ID"):
            return False
        return re.match(r"^[A-Za-z0-9_:\-.]+$", s) is not None

    def _read_saved_override(self):
        try:
            if os.path.exists(self.license_file):
                with open(self.license_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                v = state.get("device_id_override", "")
                if self._looks_like_device_id(v):
                    return str(v).strip()
        except (OSError, ValueError, TypeError):
            return ""
        return ""

    def _legacy_qgis_compatible_device_id(self):
        machine_guid = self._read_machine_guid()
        hostname = socket.gethostname()
        mac_dec = str(uuid.getnode())
        try:
            mac_hex = ("%012X" % uuid.getnode())
        except Exception:
            mac_hex = mac_dec
        try:
            username = getpass.getuser()
        except Exception:
            username = ""

        seeds = []
        if machine_guid:
            seeds.extend([
                machine_guid,
                machine_guid.lower(),
                machine_guid.upper(),
                "%s|%s|%s" % (machine_guid, hostname, mac_dec),
                "%s|%s|%s" % (hostname, mac_dec, machine_guid),
                "RUANG_SPASIAL|%s" % machine_guid,
                "RUANG_SPASIAL_DEVICE|%s" % machine_guid
            ])
        seeds.extend([
            "%s|%s" % (hostname, mac_dec),
            "%s|%s|%s" % (hostname, username, mac_dec),
            "%s|%s" % (hostname, mac_hex)
        ])
        for seed in seeds:
            if seed:
                return self._sha256(seed)[0:32]
        return self._sha256("RUANG_SPASIAL_DEVICE|UNKNOWN")[0:32]

    def _read_active_saved_device_id(self):
        """
        If ArcMap/TBX has already activated this product and saved the Device ID
        in the shared license file, QGIS follows the same Device ID so the same
        ETFAR activation code stays consistent across ArcMap and QGIS.
        """
        try:
            if os.path.exists(self.license_file):
                with open(self.license_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                active = bool(state.get("activated", False)) or bool(
                    state.get("activation_code", ""))
                product_ok = str(state.get("product_code", "")
                                 ).upper() in ("", PRODUCT_CODE)
                v = state.get("device_id", "")
                if active and product_ok and self._looks_like_device_id(v):
                    return str(v).strip()
        except (OSError, ValueError, TypeError):
            return ""
        return ""

    def get_device_id(self):
        override = self._read_saved_override()
        if override:
            return override
        active_saved = self._read_active_saved_device_id()
        if active_saved:
            return active_saved
        return self._legacy_qgis_compatible_device_id()

    def request_url(self):
        params = {
            "device_id": self.get_device_id(),
            "plugin": PRODUCT_CODE,
            "product_code": PRODUCT_CODE,
            "product_name": PRODUCT_NAME
        }
        return REQUEST_URL + "?" + urllib.parse.urlencode(params)

    def open_request_url(self):
        webbrowser.open(self.request_url())

    def _default_state(self):
        return {
            "product": PRODUCT_NAME,
            "product_code": PRODUCT_CODE,
            "device_id": self.get_device_id(),
            "activated": False,
            "activation_code": "",
            "device_id_override": "",
            "trial_used": 0,
            "last_status": "TRIAL"
        }

    def load_state(self):
        if not os.path.exists(self.license_file):
            return self._default_state()
        try:
            with open(self.license_file, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = self._default_state()
        if not isinstance(state, dict):
            state = self._default_state()
        state.setdefault("product", PRODUCT_NAME)
        state.setdefault("product_code", PRODUCT_CODE)
        state.setdefault("device_id", self.get_device_id())
        state.setdefault("activated", False)
        state.setdefault("activation_code", "")
        state.setdefault("device_id_override", "")
        state.setdefault("trial_used", 0)
        state.setdefault("last_status", "TRIAL")
        return state

    def save_state(self, state):
        state["product"] = PRODUCT_NAME
        state["product_code"] = PRODUCT_CODE
        state["device_id"] = self.get_device_id()
        os.makedirs(self.app_dir, exist_ok=True)
        temporary = self.license_file + ".tmp"
        with open(temporary, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(temporary, self.license_file)

    def reset_activation_for_testing(self):
        state = self.load_state()
        state["activated"] = False
        state["activation_code"] = ""
        state["last_status"] = "TRIAL" if self.trial_remaining(
        ) > 0 else "TRIAL_EXPIRED"
        self.save_state(state)

    def trial_used(self):
        try:
            return int(self.load_state().get("trial_used", 0))
        except Exception:
            return 0

    def trial_remaining(self):
        return max(0, TRIAL_LIMIT - self.trial_used())

    def is_activated_local(self):
        state = self.load_state()
        product_ok = str(state.get("product_code", "")).upper() == PRODUCT_CODE
        return product_ok and bool(
            state.get(
                "activated",
                False)) and bool(
            state.get(
                "activation_code",
                ""))

    def _normalize_code(self, code):
        if code is None:
            return ""
        return str(code).strip().upper().replace("-", "").replace(" ", "")

    def _local_expected_codes(self):
        device_id = self.get_device_id()
        seeds = [
            "RUANG_SPASIAL|%s|%s" % (PRODUCT_CODE, device_id),
            "RUANG_SPASIAL|%s|%s" % (PRODUCT_NAME, device_id),
            "%s|%s|RUANG_SPASIAL" % (device_id, PRODUCT_CODE),
            "%s|%s" % (device_id, PRODUCT_CODE),
            "%s|%s" % (PRODUCT_CODE, device_id)
        ]
        codes = []
        for seed in seeds:
            digest = self._sha256(seed)
            codes.append(digest[0:20])
            codes.append(digest[0:16])
            codes.append(digest[0:12])
        return list(set(codes))

    def _is_licensehub_fixed_etf_code(self, code):
        raw = str(code or "").strip().upper()
        compact = self._normalize_code(raw)
        valid_prefixes = [PRODUCT_CODE] + list(LEGACY_PRODUCT_CODES)
        for prefix in valid_prefixes:
            if raw == prefix or compact == prefix:
                return True
            if raw.startswith(prefix + "-") and len(raw) >= 8:
                return True
            if compact.startswith(prefix) and len(compact) >= 8:
                return True
        return False

    def _post_json(self, url, payload, timeout=8):
        return request_json(
            "POST",
            url,
            payload,
            timeout=timeout,
            user_agent="ExelToFeature-QGIS/" + PLUGIN_VERSION,
        )

    def _get_json(self, url, params, timeout=5):
        return request_json(
            "GET",
            url,
            params,
            timeout=timeout,
            user_agent="ExelToFeature-QGIS/" + PLUGIN_VERSION,
        )

    def _is_404_error(self, msg):
        msg = str(msg or "").lower()
        return "404" in msg or "not found" in msg

    def _friendly_server_message(self, msg):
        if self._is_404_error(msg):
            return (
                "The license synchronization endpoint is not available on the License Hub server. "
                "Approved status from the website cannot be read automatically by QGIS yet. "
                "Enter the ETFAR activation code received from the License Hub page.")
        return msg or "License status could not be confirmed from the server."

    def _status_from_response(self, data):
        if has_denial(data):
            return False, "License is inactive or pending."
        if not isinstance(data, dict):
            return None, ""
        msg = (data.get("message") or data.get("detail") or data.get("msg") or
               data.get("pesan") or data.get("keterangan") or "")
        raw_status = (data.get("status") or data.get("license_status") or
                      data.get("state") or data.get("approval_status") or
                      data.get("request_status") or data.get("activation_status") or
                      data.get("lisensi_status") or "")
        status = str(raw_status).strip().lower()
        for key in ("license", "data", "result", "request", "activation"):
            nested = data.get(key)
            if isinstance(nested, dict):
                ok_nested, msg_nested = self._status_from_response(nested)
                if ok_nested is not None:
                    return ok_nested, msg_nested or msg
        inactive_words = (
            "revoked", "rejected", "disabled", "inactive", "expired",
            "blocked", "nonactive", "nonaktif", "ditolak", "kadaluarsa",
            "expired_license", "deactivated"
        )
        active_words = (
            "active", "approved", "valid", "success", "activated", "aktif",
            "acc", "accepted", "approve", "disetujui", "diterima", "lunas"
        )
        if data.get("revoked") is True or data.get(
                "disabled") is True or data.get("blocked") is True:
            return False, msg or "License has been deactivated."
        if status in inactive_words:
            return False, msg or "License is not active."
        for field in (
            "valid",
            "active",
            "is_active",
            "approved",
            "ok",
            "success",
                "activated"):
            if data.get(field) is True:
                return True, msg or "License is active."
        if status in active_words:
            return True, msg or "License is active."
        for field in ("valid", "active", "is_active", "approved", "ok", "success"):
            if data.get(field) is False:
                return False, msg or "Activation code/license is not valid."
        return None, msg

    def activate(self, activation_code):
        code = self._normalize_code(activation_code)
        if not code:
            return False, "Enter the activation code first."
        payload = {
            "product": PRODUCT_CODE,
            "product_code": PRODUCT_CODE,
            "product_name": PRODUCT_NAME,
            "plugin": PRODUCT_CODE,
            "tool": PRODUCT_NAME,
            "device_id": self.get_device_id(),
            "activation_code": code,
            "code": code
        }
        endpoints = ["/api/license/validate"]
        last_msg = ""
        for ep in endpoints:
            data, err = self._post_json(LICENSE_API_BASE + ep, payload)
            if data is None:
                last_msg = err or last_msg
                continue
            ok, msg = self._status_from_response(data)
            if ok is True:
                state = self.load_state()
                state["activated"] = True
                state["activation_code"] = code
                state["last_status"] = "ACTIVE"
                self.save_state(state)
                return True, msg or "Activation successful."
            if ok is False:
                return False, msg or "Activation code is not valid."
            last_msg = msg or last_msg

        # Strict License Hub rule:
        # Do not activate from the local ETFAR code pattern alone.
        # The plugin becomes Active only when the website/API confirms that
        # this Device ID + Product Code + Activation Code is active/approved.
        if last_msg:
            return False, (
                "Activation code could not be verified by License Hub. "
                + self._friendly_server_message(last_msg)
            )
        return False, (
            "License is not active. Make sure the ETFAR license has been approved "
            "in License Hub for this Device ID before activating the plugin."
        )

    def _save_server_active(self, data, fallback_code="SERVER_APPROVED"):
        state = self.load_state()
        code = ""
        if isinstance(data, dict):
            code = data.get("activation_code") or data.get(
                "license_code") or data.get("code") or data.get("key") or ""
            for key in ("license", "data", "result", "activation"):
                nested = data.get(key)
                if isinstance(nested, dict):
                    code = code or nested.get("activation_code") or nested.get(
                        "license_code") or nested.get("code") or nested.get("key") or ""
        state["activated"] = True
        state["activation_code"] = self._normalize_code(code) or fallback_code
        state["last_status"] = "ACTIVE_SERVER"
        self.save_state(state)

    def refresh_activation_from_server(self):
        payload = {
            "product": PRODUCT_CODE,
            "product_code": PRODUCT_CODE,
            "product_name": PRODUCT_NAME,
            "plugin": PRODUCT_CODE,
            "tool": PRODUCT_NAME,
            "device_id": self.get_device_id(),
            "device": self.get_device_id()
        }
        endpoints = ["/api/license/status"]
        last_msg = ""
        for ep in endpoints:
            url = LICENSE_API_BASE + ep
            data, err = self._post_json(url, payload, timeout=5)
            if data is not None:
                ok, msg = self._status_from_response(data)
                if ok is True:
                    self._save_server_active(data)
                    return True, msg or "License is active based on website data."
                if ok is False:
                    state = self.load_state()
                    state["activated"] = False
                    state["last_status"] = "INACTIVE_SERVER"
                    self.save_state(state)
                    return False, msg or "License is not active or has not been approved."
                last_msg = msg or last_msg
            else:
                last_msg = err or last_msg
        return None, self._friendly_server_message(last_msg)

    def check_server_status(self):
        state = self.load_state()
        code = self._normalize_code(state.get("activation_code", ""))
        if not code or code == "SERVER_APPROVED":
            return self.refresh_activation_from_server()
        payload = {
            "product": PRODUCT_CODE,
            "product_code": PRODUCT_CODE,
            "product_name": PRODUCT_NAME,
            "plugin": PRODUCT_CODE,
            "tool": PRODUCT_NAME,
            "device_id": self.get_device_id(),
            "activation_code": code,
            "code": code
        }
        endpoints = ["/api/license/status"]
        last_msg = ""
        for ep in endpoints:
            data, err = self._post_json(
                LICENSE_API_BASE + ep, payload, timeout=5)
            if data is None:
                last_msg = err or last_msg
                continue
            ok, msg = self._status_from_response(data)
            if ok is True:
                return True, msg or "License is active."
            if ok is False:
                state["activated"] = False
                state["last_status"] = "REVOKED"
                self.save_state(state)
                return False, msg or "License is no longer active."
            last_msg = msg or last_msg
        return None, self._friendly_server_message(last_msg)

    def can_run(self):
        if self.is_activated_local():
            online_ok, online_msg = self.check_server_status()
            if online_ok is True:
                return True, "License is active."
            return False, online_msg or (
                "The active license could not be verified online."
            )
        server_ok, server_msg = self.refresh_activation_from_server()
        if server_ok is True:
            return True, "License is active."
        if self.trial_remaining() > 0:
            return True, "Trial mode. Remaining trial: %s of %s." % (
                self.trial_remaining(), TRIAL_LIMIT)
        return False, (
            "Trial has expired. Please activate the license.\n\n"
            "Device ID: %s\nActivation request: %s"
        ) % (self.get_device_id(), self.request_url())

    def consume_trial_for_run(self):
        state = self.load_state()
        if state.get("activated", False):
            return True
        try:
            used = int(state.get("trial_used", 0))
        except Exception:
            used = 0
        if used >= TRIAL_LIMIT:
            state["last_status"] = "TRIAL_EXPIRED"
            self.save_state(state)
            return False
        state["trial_used"] = used + 1
        state["last_status"] = "TRIAL" if state["trial_used"] < TRIAL_LIMIT else "TRIAL_EXPIRED"
        self.save_state(state)
        return True

    def status_text(self):
        state = self.load_state()
        last_status = str(state.get("last_status", "")).upper()

        if self.is_activated_local():
            return "Active - Product ETFAR - Device ID: %s" % self.get_device_id()

        if last_status in (
            "REVOKED",
            "INACTIVE_SERVER",
            "DEACTIVATED",
            "DISABLED",
                "BLOCKED"):
            return "Deactivated - License is not active"

        remaining = self.trial_remaining()
        if remaining > 0:
            return "Trial - %s of %s uses remaining" % (remaining, TRIAL_LIMIT)

        return "Expired - Trial limit reached"
