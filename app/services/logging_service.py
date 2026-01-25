import logging
import os

_LOG_CONFIGURED = False


def configure_logging(log_dir):
    global _LOG_CONFIGURED
    if _LOG_CONFIGURED:
        return
    try:
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "Text_expander.log")
        logging.basicConfig(
            filename=log_path,
            filemode="w",
            encoding="utf-8",
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
            force=True,
        )
        logging.info("=== Запуск Text expander ===")
    except Exception:
        # Не ломаем приложение из-за логирования.
        pass
    finally:
        _LOG_CONFIGURED = True
