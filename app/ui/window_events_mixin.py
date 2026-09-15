import ctypes

from PySide6.QtWidgets import QApplication

from app.services.windows_api import (
    HTCLOSE,
    SC_CLOSE,
    SC_MINIMIZE,

    WM_NCRBUTTONUP,
    WM_SYSCOMMAND,
    WIN_LIBS_LOADED,
)


class WindowEventsMixin:
    def closeEvent(self, event):
        """Завершает приложение при обычном нажатии на крестик окна."""
        if not self.is_closing:
            self._shutdown_application()
        event.accept()
        # В точке входа отключено автоматическое завершение при закрытии
        # последнего окна: это нужно для работы через системный трей. Обычный
        # клик по крестику, напротив, должен завершать event loop и процесс.
        QApplication.quit()

    def nativeEvent(self, eventType, message):
        """Перехватываем системные сообщения Windows."""
        if WIN_LIBS_LOADED and eventType == "windows_generic_MSG":
            msg = ctypes.wintypes.MSG.from_address(int(message))

            # WM_NCRBUTTONUP - отпускание правой кнопки мыши в неклиентской области
            if msg.message == WM_NCRBUTTONUP:
                # HTCLOSE = 20 - это код для кнопки закрытия
                if msg.wParam == HTCLOSE:
                    self.hide_to_tray()
                    return True, 0

            # WM_SYSCOMMAND - системные команды окна
            if msg.message == WM_SYSCOMMAND:
                # SC_CLOSE - нажатие на крестик (левая кнопка)
                if msg.wParam == SC_CLOSE:
                    self.quit_application()
                    return True, 0

                # SC_MINIMIZE - нажатие на кнопку минимизации
                elif msg.wParam == SC_MINIMIZE:
                    self.showMinimized()
                    return True, 0

        return super().nativeEvent(eventType, message)
