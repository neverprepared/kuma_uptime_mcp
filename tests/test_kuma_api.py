"""Tests for KumaV2Api custom Socket.IO client."""

import threading
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from mcp_uptime_kuma.kuma_api import KumaV2Api


@pytest.fixture
def api():
    """Create a KumaV2Api with mocked Socket.IO client (skip real connect)."""
    with patch("mcp_uptime_kuma.kuma_api.socketio.Client") as MockClient:
        mock_sio = MagicMock()
        MockClient.return_value = mock_sio
        # Capture event handlers registered via sio.on decorator
        handlers = {}

        def fake_on(event):
            def decorator(fn):
                handlers[event] = fn
                return fn
            return decorator

        mock_sio.on = fake_on
        mock_sio.connect = MagicMock()

        obj = KumaV2Api("http://localhost:3001", timeout=5)
        obj._handlers = handlers
        # Pre-set login event so _call doesn't block
        obj._login_event.set()
        yield obj


# ── Constructor / connection ────────────────────────────────────────


class TestConnection:

    def test_url_trailing_slash_stripped(self):
        with patch("mcp_uptime_kuma.kuma_api.socketio.Client") as MockClient:
            mock_sio = MagicMock()
            mock_sio.on = MagicMock(return_value=lambda fn: fn)
            MockClient.return_value = mock_sio
            obj = KumaV2Api("http://localhost:3001/", timeout=1)
            assert obj._url == "http://localhost:3001"

    def test_connect_called_on_init(self):
        with patch("mcp_uptime_kuma.kuma_api.socketio.Client") as MockClient:
            mock_sio = MagicMock()
            mock_sio.on = MagicMock(return_value=lambda fn: fn)
            MockClient.return_value = mock_sio
            KumaV2Api("http://localhost:3001", timeout=5)
            mock_sio.connect.assert_called_once_with(
                "http://localhost:3001", wait_timeout=5
            )

    def test_disconnect(self, api):
        api.disconnect()
        api.sio.disconnect.assert_called_once()

    def test_disconnect_swallows_exceptions(self, api):
        api.sio.disconnect.side_effect = Exception("already disconnected")
        api.disconnect()  # Should not raise


# ── Login ───────────────────────────────────────────────────────────


class TestLogin:

    def test_login_emits_credentials(self, api):
        api._login_event.clear()

        def fake_emit(event, data, **kwargs):
            if event == "login":
                # Simulate server sending monitorList after login
                api._login_event.set()

        api.sio.emit = fake_emit
        api.login("admin", "secret")
        assert api._credentials["username"] == "admin"
        assert api._credentials["password"] == "secret"

    def test_login_with_mfa(self, api):
        api._login_event.clear()

        def fake_emit(event, data, **kwargs):
            if event == "login":
                api._login_event.set()

        api.sio.emit = fake_emit
        api.login("admin", "secret", token="123456")
        assert api._credentials["token"] == "123456"

    def test_login_by_token_emits_token(self, api):
        api._login_event.clear()

        def fake_emit(event, data, **kwargs):
            if event == "loginByToken":
                api._login_event.set()

        api.sio.emit = fake_emit
        api.login_by_token("jwt-token-here")
        assert api._credentials["_by_token"] is True
        assert api._credentials["token"] == "jwt-token-here"

    def test_login_timeout_raises(self, api):
        api._login_event.clear()
        api._timeout = 0.1
        api.sio.emit = MagicMock()
        with pytest.raises(TimeoutError, match="Login timed out"):
            api.login("admin", "secret")

    def test_reconnect_triggers_login(self, api):
        api._credentials = {"username": "admin", "password": "secret"}
        handler = api._handlers["connect"]
        api.sio.emit = MagicMock()
        handler()
        call_args = api.sio.emit.call_args
        assert call_args[0] == ("login", {
            "username": "admin",
            "password": "secret",
            "token": "",
        })
        assert call_args[1].get("callback") is not None

    def test_disconnect_event_clears_login(self, api):
        api._login_event.set()
        handler = api._handlers["disconnect"]
        handler()
        assert not api._login_event.is_set()


# ── Event handlers / cache ──────────────────────────────────────────


class TestEventCache:

    def test_monitor_list_dict(self, api):
        handler = api._handlers["monitorList"]
        handler({"1": {"id": 1, "name": "A"}, "2": {"id": 2, "name": "B"}})
        monitors = api.get_monitors()
        assert len(monitors) == 2

    def test_monitor_list_incremental_update(self, api):
        handler = api._handlers["monitorList"]
        handler({"1": {"id": 1, "name": "A"}})
        handler({"2": {"id": 2, "name": "B"}})
        monitors = api.get_monitors()
        assert len(monitors) == 2

    def test_monitor_list_non_dict(self, api):
        handler = api._handlers["monitorList"]
        handler([{"id": 1}, {"id": 2}])
        monitors = api.get_monitors()
        assert len(monitors) == 2

    def test_notification_list(self, api):
        handler = api._handlers["notificationList"]
        handler([{"id": 1, "name": "Slack"}])
        assert len(api.get_notifications()) == 1
        assert api.get_notification(1)["name"] == "Slack"

    def test_notification_not_found(self, api):
        api._event_cache["notificationList"] = []
        with pytest.raises(ValueError, match="Notification with id 99"):
            api.get_notification(99)

    def test_status_page_list_dict(self, api):
        handler = api._handlers["statusPageList"]
        handler({"main": {"slug": "main", "title": "Main"}})
        pages = api.get_status_pages()
        assert len(pages) == 1

    def test_status_page_list_incremental(self, api):
        handler = api._handlers["statusPageList"]
        handler({"main": {"slug": "main"}})
        handler({"dev": {"slug": "dev"}})
        assert len(api.get_status_pages()) == 2

    def test_maintenance_list_dict(self, api):
        handler = api._handlers["maintenanceList"]
        handler({"1": {"id": 1, "title": "MW1"}})
        assert len(api.get_maintenances()) == 1

    def test_maintenance_list_incremental(self, api):
        handler = api._handlers["maintenanceList"]
        handler({"1": {"id": 1}})
        handler({"2": {"id": 2}})
        assert len(api.get_maintenances()) == 2

    def test_info_event(self, api):
        handler = api._handlers["info"]
        handler({"version": "2.0.2"})
        assert api.info()["version"] == "2.0.2"

    def test_avg_ping_event(self, api):
        handler = api._handlers["avgPing"]
        handler(1, 42.5)
        assert api.avg_ping(1) == 42.5

    def test_avg_ping_string_fallback(self, api):
        api._avg_ping["1"] = 42.5
        assert api.avg_ping(1) == 42.5

    def test_uptime_event(self, api):
        handler = api._handlers["uptime"]
        handler("1_24", 0.998)
        handler("1_720", 0.995)
        result = api.uptime(1)
        assert result["24"] == 0.998
        assert result["720"] == 0.995

    def test_cert_info_event(self, api):
        handler = api._handlers["certInfo"]
        handler(1, {"valid": True, "daysRemaining": 30})
        assert api.cert_info(1)["valid"] is True

    def test_cert_info_string_fallback(self, api):
        api._cert_info["1"] = {"valid": True}
        assert api.cert_info(1)["valid"] is True


# ── _call / _unwrap helpers ─────────────────────────────────────────


class TestCallHelper:

    def test_call_waits_for_login(self, api):
        api._login_event.clear()
        api._timeout = 0.1
        with pytest.raises(TimeoutError, match="Not logged in"):
            api._call("someEvent")

    def test_call_delegates_to_sio(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        result = api._call("someEvent", {"key": "val"})
        api.sio.call.assert_called_once_with("someEvent", {"key": "val"}, timeout=5)
        assert result == {"ok": True}

    def test_unwrap_ok_true(self, api):
        assert api._unwrap({"ok": True, "msg": "done"}) == {"ok": True, "msg": "done"}

    def test_unwrap_ok_false_raises(self, api):
        with pytest.raises(RuntimeError, match="Something failed"):
            api._unwrap({"ok": False, "msg": "Something failed"})

    def test_unwrap_no_ok_field(self, api):
        # No "ok" key defaults to True
        assert api._unwrap({"data": 123}) == {"data": 123}

    def test_unwrap_non_dict(self, api):
        assert api._unwrap("plain string") == "plain string"
        assert api._unwrap(42) == 42


# ── Call-based: monitors ────────────────────────────────────────────


class TestMonitorCalls:

    def test_get_monitor_unwraps(self, api):
        api.sio.call = MagicMock(return_value={"monitor": {"id": 1, "name": "A"}})
        result = api.get_monitor(1)
        assert result == {"id": 1, "name": "A"}
        api.sio.call.assert_called_once_with("getMonitor", 1, timeout=5)

    def test_get_monitor_raw_fallback(self, api):
        api.sio.call = MagicMock(return_value={"id": 1, "name": "A"})
        result = api.get_monitor(1)
        assert result == {"id": 1, "name": "A"}

    def test_add_monitor(self, api):
        api.sio.call = MagicMock(return_value={"ok": True, "monitorID": 3})
        result = api.add_monitor(type="http", name="Test", url="https://test.com")
        api.sio.call.assert_called_once_with(
            "add", {"type": "http", "name": "Test", "url": "https://test.com"}, timeout=5
        )
        assert result["monitorID"] == 3

    def test_edit_monitor_merges(self, api):
        api.sio.call = MagicMock(side_effect=[
            {"monitor": {"id": 1, "name": "Old", "url": "https://old.com"}},
            {"ok": True, "monitorID": 1},
        ])
        result = api.edit_monitor(1, name="New")
        edit_call = api.sio.call.call_args_list[1]
        assert edit_call[0][0] == "editMonitor"
        assert edit_call[0][1]["name"] == "New"
        assert edit_call[0][1]["url"] == "https://old.com"
        assert edit_call[0][1]["id"] == 1

    def test_delete_monitor(self, api):
        api.sio.call = MagicMock(return_value={"ok": True, "msg": "Deleted"})
        result = api.delete_monitor(1)
        api.sio.call.assert_called_once_with("deleteMonitor", 1, timeout=5)

    def test_pause_monitor(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        api.pause_monitor(1)
        api.sio.call.assert_called_once_with("pauseMonitor", 1, timeout=5)

    def test_resume_monitor(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        api.resume_monitor(1)
        api.sio.call.assert_called_once_with("resumeMonitor", 1, timeout=5)

    def test_get_monitor_beats_unwraps(self, api):
        api.sio.call = MagicMock(return_value={"data": [{"status": 1}]})
        result = api.get_monitor_beats(1, 24)
        assert result == [{"status": 1}]
        api.sio.call.assert_called_once_with("getMonitorBeats", (1, 24), timeout=5)


# ── Call-based: tags ────────────────────────────────────────────────


class TestTagCalls:

    def test_get_tags_unwraps(self, api):
        api.sio.call = MagicMock(return_value={"tags": [{"id": 1, "name": "prod"}]})
        result = api.get_tags()
        assert result == [{"id": 1, "name": "prod"}]

    def test_get_tag_by_id(self, api):
        api.sio.call = MagicMock(return_value={"tags": [
            {"id": 1, "name": "prod"},
            {"id": 2, "name": "staging"},
        ]})
        assert api.get_tag(2)["name"] == "staging"

    def test_get_tag_not_found(self, api):
        api.sio.call = MagicMock(return_value={"tags": []})
        with pytest.raises(ValueError, match="Tag with id 99"):
            api.get_tag(99)

    def test_add_tag(self, api):
        api.sio.call = MagicMock(return_value={"ok": True, "tag": {"id": 3}})
        api.add_tag("critical", "#ef4444")
        api.sio.call.assert_called_once_with(
            "addTag", {"name": "critical", "color": "#ef4444"}, timeout=5
        )

    def test_edit_tag_merges(self, api):
        api.sio.call = MagicMock(side_effect=[
            {"tags": [{"id": 1, "name": "prod", "color": "#dc2626"}]},
            {"ok": True},
        ])
        api.edit_tag(1, name="production")
        edit_call = api.sio.call.call_args_list[1]
        assert edit_call[0][1]["name"] == "production"
        assert edit_call[0][1]["color"] == "#dc2626"

    def test_delete_tag(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        api.delete_tag(1)
        api.sio.call.assert_called_once_with("deleteTag", 1, timeout=5)

    def test_add_monitor_tag(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        api.add_monitor_tag(tag_id=1, monitor_id=2, value="primary")
        api.sio.call.assert_called_once_with("addMonitorTag", {
            "tag_id": 1, "monitor_id": 2, "value": "primary",
        }, timeout=5)

    def test_delete_monitor_tag(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        api.delete_monitor_tag(tag_id=1, monitor_id=2)
        api.sio.call.assert_called_once_with("deleteMonitorTag", {
            "tag_id": 1, "monitor_id": 2, "value": "",
        }, timeout=5)


# ── Call-based: notifications ───────────────────────────────────────


class TestNotificationCalls:

    def test_add_notification(self, api):
        api.sio.call = MagicMock(return_value={"ok": True, "id": 2})
        api.add_notification(name="Test", type="slack", slackwebhookURL="https://...")
        api.sio.call.assert_called_once_with("addNotification", (
            {"name": "Test", "type": "slack", "slackwebhookURL": "https://..."},
            None,
        ), timeout=5)

    def test_edit_notification_merges(self, api):
        api._event_cache["notificationList"] = [
            {"id": 1, "name": "Slack", "type": "slack", "slackwebhookURL": "old"},
        ]
        api.sio.call = MagicMock(return_value={"ok": True})
        api.edit_notification(1, name="Updated Slack")
        call_args = api.sio.call.call_args[0]
        assert call_args[0] == "addNotification"
        payload, nid = call_args[1]
        assert nid == 1
        assert payload["name"] == "Updated Slack"
        assert payload["slackwebhookURL"] == "old"

    def test_delete_notification(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        api.delete_notification(1)
        api.sio.call.assert_called_once_with("deleteNotification", 1, timeout=5)

    def test_test_notification(self, api):
        api.sio.call = MagicMock(return_value={"ok": True, "msg": "Sent"})
        api.test_notification(name="Test", type="slack")
        api.sio.call.assert_called_once_with("testNotification", {
            "name": "Test", "type": "slack",
        }, timeout=5)


# ── Call-based: status pages ────────────────────────────────────────


class TestStatusPageCalls:

    def test_get_status_page_unwraps(self, api):
        api.sio.call = MagicMock(return_value={
            "config": {"slug": "main", "title": "Main Status"},
        })
        result = api.get_status_page("main")
        assert result["slug"] == "main"

    def test_add_status_page(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        api.add_status_page("New Page", "new-page")
        api.sio.call.assert_called_once_with(
            "addStatusPage", ("New Page", "new-page"), timeout=5
        )

    def test_save_status_page(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        api.save_status_page("main", title="Updated", published=True)
        call_args = api.sio.call.call_args[0]
        assert call_args[0] == "saveStatusPage"
        slug, config, icon, groups = call_args[1]
        assert slug == "main"
        assert config["title"] == "Updated"
        assert icon == "/icon.svg"
        assert groups is None

    def test_save_status_page_with_groups(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        group_list = [{"name": "Services", "monitorList": [{"id": 1}]}]
        api.save_status_page("main", publicGroupList=group_list)
        call_args = api.sio.call.call_args[0]
        _, _, _, groups = call_args[1]
        assert groups == group_list

    def test_delete_status_page(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        api.delete_status_page("main")
        api.sio.call.assert_called_once_with("deleteStatusPage", "main", timeout=5)


# ── Call-based: maintenance ─────────────────────────────────────────


class TestMaintenanceCalls:

    def test_get_maintenance_unwraps(self, api):
        api.sio.call = MagicMock(return_value={
            "maintenance": {"id": 1, "title": "MW1"},
        })
        result = api.get_maintenance(1)
        assert result["title"] == "MW1"

    def test_add_maintenance(self, api):
        api.sio.call = MagicMock(return_value={"ok": True, "maintenanceID": 2})
        api.add_maintenance(title="Deploy", strategy="manual")
        api.sio.call.assert_called_once_with("addMaintenance", {
            "title": "Deploy", "strategy": "manual",
        }, timeout=5)

    def test_edit_maintenance_merges(self, api):
        api.sio.call = MagicMock(side_effect=[
            {"maintenance": {"id": 1, "title": "Old", "strategy": "manual"}},
            {"ok": True},
        ])
        api.edit_maintenance(1, title="New")
        edit_call = api.sio.call.call_args_list[1]
        assert edit_call[0][1]["title"] == "New"
        assert edit_call[0][1]["strategy"] == "manual"
        assert edit_call[0][1]["id"] == 1

    def test_delete_maintenance(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        api.delete_maintenance(1)
        api.sio.call.assert_called_once_with("deleteMaintenance", 1, timeout=5)

    def test_pause_maintenance(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        api.pause_maintenance(1)
        api.sio.call.assert_called_once_with("pauseMaintenance", 1, timeout=5)

    def test_resume_maintenance(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        api.resume_maintenance(1)
        api.sio.call.assert_called_once_with("resumeMaintenance", 1, timeout=5)

    def test_add_monitor_maintenance(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        api.add_monitor_maintenance(1, [{"id": 2}, {"id": 3}])
        api.sio.call.assert_called_once_with(
            "addMonitorMaintenance", (1, [{"id": 2}, {"id": 3}]), timeout=5
        )

    def test_add_status_page_maintenance(self, api):
        api.sio.call = MagicMock(return_value={"ok": True})
        api.add_status_page_maintenance(1, [{"id": 10}])
        api.sio.call.assert_called_once_with(
            "addMaintenanceStatusPage", (1, [{"id": 10}]), timeout=5
        )


# ── Call-based: system ──────────────────────────────────────────────


class TestSystemCalls:

    def test_get_database_size_unwraps(self, api):
        api.sio.call = MagicMock(return_value={"size": 1048576})
        result = api.get_database_size()
        assert result == 1048576

    def test_get_database_size_raw_fallback(self, api):
        api.sio.call = MagicMock(return_value={"data": 999})
        result = api.get_database_size()
        assert result == {"data": 999}
