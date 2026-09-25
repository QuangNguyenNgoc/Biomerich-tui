"""
AppController — Business logic layer extracted from the old main.py.

This class wraps all core module interactions, replacing the ~100 @eel.expose
functions from main.py. The TUI screens call methods on this controller
instead of RPC endpoints.
"""

import sys
import os
import time
import threading
import atexit
from typing import Callable, Any, Optional


class AppController:
    """Central controller bridging TUI screens to core business logic."""

    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}
        self._hotkey_handle = None
        self._hotkey_lock = threading.Lock()
        self._mode_hotkey_handle = None
        self._mode_hotkey_lock = threading.Lock()
        self._maintenance_lock = threading.Lock()
        self._maintenance_active = False

        # --- Initialize core ---
        from core import ConfigManager, MacroEngine
        from core import status_events, activity_log, account_timeline

        self.config = ConfigManager()

        # Setup logging
        try:
            from core import applog

            applog.setup(self.config.dir)
        except Exception:
            pass

        # Resolve existing Roblox window bindings
        try:
            from core import win_windows

            win_windows.resolve_accounts(self.config.accounts)
            self.config.save()
        except Exception as e:
            print(f"[Controller] Window restore failed: {e}")

        # Create engine
        self.engine = MacroEngine(self.config)

        # Wire engine callbacks to our event system
        self.engine.rare_ping_notifier = lambda p: self._emit("rare_ping_blocked", p)
        self.engine.rare_ping_resolver = lambda i: self._emit("rare_ping_resolved", i)
        self.engine.biome_health_notifier = lambda p: self._emit(
            "biome_health_warning", p
        )
        self.engine.biome_health_resolver = lambda a: self._emit(
            "biome_health_resolved", a
        )

        # Wire activity log providers
        activity_log.account_provider = lambda: self.engine.automation.current_account
        activity_log.account_id_provider = self._resolve_account_id
        activity_log.timeline_sink = account_timeline.record_activity

        # --- Performance subsystems ---
        from core import ram_trim, throttle as throttle_mod
        from core import performance_benchmark as perf_bench_mod

        self.ram_trimmer = ram_trim.RamTrimmer(
            self.config, is_engine_running=lambda: self.engine.running
        )
        self.throttler = throttle_mod.ThrottleEngine(
            self.config, is_engine_running=lambda: self.engine.running
        )
        self.engine.anti_afk.set_throttler(self.throttler)
        self.engine.automation.set_throttler(self.throttler)
        self.benchmark = perf_bench_mod.PerformanceBenchmark(
            self.config, self.throttler
        )

        # --- Roblox subsystems ---
        from core import roblox_auth
        from core import webhooks as _webhooks

        self._roblox_auth = roblox_auth
        self._webhooks = _webhooks

        # --- Register atexit handlers ---
        atexit.register(self.throttler.stop)
        atexit.register(self.benchmark.stop)
        atexit.register(roblox_auth.stop_account_launch_cleanup)
        atexit.register(roblox_auth.release_multi_instance)
        atexit.register(lambda: _webhooks.flush(8.0))
        atexit.register(self.config.save_on_shutdown)

        # --- Background profile refresh ---
        self._refresh_missing_profiles()

        print(f"[SolRich_TUI] Config folder: {self.config.dir}")

    # ── Event System ──────────────────────────────────────────────

    def on(self, event: str, callback: Callable) -> None:
        """Subscribe to an event."""
        self._listeners.setdefault(event, []).append(callback)

    def _emit(self, event: str, *args) -> None:
        """Emit an event to all subscribers."""
        for cb in self._listeners.get(event, []):
            try:
                cb(*args)
            except Exception as e:
                print(f"[Event] Error in {event} handler: {e}")

    # ── Engine Control ────────────────────────────────────────────

    def is_engine_running(self) -> bool:
        return self.engine.running

    def get_engine_mode(self) -> str:
        return self.config.automation.get("mode", "idle")

    def start_engine(self) -> dict:
        with self._maintenance_lock:
            if self._maintenance_active:
                return {
                    "ok": False,
                    "errors": ["Maintenance is running. Please wait."],
                    "running": False,
                }
            result = self.engine.start()
            if result.get("ok"):
                self._emit("engine_started", result)
            return result

    def stop_engine(self) -> dict:
        result = self.engine.stop()
        self._emit("engine_stopped", result)
        return result

    def set_engine_mode(self, mode: str) -> None:
        allowed = ("idle", "automation", "eden")
        if mode in allowed:
            self.config.automation["mode"] = mode
            self.config.save()

    # ── State Getters ─────────────────────────────────────────────

    def get_state(self) -> dict:
        """Get the full application state (config + engine state)."""
        return self.config.state()

    def get_live_accounts(self) -> list:
        """Merge static account config with live runtime data (online, biome)."""
        state_accounts = self.config.state().get("accounts", [])

        # Get live runtime data from engine
        runtime = []
        try:
            runtime = self.engine.account_runtime()
        except Exception:
            pass

        rt_map = {r.get("id"): r for r in runtime if r.get("id")}

        # Merge
        for acc in state_accounts:
            acc_id = acc.get("id")
            rt_data = rt_map.get(acc_id, {})
            acc["online"] = rt_data.get("online", False)
            acc["currentBiome"] = rt_data.get("currentBiome", None)
            acc["hwndKnown"] = rt_data.get("hwndKnown", False)

        return state_accounts

    def get_settings(self) -> dict:
        return dict(self.config.settings)

    def get_status_snapshot(self) -> dict:
        """Get live status from status_events."""
        from core import status_events

        return status_events.snapshot()

    def get_activity_log(self, since_id: int = 0) -> dict:
        from core import activity_log

        res = activity_log.since(since_id)
        return {"entries": res.get("entries", []), "head": res.get("last", since_id)}
    def get_aura_log(self, since_id: int = 0) -> list:
        try:
            if hasattr(self.engine, "aura") and self.engine.aura:
                return self.engine.aura.aura_log(since_id)
        except Exception:
            pass
        return []


    def get_event_log(self, since_id: int = 0) -> list:
        from core import event_log

        return event_log.get(since_id)

    def get_account_timeline(
        self, account_id=None, before_id=None, limit=50, **kwargs
    ) -> dict:
        from core import account_timeline

        return account_timeline.get(account_id, before_id, limit, **kwargs)

    # ── Settings ──────────────────────────────────────────────────

    def set_setting(self, key: str, value: Any) -> None:
        self.config.settings[key] = value
        
        # Apply changes live to subsystems
        if key == "hotkey":
            self.register_hotkeys()
        elif key == "modeHotkey":
            self.register_hotkeys()
        elif key in ("ramTrimEnabled", "ramTrimInterval"):
            if hasattr(self, "ram_trimmer"):
                self.ram_trimmer.sync()
        elif key.startswith("throttle"):
            if hasattr(self, "throttler"):
                self.throttler.sync()
        elif key.startswith("antiAfk"):
            if hasattr(self.engine, "refresh_anti_afk"):
                self.engine.refresh_anti_afk()
        elif key in ("monitorDimEnabled", "monitorDimLevel") and self.engine.running:
            from core import monitor_dim
            if self.config.settings.get("monitorDimEnabled"):
                monitor_dim.start(self.config.settings.get("monitorDimLevel", 40))
            else:
                monitor_dim.stop()

    def save_config(self) -> None:
        self.config.save()

    # ── Account Management ────────────────────────────────────────

    def add_account(self, name: str, link: str = "", token: str = None) -> dict:
        try:
            avatar = ""
            roblox_user_id = None
            roblox_username = ""
            try:
                from core.macro_engine import MacroEngine

                profile = MacroEngine.get_roblox_profile(name)
                avatar = profile.get("avatar", "")
                roblox_user_id = profile.get("id")
                roblox_username = profile.get("name", "")
            except Exception:
                pass
            acc = self.config.add_account(
                name=name,
                link=link or "",
                avatar=avatar,
                roblox_user_id=roblox_user_id,
                roblox_username=roblox_username,
            )
            acc_id = acc.get("id")
            if token and acc_id:
                self.config.set_account_token(acc_id, token)
            self.config.save()
            return {"ok": True, "id": acc_id, "account": acc}
        except ValueError as ve:
            return {"ok": False, "error": str(ve)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def update_account(
        self,
        acc_id: str,
        name: str = None,
        link: str = None,
        token: str = None,
        modules: dict = None,
    ) -> dict:
        try:
            for acc in self.config.accounts:
                if acc.get("id") == acc_id:
                    if name is not None:
                        acc["name"] = name
                    if link is not None:
                        acc["link"] = link
                    if modules:
                        for k, v in modules.items():
                            acc[k] = v
                    if token:
                        self.config.set_account_token(acc_id, token)
                    self.config.save()
                    return {"ok": True}
            return {"ok": False, "error": "Account not found"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def move_account(self, acc_id: str, direction: str) -> dict:
        try:
            self.config.move_account(acc_id, direction)
            self.config.save()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def toggle_account_enabled(self, acc_id: str) -> dict:
        try:
            account = next(
                (a for a in self.config.accounts if a.get("id") == acc_id), None
            )
            if account:
                new_state = not account.get("enabled", True)
                self.config.set_account_enabled(acc_id, new_state)
                self.config.save()
                return {"ok": True, "enabled": new_state}
            return {"ok": False}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def toggle_webhook_active(self, wh_id: str) -> dict:
        try:
            wh = next((w for w in self.config.webhooks if w.get("id") == wh_id), None)
            if wh:
                new_state = not wh.get("active", True)
                self.config.set_webhook_active(wh_id, new_state)
                self.config.save()
                return {"ok": True, "active": new_state}
            return {"ok": False}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def test_webhook(self, wh_id: str) -> dict:
        try:
            from core import webhooks

            wh = next((w for w in self.config.webhooks if w.get("id") == wh_id), None)
            if wh:
                webhooks.macro_started(
                    urls=[wh.get("url")], account_names=["Test Account"], version="Test"
                )
                return {"ok": True}
            return {"ok": False}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def clear_roblox_logs(self) -> dict:
        try:
            from core import roblox_cleanup

            roblox_cleanup.clear_logs()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def factory_reset(self) -> dict:
        try:
            self.config.reset_to_defaults()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def open_url(self, url: str) -> None:
        import webbrowser

        webbrowser.open(url)
    def get_token_security_status(self) -> dict:
        return self.config.token_security_status()

    def clear_account_token(self, acc_id: str) -> dict:
        try:
            self.config.clear_account_token(acc_id)
            self.config.save()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def clear_all_account_tokens(self) -> dict:
        try:
            self.config.clear_all_account_tokens()
            self.config.save()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def revalidate_account_token(self, acc_id: str) -> dict:
        try:
            token = self.config.account_token(acc_id)
            if not token:
                return {"ok": False, "error": "No token"}
            from core import roblox_auth
            info = roblox_auth.validate_token(token)
            if info.get("refreshed"):
                self.config.set_account_token(acc_id, info["refreshed"])
                
            if info.get("ok") or info.get("refreshed"):
                self.config.set_account_token_status(
                    acc_id, info.get("name", ""), True, info.get("id")
                )
                self.config.save()
                return {"ok": True, "user": info.get("name", "")}
                
            if info.get("definitive"):
                self.config.set_account_token_status(acc_id, "", False)
                self.config.save()
                return {"ok": False, "error": info.get("error")}
                
            return {"ok": False, "error": info.get("error"), "transient": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}


    def delete_account(self, acc_id: str) -> dict:
        try:
            self.config.delete_account(acc_id)
            self.config.save()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def launch_account(self, acc_id: str) -> dict:
        account = self._find_account(acc_id)
        if not account:
            return {"ok": False, "error": "Account not found"}
        try:
            token = self.config.account_token(acc_id)
            if not token:
                return {"ok": False, "error": "No token set"}
            result = self._roblox_auth.launch_account(
                token,
                link=account.get("link", ""),
                place_id=None,
            )
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def launch_all_accounts(self) -> None:
        """Launch all enabled accounts with staggered delays."""

        def _launch_thread():
            for acc in self.config.accounts:
                if acc.get("enabled", True):
                    self.launch_account(acc.get("id", ""))
                    time.sleep(3.0)

        threading.Thread(target=_launch_thread, daemon=True).start()

    # ── Webhooks ──────────────────────────────────────────────────

    def add_webhook(self, name: str, url: str) -> dict:
        try:
            result = self.config.add_webhook(name, url)
            self.config.save()
            return result
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def delete_webhook(self, wh_id: str) -> dict:
        try:
            self.config.delete_webhook(wh_id)
            self.config.save()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Calibration ───────────────────────────────────────────────

    def apply_recommended_preset(self) -> dict:
        """Auto-detect display and apply matching calibration preset."""
        try:
            from core import display_calibration, presets

            result = display_calibration.inspect_displays(presets.preset_names())
            recommended = result.get("recommended")
            if recommended:
                self.config.load_preset(recommended)
                self.config.save()
                return {"ok": True, "preset": recommended}
            return {"ok": False, "error": "No matching preset"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def export_calibration(self) -> str:
        """Export calibration as JSON text."""
        try:
            from core import calibration_transfer

            return calibration_transfer.export_text(self.config.automation)
        except Exception:
            return ""

    # ── Performance ───────────────────────────────────────────────

    def get_performance(self) -> dict:
        try:
            from core import perf as perfmon

            return perfmon.snapshot(
                self.config.accounts,
                self.throttler.status(),
            )
        except Exception:
            return {"roblox": []}

    def trim_ram_now(self) -> dict:
        return self.ram_trimmer.trim_now()

    def start_benchmark(self) -> None:
        self.benchmark.start()

    def stop_benchmark(self) -> None:
        self.benchmark.stop()

    def get_throttle_status(self) -> dict:
        return self.throttler.status()

    # ── Hotkeys ───────────────────────────────────────────────────

    def register_hotkeys(self) -> None:
        """Register global hotkeys using the keyboard library."""
        try:
            import keyboard as kb
        except ImportError:
            print("[Hotkey] keyboard module not available")
            return

        saved_hotkey = self.config.settings.get("hotkey", "F5")
        self._register_hotkey(saved_hotkey)

        saved_mode = self.config.settings.get("modeHotkey", "none")
        if saved_mode and saved_mode != "none":
            self._register_mode_hotkey(saved_mode)

    def _register_hotkey(self, key: str) -> None:
        try:
            import keyboard as kb
        except ImportError:
            return

        with self._hotkey_lock:
            if self._hotkey_handle is not None:
                try:
                    kb.remove_hotkey(self._hotkey_handle)
                except Exception:
                    pass

            if not key or key == "none":
                self._hotkey_handle = None
                return

            def _on_hotkey():
                if self.is_engine_running():
                    result = self.stop_engine()
                    self._emit("engine_stopped", result)
                else:
                    result = self.start_engine()
                    if result.get("ok"):
                        self._emit("engine_started", result)

            try:
                self._hotkey_handle = kb.add_hotkey(key, _on_hotkey, suppress=True)
            except Exception as e:
                print(f"[Hotkey] Failed to register '{key}': {e}")

    def _register_mode_hotkey(self, key: str) -> None:
        try:
            import keyboard as kb
        except ImportError:
            return

        with self._mode_hotkey_lock:
            if self._mode_hotkey_handle is not None:
                try:
                    kb.remove_hotkey(self._mode_hotkey_handle)
                except Exception:
                    pass

            if not key or key == "none":
                self._mode_hotkey_handle = None
                return

            modes = ["idle", "automation", "eden"]

            def _on_mode_hotkey():
                current = self.get_engine_mode()
                idx = modes.index(current) if current in modes else 0
                next_mode = modes[(idx + 1) % len(modes)]
                self.set_engine_mode(next_mode)
                self._emit("mode_changed", next_mode)

            try:
                self._mode_hotkey_handle = kb.add_hotkey(
                    key, _on_mode_hotkey, suppress=True
                )
            except Exception as e:
                print(f"[Hotkey] Failed to register mode '{key}': {e}")

    # ── Shutdown ──────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Clean shutdown of all subsystems."""
        if self.engine.running:
            self.engine.stop()
        self.ram_trimmer.stop()
        self.throttler.stop()
        self.benchmark.stop()
        self.config.save_on_shutdown()

    def startup_services(self) -> None:
        """Start background services (call after TUI is ready)."""
        self.ram_trimmer.start()
        self.throttler.start()
        self.engine.refresh_anti_afk()
        self.register_hotkeys()

    # ── Internal Helpers ──────────────────────────────────────────

    def _find_account(self, acc_id: str) -> Optional[dict]:
        for acc in self.config.accounts:
            if acc.get("id") == acc_id:
                return acc
        return None

    def _resolve_account_id(self, account_name) -> Optional[str]:
        wanted = str(account_name or "").casefold()
        for account in self.config.accounts:
            if str(account.get("name") or "").casefold() == wanted:
                return account.get("id")
        return None

    def _refresh_missing_profiles(self) -> None:
        """Background task to fill in missing Roblox profiles."""

        def _do():
            try:
                from core import MacroEngine

                missing = [
                    acc
                    for acc in self.config.accounts
                    if not acc.get("robloxUserId") and acc.get("name")
                ]
                if not missing:
                    return
                profiles = MacroEngine.get_roblox_profiles(
                    acc.get("name") for acc in missing
                )
                changed = False
                for acc in missing:
                    profile = profiles.get(str(acc.get("name") or "").casefold())
                    if profile and profile.get("id"):
                        acc["robloxUserId"] = profile["id"]
                        acc["robloxUsername"] = profile.get("name", "")
                        changed = True
                if changed:
                    self.config.save()
            except Exception:
                pass

        threading.Thread(target=_do, name="profile-backfill", daemon=True).start()
