"""Drop-in replacement for UptimeKumaApi targeting Uptime Kuma v2.x.

The uptime-kuma-api library (v1.2.1) only supports Kuma v1.21.3-1.23.2.
Kuma v2.0.2 never sends Socket.IO acknowledgements for *any* event —
``login``, ``add``, ``editMonitor``, ``deleteMonitor``, ``getTags``, etc.
This means ``sio.call()`` (which blocks waiting for an ack) always times
out.  This module uses ``sio.emit`` with a callback + ``threading.Event``
for all operations, returning ``None`` when the server doesn't ack (which
is the normal case — the operation still succeeds server-side).
"""

import logging
import threading

import socketio

logger = logging.getLogger(__name__)


class KumaV2Api:
    """Socket.IO client implementing the same method signatures used by all
    tool files in this project."""

    def __init__(self, url, timeout=30):
        self._url = url.rstrip("/")
        self._timeout = timeout
        self._credentials: dict = {}

        # Event caches
        self._event_cache: dict = {}
        self._avg_ping: dict = {}
        self._uptime: dict = {}
        self._cert_info: dict = {}

        # Synchronisation
        self._login_event = threading.Event()
        self._call_lock = threading.Lock()

        # Socket.IO client
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_delay=1,
            reconnection_delay_max=30,
            logger=False,
        )

        self._register_handlers()
        self.sio.connect(self._url, wait_timeout=self._timeout)

    # ── Event handlers ────────────────────────────────────────────────

    def _register_handlers(self):
        @self.sio.on("monitorList")
        def _on_monitor_list(data):
            if isinstance(data, dict):
                existing = self._event_cache.get("monitorList", {})
                existing.update(data)
                self._event_cache["monitorList"] = existing
            else:
                self._event_cache["monitorList"] = data
            self._login_event.set()

        @self.sio.on("notificationList")
        def _on_notification_list(data):
            self._event_cache["notificationList"] = data

        @self.sio.on("statusPageList")
        def _on_status_page_list(data):
            if isinstance(data, dict):
                existing = self._event_cache.get("statusPageList", {})
                existing.update(data)
                self._event_cache["statusPageList"] = existing
            else:
                self._event_cache["statusPageList"] = data

        @self.sio.on("maintenanceList")
        def _on_maintenance_list(data):
            if isinstance(data, dict):
                existing = self._event_cache.get("maintenanceList", {})
                existing.update(data)
                self._event_cache["maintenanceList"] = existing
            else:
                self._event_cache["maintenanceList"] = data

        @self.sio.on("info")
        def _on_info(data):
            self._event_cache["info"] = data

        @self.sio.on("avgPing")
        def _on_avg_ping(monitor_id, value):
            self._avg_ping[monitor_id] = value

        @self.sio.on("uptime")
        def _on_uptime(key, value):
            self._uptime[key] = value

        @self.sio.on("certInfo")
        def _on_cert_info(monitor_id, data):
            self._cert_info[monitor_id] = data

        @self.sio.on("disconnect")
        def _on_disconnect():
            self._login_event.clear()

        @self.sio.on("connect")
        def _on_connect():
            if self._credentials:
                self._do_login()

    # ── Login / connection ────────────────────────────────────────────

    def _do_login(self):
        """Emit login with a no-op callback so the packet includes an ack ID.

        Kuma v2 ignores login events that lack an ack callback in the
        Socket.IO packet.  The server never actually sends the ack back,
        so we rely on the ``monitorList`` broadcast as proof of success.
        """
        self._login_event.clear()
        _noop = lambda *a: None  # noqa: E731
        if self._credentials.get("_by_token"):
            self.sio.emit(
                "loginByToken", self._credentials["token"], callback=_noop,
            )
        else:
            self.sio.emit("login", {
                "username": self._credentials.get("username", ""),
                "password": self._credentials.get("password", ""),
                "token": self._credentials.get("token", ""),
            }, callback=_noop)

    def _wait_for_login(self):
        if not self._login_event.wait(timeout=self._timeout):
            raise TimeoutError(
                f"Login timed out after {self._timeout}s - "
                "no monitorList received from server"
            )

    def login(self, username, password, token=""):
        self._credentials = {
            "username": username,
            "password": password,
            "token": token,
        }
        self._do_login()
        self._wait_for_login()

    def login_by_token(self, token):
        self._credentials = {"token": token, "_by_token": True}
        self._do_login()
        self._wait_for_login()

    def disconnect(self):
        try:
            self.sio.disconnect()
        except Exception:
            pass

    # ── Internal call helper ──────────────────────────────────────────

    def _call(self, event, data=None, timeout=None):
        """Emit *event* with optional *data* and wait for an optional ack.

        Kuma v2 never sends Socket.IO acknowledgements, so we use
        ``sio.emit`` with a callback and ``threading.Event``.  If the
        ack never arrives within *timeout* seconds the operation is
        assumed to have succeeded and ``None`` is returned.

        If the login state has been lost (e.g. the server recycled the
        session), attempt a single re-login before giving up.
        """
        t = timeout or self._timeout
        if not self._login_event.wait(timeout=t):
            if self._credentials:
                self._do_login()
                if not self._login_event.wait(timeout=t):
                    raise TimeoutError("Not logged in")
            else:
                raise TimeoutError("Not logged in")
        with self._call_lock:
            result_holder = {}
            done = threading.Event()

            def on_ack(*args):
                result_holder["value"] = args[0] if len(args) == 1 else args
                done.set()

            self.sio.emit(event, data, callback=on_ack)
            done.wait(timeout=t)
            return result_holder.get("value")

    @staticmethod
    def _unwrap(result):
        """Raise on ``{ok: false}`` ack payloads.

        When *result* is ``None`` (Kuma v2 never acked) the operation is
        assumed to have succeeded — return ``{"ok": True}``.
        """
        if result is None:
            return {"ok": True}
        if isinstance(result, dict) and not result.get("ok", True):
            raise RuntimeError(result.get("msg", "Unknown error from server"))
        return result

    # ── Event-cached: monitors ────────────────────────────────────────

    def get_monitors(self):
        data = self._event_cache.get("monitorList", {})
        if isinstance(data, dict):
            return list(data.values())
        return list(data)

    # ── Event-cached: notifications ───────────────────────────────────

    def get_notifications(self):
        return list(self._event_cache.get("notificationList", []))

    def get_notification(self, id):
        for n in self.get_notifications():
            if n.get("id") == id:
                return n
        raise ValueError(f"Notification with id {id} not found")

    # ── Event-cached: status pages ────────────────────────────────────

    def get_status_pages(self):
        data = self._event_cache.get("statusPageList", {})
        if isinstance(data, dict):
            return list(data.values())
        return list(data)

    # ── Event-cached: maintenance ─────────────────────────────────────

    def get_maintenances(self):
        data = self._event_cache.get("maintenanceList", {})
        if isinstance(data, dict):
            return list(data.values())
        return list(data)

    # ── Event-cached: system / per-monitor stats ──────────────────────

    def info(self):
        return self._event_cache.get("info", {})

    def avg_ping(self, id):
        return self._avg_ping.get(id, self._avg_ping.get(str(id)))

    def uptime(self, id):
        result = {}
        prefix = f"{id}_"
        for key, val in list(self._uptime.items()):
            k = str(key)
            if k.startswith(prefix):
                result[k[len(prefix):]] = val
            elif k == str(id):
                result[k] = val
        return result or self._uptime.get(id, self._uptime.get(str(id)))

    def cert_info(self, id):
        return self._cert_info.get(id, self._cert_info.get(str(id)))

    # ── Call-based: monitors ──────────────────────────────────────────

    def get_monitor(self, id):
        r = self._call("getMonitor", id)
        if isinstance(r, dict) and "monitor" in r:
            return r["monitor"]
        return r

    def add_monitor(self, **kwargs):
        return self._unwrap(self._call("add", kwargs))

    def edit_monitor(self, id, **kwargs):
        existing = self.get_monitor(id)
        existing.update(kwargs)
        existing["id"] = id
        return self._unwrap(self._call("editMonitor", existing))

    def delete_monitor(self, id):
        return self._unwrap(self._call("deleteMonitor", id))

    def pause_monitor(self, id):
        return self._unwrap(self._call("pauseMonitor", id))

    def resume_monitor(self, id):
        return self._unwrap(self._call("resumeMonitor", id))

    def get_monitor_beats(self, id, hours):
        r = self._call("getMonitorBeats", (id, hours))
        if isinstance(r, dict) and "data" in r:
            return r["data"]
        return r

    # ── Call-based: tags ──────────────────────────────────────────────

    def get_tags(self):
        r = self._call("getTags")
        if isinstance(r, dict) and "tags" in r:
            return r["tags"]
        return r

    def get_tag(self, id):
        for t in self.get_tags():
            if t.get("id") == id:
                return t
        raise ValueError(f"Tag with id {id} not found")

    def add_tag(self, name, color):
        return self._unwrap(
            self._call("addTag", {"name": name, "color": color})
        )

    def edit_tag(self, id, **kwargs):
        existing = self.get_tag(id)
        existing.update(kwargs)
        existing["id"] = id
        return self._unwrap(self._call("editTag", existing))

    def delete_tag(self, id):
        return self._unwrap(self._call("deleteTag", id))

    def add_monitor_tag(self, tag_id, monitor_id, value=""):
        return self._unwrap(self._call("addMonitorTag", {
            "tag_id": tag_id,
            "monitor_id": monitor_id,
            "value": value,
        }))

    def delete_monitor_tag(self, tag_id, monitor_id, value=""):
        return self._unwrap(self._call("deleteMonitorTag", {
            "tag_id": tag_id,
            "monitor_id": monitor_id,
            "value": value,
        }))

    # ── Call-based: notifications ─────────────────────────────────────

    def add_notification(self, **kwargs):
        return self._unwrap(self._call("addNotification", (kwargs, None)))

    def edit_notification(self, id, **kwargs):
        existing = self.get_notification(id)
        merged = {**existing, **kwargs}
        return self._unwrap(self._call("addNotification", (merged, id)))

    def delete_notification(self, id):
        return self._unwrap(self._call("deleteNotification", id))

    def test_notification(self, **kwargs):
        return self._unwrap(self._call("testNotification", kwargs))

    # ── Call-based: status pages ──────────────────────────────────────

    def get_status_page(self, slug):
        r = self._call("getStatusPage", slug)
        if isinstance(r, dict) and "config" in r:
            return r["config"]
        return r

    def add_status_page(self, title, slug):
        return self._unwrap(self._call("addStatusPage", (title, slug)))

    def save_status_page(self, slug, **kwargs):
        icon = kwargs.pop("icon", "/icon.svg")
        public_group_list = kwargs.pop("publicGroupList", None)
        return self._unwrap(
            self._call("saveStatusPage", (slug, kwargs, icon, public_group_list))
        )

    def delete_status_page(self, slug):
        return self._unwrap(self._call("deleteStatusPage", slug))

    # ── Call-based: maintenance ────────────────────────────────────────

    def get_maintenance(self, id):
        r = self._call("getMaintenance", id)
        if isinstance(r, dict) and "maintenance" in r:
            return r["maintenance"]
        return r

    def add_maintenance(self, **kwargs):
        return self._unwrap(self._call("addMaintenance", kwargs))

    def edit_maintenance(self, id, **kwargs):
        existing = self.get_maintenance(id)
        existing.update(kwargs)
        existing["id"] = id
        return self._unwrap(self._call("editMaintenance", existing))

    def delete_maintenance(self, id):
        return self._unwrap(self._call("deleteMaintenance", id))

    def pause_maintenance(self, id):
        return self._unwrap(self._call("pauseMaintenance", id))

    def resume_maintenance(self, id):
        return self._unwrap(self._call("resumeMaintenance", id))

    def add_monitor_maintenance(self, id, monitors):
        return self._unwrap(
            self._call("addMonitorMaintenance", (id, monitors))
        )

    def add_status_page_maintenance(self, id, pages):
        return self._unwrap(
            self._call("addMaintenanceStatusPage", (id, pages))
        )

    # ── Call-based: system ────────────────────────────────────────────

    def get_database_size(self):
        r = self._call("getDatabaseSize")
        if isinstance(r, dict) and "size" in r:
            return r["size"]
        return r
