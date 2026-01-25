import ctypes
import json
import logging
import os
import time
from ctypes import wintypes
from threading import Timer

import pyperclip
from pynput import keyboard

from app.services import scan_code_keyboard as sc
from app.services.windows_api import (
    get_active_process_name,
    get_active_window_class,
    get_active_window_title,
)


class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


class ListenerWorker:
    """
    Рабочий класс для pynput, который будет выполняться в отдельном потоке.
    """

    BUFFER_SIZE = 20

    def __init__(self, snippets_file):
        self.snippets_file = snippets_file
        self.scan_buffer = []
        self.snippets_by_abbr = {}
        self.snippets_by_scan = {}
        self.is_paused = False
        self.is_replacing = False
        self.listener = None
        self.last_active_pid = None
        self._last_hook_refresh_by_process = {}
        self._scheduled_hook_refresh_pid = None
        self._scheduled_hook_refresh_process_key = None
        self._scheduled_hook_refresh_deadlines = []
        self._hook_started_at = None
        self._last_key_event_at = None
        self._no_event_restart_attempts = 0
        self.should_run = True
        self._first_key_logged = False
        self.reload_snippets()

    def _get_system_idle_ms(self):
        try:
            info = _LASTINPUTINFO()
            info.cbSize = ctypes.sizeof(_LASTINPUTINFO)
            if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
                return None
            tick = ctypes.windll.kernel32.GetTickCount()
            return (tick - info.dwTime) & 0xFFFFFFFF
        except Exception:
            return None

    def run(self):
        """Запускает цикл слушателя с автоматическим переподключением."""
        logging.info("[RUN] Слушатель запущен")
        while self.should_run:
            try:
                self.listener = keyboard.Listener(on_press=self.on_press)
                self.listener.start()
                try:
                    self.listener.wait()
                except Exception:
                    pass
                self.last_active_pid = self._get_active_process_id()
                self._hook_started_at = time.monotonic()
                self._scheduled_hook_refresh_pid = None
                self._scheduled_hook_refresh_process_key = None
                self._scheduled_hook_refresh_deadlines = []
                while self.should_run and self.listener.running:
                    time.sleep(0.25)

                    now = time.monotonic()
                    current_pid = self._get_active_process_id()

                    if (
                        not self._first_key_logged
                        and self._hook_started_at is not None
                        and now - self._hook_started_at >= 30.0
                        and self._no_event_restart_attempts < 3
                    ):
                        idle_ms = self._get_system_idle_ms()
                        if idle_ms is not None and idle_ms < 5000:
                            self._no_event_restart_attempts += 1
                            logging.warning(
                                "[RESTART] Нет событий клавиатуры; перезапуск хука (%d/3)",
                                self._no_event_restart_attempts,
                            )
                            self.scan_buffer = []
                            if self.listener:
                                self.listener.stop()
                            break
                    if current_pid and current_pid != self.last_active_pid:
                        self.last_active_pid = current_pid
                        self.scan_buffer = []
                        active_process = get_active_process_name()
                        process_key = active_process or f"pid:{current_pid}"
                        last_refresh = self._last_hook_refresh_by_process.get(process_key)
                        should_schedule = (
                            last_refresh is None or (now - last_refresh) >= 20.0
                        )
                        if should_schedule:
                            self._scheduled_hook_refresh_pid = current_pid
                            self._scheduled_hook_refresh_process_key = process_key
                            self._scheduled_hook_refresh_deadlines = [
                                now + 0.5,
                                now + 3.0,
                                now + 10.0,
                                now + 20.0,
                            ]
                            logging.info(
                                "[RESTART] Активный процесс %s, планируем обновление хука",
                                active_process or current_pid,
                            )
                        else:
                            self._scheduled_hook_refresh_pid = None
                            self._scheduled_hook_refresh_process_key = None
                            self._scheduled_hook_refresh_deadlines = []

                    if (
                        self._scheduled_hook_refresh_pid
                        and current_pid == self._scheduled_hook_refresh_pid
                        and self._scheduled_hook_refresh_deadlines
                        and now >= self._scheduled_hook_refresh_deadlines[0]
                    ):
                        self._scheduled_hook_refresh_deadlines.pop(0)
                        self.scan_buffer = []
                        is_last_refresh = not self._scheduled_hook_refresh_deadlines
                        if is_last_refresh and self._scheduled_hook_refresh_process_key:
                            self._last_hook_refresh_by_process[
                                self._scheduled_hook_refresh_process_key
                            ] = now
                            self._scheduled_hook_refresh_pid = None
                            self._scheduled_hook_refresh_process_key = None
                        logging.info(
                            "[RESTART] Обновление хука для активного процесса %s",
                            get_active_process_name() or current_pid,
                        )
                        if self.listener:
                            self.listener.stop()
                        break
                # Если listener неожиданно остановился, цикл создаст его заново

            except Exception as exc:
                logging.exception("[WARN] Ошибка слушателя: %s", exc)
                time.sleep(1.0)
            finally:
                if self.listener:
                    self.listener.stop()
                    self.listener.join(timeout=1.0)
                    self.listener = None

        logging.info("[STOP] Слушатель остановлен")

    def stop(self):
        """Останавливает слушатель."""
        self.should_run = False
        if self.listener:
            self.listener.stop()

    def _get_active_process_id(self):
        """Возвращает PID активного процесса (ForegroundWindow), если он доступен."""
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return None
            pid = wintypes.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            return pid.value or None
        except Exception:
            return None

    def reload_snippets(self):
        """Перезагружает сниппеты из файла в расширенный словарь с фильтрами окон."""
        try:
            if os.path.exists(self.snippets_file):
                with open(self.snippets_file, "r", encoding="utf-8") as f:
                    categorized_data = json.load(f)
                flat_snippets = {}
                if isinstance(categorized_data, dict):
                    is_flat = bool(categorized_data) and all(
                        isinstance(v, str) for v in categorized_data.values()
                    )
                    if is_flat:
                        # Плоский формат без фильтров (для обратной совместимости)
                        flat_snippets = {
                            abbr: {"text": text, "filter": None}
                            for abbr, text in categorized_data.items()
                            if isinstance(text, str)
                        }
                    else:
                        # Иерархический формат: category -> {enabled, snippets, categories, window_filter}
                        def _ingest_payload(
                            payload, default_enabled=True, inherited_filter=None
                        ):
                            if not isinstance(payload, dict):
                                return
                            category_default_enabled = payload.get(
                                "enabled", default_enabled
                            )
                            # Получаем window_filter категории (если есть)
                            category_filter = payload.get("window_filter")
                            # Если у категории нет своего фильтра, наследуем от родителя
                            effective_filter = (
                                category_filter if category_filter else inherited_filter
                            )

                            snippets_block = payload.get("snippets")
                            if not isinstance(snippets_block, dict):
                                snippets_block = {
                                    key: value
                                    for key, value in payload.items()
                                    if key not in {"enabled", "categories", "window_filter"}
                                }

                            for abbr, snippet_payload in snippets_block.items():
                                if isinstance(snippet_payload, dict):
                                    snippet_text = snippet_payload.get("text", "")
                                    snippet_enabled = snippet_payload.get("enabled")
                                    # Сниппет может иметь свой фильтр или наследовать от категории
                                    snippet_filter = snippet_payload.get("window_filter")
                                    if not snippet_filter:
                                        snippet_filter = effective_filter
                                else:
                                    snippet_text = snippet_payload
                                    snippet_enabled = None
                                    snippet_filter = effective_filter
                                if snippet_enabled is None:
                                    snippet_enabled = category_default_enabled
                                if not snippet_enabled:
                                    continue
                                if not isinstance(snippet_text, str):
                                    snippet_text = str(snippet_text)
                                flat_snippets[abbr] = {
                                    "text": snippet_text,
                                    "filter": snippet_filter,
                                }

                            subcategories = payload.get("categories", {})
                            if isinstance(subcategories, dict):
                                for sub_payload in subcategories.values():
                                    _ingest_payload(
                                        sub_payload,
                                        category_default_enabled,
                                        effective_filter,
                                    )

                        for payload in categorized_data.values():
                            _ingest_payload(payload)
                elif isinstance(categorized_data, list):
                    # Неподдерживаемый тип (для совместимости).
                    flat_snippets = {}
                else:
                    flat_snippets = {}
                self.snippets_by_abbr, self.snippets_by_scan = sc.build_snippet_index(
                    flat_snippets
                )
                print("[INFO] Сниппеты успешно перезагружены.")
                logging.info(
                    "[INFO] Сниппеты загружены: %d, индекс: %d",
                    len(self.snippets_by_abbr),
                    len(self.snippets_by_scan),
                )
            else:
                self.snippets_by_abbr = {}
                self.snippets_by_scan = {}
                print("[WARN] Файл сниппетов не найден.")
                logging.warning(
                    "[WARN] Файл сниппетов не найден: %s", self.snippets_file
                )
        except (json.JSONDecodeError, IOError, StopIteration) as e:
            print(f"[ERROR] Ошибка при загрузке сниппетов: {e}")
            self.snippets_by_abbr = {}
            self.snippets_by_scan = {}
            logging.exception("[ERROR] Ошибка загрузки сниппетов: %s", e)

    def toggle_pause(self):
        """Переключает состояние паузы."""
        self.is_paused = not self.is_paused
        status = "приостановлен" if self.is_paused else "возобновлен"
        print(f"[INFO] Слушатель {status}.")

    def on_press(self, key):
        """Обработчик нажатия клавиши."""
        if self.is_paused or self.is_replacing:
            return
        self._last_key_event_at = time.monotonic()
        if not self._first_key_logged:
            logging.info("[INFO] Первое событие клавиши: %s", key)
            self._first_key_logged = True
        scan_code = sc.scan_code_from_key(key)
        is_space = key == keyboard.Key.space
        is_backspace = key == keyboard.Key.backspace

        if scan_code == sc.SC_SPACE or is_space:
            self.check_for_snippet(self.scan_buffer)
            self.scan_buffer = []
            return

        if scan_code == sc.SC_BACKSPACE or is_backspace:
            if self.scan_buffer:
                self.scan_buffer.pop()
            return

        if scan_code is None:
            return

        try:
            if key.char:
                # Фильтруем управляющие символы (ASCII < 32 и DEL область)
                if ord(key.char) >= 32 and not (127 <= ord(key.char) <= 159):
                    self.scan_buffer.append(scan_code)
                else:
                    self.scan_buffer = []
            else:
                self.scan_buffer = []
        except AttributeError:
            self.scan_buffer = []

        if len(self.scan_buffer) > self.BUFFER_SIZE:
            self.scan_buffer = self.scan_buffer[-self.BUFFER_SIZE :]

    def check_for_snippet(self, current_buffer):
        """Проверяет скан-коды в буфере и запускает замену с задержкой."""
        if not current_buffer:
            return False

        entries = self.snippets_by_scan.get(tuple(current_buffer))
        if not entries:
            if sc.is_dot_prefix(current_buffer):
                active_process = get_active_process_name()
                logging.info(
                    "[SNIPPET] Нет совпадения (%s) в %s",
                    sc.format_scancodes(current_buffer),
                    active_process or "unknown",
                )
            return False

        matched_entry = None
        for entry in entries:
            window_filter = entry.get("filter")
            if window_filter and not self._matches_window_filter(window_filter):
                continue
            matched_entry = entry
            break

        if not matched_entry:
            if sc.is_dot_prefix(current_buffer):
                active_process = get_active_process_name()
                logging.info(
                    "[SNIPPET] Отфильтровано по окну (%s) в %s",
                    sc.format_scancodes(current_buffer),
                    active_process or "unknown",
                )
            return False

        text_to_insert = matched_entry["text"]
        resolved_abbr = matched_entry.get("abbr", "")
        if sc.is_dot_prefix(current_buffer):
            active_process = get_active_process_name()
            logging.info(
                "[SNIPPET] Сработал '%s' (%s) в %s",
                resolved_abbr,
                sc.format_scancodes(current_buffer),
                active_process or "unknown",
            )
        Timer(
            0.05,
            self.replace_text,
            args=[len(current_buffer), text_to_insert],
        ).start()
        return True

    def _matches_window_filter(self, window_filter):
        """Проверяет, соответствует ли активное окно заданному фильтру."""
        if not window_filter:
            return True

        filter_title = window_filter.get("title", "").strip()
        filter_class = window_filter.get("class", "").strip()
        match_mode = window_filter.get("match_mode", "contains")

        # Если фильтры пустые, пропускаем
        if not filter_title and not filter_class:
            return True

        # Получаем информацию об активном окне
        current_title = get_active_window_title() or ""
        current_class = get_active_window_class() or ""

        # Проверяем заголовок
        if filter_title:
            if match_mode == "exact":
                if current_title != filter_title:
                    return False
            else:  # contains (по умолчанию)
                if filter_title.lower() not in current_title.lower():
                    return False

        # Проверяем класс окна
        if filter_class:
            if match_mode == "exact":
                if current_class != filter_class:
                    return False
            else:  # contains
                if filter_class.lower() not in current_class.lower():
                    return False

        return True

    def replace_text(self, typed_length, text):
        """
        Выполняет замену текста, используя разные методы для Word и других программ.
        """
        if self.is_replacing:
            return
        self.is_replacing = True
        original_clipboard = None
        try:
            active_process = get_active_process_name()
            is_word = active_process == "winword.exe" if active_process else False

            try:
                original_clipboard = pyperclip.paste()
            except Exception:
                logging.exception("[WARN] Ошибка чтения буфера обмена")
                original_clipboard = None

            try:
                pyperclip.copy(text)
            except Exception:
                logging.exception("[ERROR] Ошибка записи в буфер обмена")
                return
            time.sleep(0.05)

            if is_word:
                # --- Метод для Word ---
                for _ in range(typed_length + 1):
                    sc.tap_key(sc.SC_BACKSPACE)
                    time.sleep(0.01)
                time.sleep(0.05)
                sc.press_key(sc.SC_CTRL)
                sc.tap_key(sc.SC_V)
                sc.release_key(sc.SC_CTRL)
                time.sleep(0.05)
            else:
                # --- Метод для всех остальных программ ---
                sc.press_key(sc.SC_SHIFT)
                for _ in range(typed_length + 1):
                    sc.tap_key(sc.SC_LEFT, extended=True)
                sc.release_key(sc.SC_SHIFT)
                time.sleep(0.03)
                sc.tap_key(sc.SC_DELETE, extended=True)
                time.sleep(0.05)
                sc.press_key(sc.SC_SHIFT)
                sc.tap_key(sc.SC_INSERT, extended=True)
                sc.release_key(sc.SC_SHIFT)
                time.sleep(0.05)

        except Exception as e:
            logging.exception("[ERROR] Ошибка при замене текста: %s", e)
        finally:
            if original_clipboard is not None:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    logging.exception("[WARN] Ошибка восстановления буфера обмена")
            self.is_replacing = False
