import ctypes

from app.services.windows_api import (
    HTCLOSE,
    SC_CLOSE,
    SC_MINIMIZE,
    WM_NCRBUTTONDOWN,
    WM_SYSCOMMAND,
    WIN_LIBS_LOADED,
)


class WindowEventsMixin:
    def nativeEvent(self, eventType, message):
        """Перехватываем системные сообщения Windows."""
        if WIN_LIBS_LOADED and eventType == "windows_generic_MSG":
            msg = ctypes.wintypes.MSG.from_address(int(message))

            # WM_NCRBUTTONDOWN - правая кнопка мыши в неклиентской области (заголовок окна)
            if msg.message == WM_NCRBUTTONDOWN:
                # HTCLOSE = 20 - это код для кнопки закрытия
                if msg.wParam == HTCLOSE:
                    print("Правый клик на крестик - сворачиваем в трей")
                    self.right_click_on_close = True
                    self.hide_to_tray()
                    return True, 0

            # WM_SYSCOMMAND - системные команды окна
            if msg.message == WM_SYSCOMMAND:
                # SC_CLOSE - нажатие на крестик (левая кнопка)
                if msg.wParam == SC_CLOSE:
                    if not self.right_click_on_close:
                        print("Левый клик на крестик - закрываем приложение")
                        self.quit_application()
                        return True, 0
                    else:
                        # Сбрасываем флаг
                        self.right_click_on_close = False
                        return True, 0

                # SC_MINIMIZE - нажатие на кнопку минимизации
                elif msg.wParam == SC_MINIMIZE:
                    print("Левый клик на минимизацию - сворачиваем на панель задач")
                    self.showMinimized()
                    return True, 0

        return super().nativeEvent(eventType, message)
