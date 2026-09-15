from __future__ import annotations

import json
import os

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.services.data_exchange_service import save_json_document
from app.services.ui_scale_service import (
    DEFAULT_UI_SCALE_DELTA_PERCENT,
    DEFAULT_UI_SCALE_PERCENT,
    UI_SCALE_MODE_AUTO,
    UIScaleState,
    normalize_ui_scale_delta_percent,
    resolve_ui_scale_from_screen,
    scale_px,
)
from app.ui.ui_scale_runtime import apply_scaled_widget_metrics


DEFAULT_INITIAL_WINDOW_SIZE = (1000, 720)
MIN_READABLE_INITIAL_WINDOW_SIZE = (800, 600)


class UiScaleMixin:
    def _init_ui_scale_runtime(self):
        self._ui_scale_state: UIScaleState | None = None
        self._ui_scale_factor = 1.0
        self._ui_scale_delta_percent = DEFAULT_UI_SCALE_DELTA_PERCENT
        self._ui_scale_screen = None
        self._ui_scale_app_hooks_installed = False
        self._ui_scale_window_hook_installed = False

    def get_ui_scale_factor(self):
        return self._ui_scale_factor

    def _resolve_ui_scale_screen(self):
        handle = self.windowHandle()
        if handle is not None and handle.screen() is not None:
            return handle.screen()

        screen_getter = getattr(self, "screen", None)
        if callable(screen_getter) and screen_getter() is not None:
            return screen_getter()

        app = QApplication.instance()
        if app is not None:
            return app.primaryScreen()
        return None

    def _set_ui_scale_combo_delta(self, delta_percent):
        if not hasattr(self, "ui_scale_combo"):
            return

        normalized_delta = normalize_ui_scale_delta_percent(delta_percent)
        index = self.ui_scale_combo.findData(normalized_delta)
        if index < 0:
            index = self.ui_scale_combo.findData(DEFAULT_UI_SCALE_DELTA_PERCENT)
        if index < 0:
            return

        self.ui_scale_combo.blockSignals(True)
        self.ui_scale_combo.setCurrentIndex(index)
        self.ui_scale_combo.blockSignals(False)

    def _update_ui_scale_info_label(self):
        if not hasattr(self, "ui_scale_info_label") or self._ui_scale_state is None:
            return
        state = self._ui_scale_state
        self.ui_scale_info_label.setText(
            f"Авто: {state.auto_percent}% | "
            f"Поправка: {100 + state.delta_percent}% | "
            f"Итог: {state.final_percent}%"
        )

    def _read_settings_for_ui_scale(self):
        if not os.path.exists(self.settings_file):
            return {}
        try:
            with open(self.settings_file, "r", encoding="utf-8") as file:
                payload = json.load(file)
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _save_ui_scale_settings(self, state: UIScaleState | None = None):
        settings = self._read_settings_for_ui_scale()
        state = state or self._ui_scale_state
        settings["ui_scale_mode"] = UI_SCALE_MODE_AUTO
        settings["ui_scale_delta_percent"] = self._ui_scale_delta_percent
        settings["ui_scale_percent"] = (
            state.final_percent if state is not None else DEFAULT_UI_SCALE_PERCENT
        )
        try:
            save_json_document(self.settings_file, settings)
        except Exception:
            pass

    def _apply_scaled_widget_specifics(self, scale_factor):
        if hasattr(self, "snippet_tree_widget"):
            self.snippet_tree_widget.setColumnWidth(1, scale_px(20, scale_factor, 18))
            self.snippet_tree_widget.setIndentation(
                scale_px(12, scale_factor, 6)
            )
        if hasattr(self, "_apply_admin_status_style"):
            self._apply_admin_status_style()

    def _apply_initial_window_size(self):
        """Задаёт читаемую стартовую геометрию для профиля без настроек."""
        screen = self._resolve_ui_scale_screen()
        if screen is None:
            self.resize(*DEFAULT_INITIAL_WINDOW_SIZE)
            return

        available = screen.availableGeometry()
        default_width, default_height = DEFAULT_INITIAL_WINDOW_SIZE
        minimum_width, minimum_height = MIN_READABLE_INITIAL_WINDOW_SIZE
        width = min(
            available.width(),
            max(minimum_width, min(default_width, round(available.width() * 0.8))),
        )
        height = min(
            available.height(),
            max(minimum_height, min(default_height, round(available.height() * 0.8))),
        )
        self.resize(width, height)
        self.move(
            available.x() + (available.width() - width) // 2,
            available.y() + (available.height() - height) // 2,
        )

        if hasattr(self, "splitter"):
            tree_width = min(320, max(220, round(width * 0.3)))
            self.splitter.setSizes([tree_width, max(1, width - tree_width)])

    def _fit_window_to_scaled_minimum(self):
        if self.isMaximized():
            return
        minimum_size = self.minimumSize()
        current_size = self.size()
        target_width = max(current_size.width(), minimum_size.width())
        target_height = max(current_size.height(), minimum_size.height())
        if target_width != current_size.width() or target_height != current_size.height():
            self.resize(target_width, target_height)

    def apply_ui_scale(self, allow_window_resize=False, reason="runtime"):
        delta_percent = normalize_ui_scale_delta_percent(self._ui_scale_delta_percent)
        self._ui_scale_delta_percent = delta_percent

        screen = self._resolve_ui_scale_screen()
        state = resolve_ui_scale_from_screen(screen, delta_percent)
        self._ui_scale_state = state
        self._ui_scale_factor = state.scale_factor

        self._set_ui_scale_combo_delta(delta_percent)
        if hasattr(self, "_apply_styles"):
            self._apply_styles(state.scale_factor)
        apply_scaled_widget_metrics(self, state.scale_factor)
        self._apply_scaled_widget_specifics(state.scale_factor)
        self._update_ui_scale_info_label()
        self._save_ui_scale_settings(state)

        if allow_window_resize and reason in {"startup", "manual-delta"}:
            self._fit_window_to_scaled_minimum()

        return state

    def install_ui_scale_screen_hooks(self):
        app = QApplication.instance()
        if app is not None and not self._ui_scale_app_hooks_installed:
            app.primaryScreenChanged.connect(self.on_ui_scale_topology_changed)
            app.screenAdded.connect(self.on_ui_scale_topology_changed)
            app.screenRemoved.connect(self.on_ui_scale_topology_changed)
            self._ui_scale_app_hooks_installed = True

        handle = self.windowHandle()
        if handle is not None and not self._ui_scale_window_hook_installed:
            handle.screenChanged.connect(self.on_ui_scale_window_screen_changed)
            self._ui_scale_window_hook_installed = True

        self._connect_ui_scale_screen(self._resolve_ui_scale_screen())

    def _connect_ui_scale_screen(self, screen):
        if screen is None or screen is self._ui_scale_screen:
            return

        if self._ui_scale_screen is not None:
            for signal in (
                self._ui_scale_screen.logicalDotsPerInchChanged,
                self._ui_scale_screen.geometryChanged,
                self._ui_scale_screen.availableGeometryChanged,
            ):
                try:
                    signal.disconnect(self.on_ui_scale_screen_metrics_changed)
                except (RuntimeError, TypeError):
                    pass

        self._ui_scale_screen = screen
        screen.logicalDotsPerInchChanged.connect(self.on_ui_scale_screen_metrics_changed)
        screen.geometryChanged.connect(self.on_ui_scale_screen_metrics_changed)
        screen.availableGeometryChanged.connect(self.on_ui_scale_screen_metrics_changed)

    def _finish_ui_scale_startup(self):
        self.install_ui_scale_screen_hooks()
        self.apply_ui_scale(allow_window_resize=False, reason="runtime")

    def schedule_ui_scale_startup(self):
        QTimer.singleShot(0, self._finish_ui_scale_startup)

    def on_ui_scale_window_screen_changed(self, screen):
        self._connect_ui_scale_screen(screen)
        self.apply_ui_scale(allow_window_resize=False, reason="screen-changed")

    def on_ui_scale_screen_metrics_changed(self, *args):
        self.apply_ui_scale(allow_window_resize=False, reason="screen-metrics")

    def on_ui_scale_topology_changed(self, *args):
        self._connect_ui_scale_screen(self._resolve_ui_scale_screen())
        self.apply_ui_scale(allow_window_resize=False, reason="screen-topology")

    def on_ui_scale_delta_changed(self, index=None):
        if not hasattr(self, "ui_scale_combo"):
            return
        self._ui_scale_delta_percent = normalize_ui_scale_delta_percent(
            self.ui_scale_combo.currentData()
        )
        state = self.apply_ui_scale(allow_window_resize=True, reason="manual-delta")
        self.statusBar().showMessage(
            f"Масштаб интерфейса: {state.final_percent}%",
            3000,
        )
