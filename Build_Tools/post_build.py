# -*- coding: utf-8 -*-
"""
POST-BUILD CLEANUP SCRIPT (TEMPLATE)
Копирует ключевые файлы и убирает временные директории.
"""

import os
import shutil

# ========================================================
# 🔧 CONFIGURATION SECTION
# ========================================================
# Имя папки в dist (должно совпадать с именем в .spec файле)
APP_NAME = "Text_expander"

# Список файлов для копирования: (source_path, dest_relative_path)
# source_path: путь от корня проекта
# dest_relative_path: путь внутри папки с exe
FILES_TO_COPY = [
    ("logo.ico", "logo.ico"),
    ("snippets.json", "snippets.json"),
    ("expander_settings.json", "expander_settings.json"),
]

# Временные папки для удаления
TEMP_DIRS = [
    "build",
    "dist",
    "__pycache__",
]
# ========================================================

def safe_copy(src: str, dst: str, label: str) -> None:
    if os.path.exists(src):
        try:
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
            print(f"[OK] Copied {label}")
        except Exception as e:
            print(f"[ERROR] Failed to copy {label}: {e}")
    else:
        print(f"[SKIP] {label} not found at {src}")


def main() -> None:
    print("\n" + "=" * 60)
    print(f"POST-BUILD CLEANUP: {APP_NAME}")
    print("=" * 60)

    script_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    dist_app_dir = os.path.join(script_dir, "dist", APP_NAME)
    final_app_dir = os.path.join(project_root, APP_NAME)

    # 1. Переносим собранное приложение
    if os.path.exists(dist_app_dir):
        try:
            if os.path.exists(final_app_dir):
                shutil.rmtree(final_app_dir)
                print(f"[OK] Removed old {APP_NAME}/")
            shutil.move(dist_app_dir, final_app_dir)
            print(f"[OK] Moved to: {final_app_dir}")
        except Exception as e:
            print(f"[ERROR] Failed to move: {e}")
    else:
        print(f"[ERROR] dist/{APP_NAME} not found! Build might have failed.")
        return

    # 2. Копируем дополнительные файлы
    for src_rel, dst_rel in FILES_TO_COPY:
        src = os.path.join(project_root, src_rel)
        dst = os.path.join(final_app_dir, dst_rel)
        safe_copy(src, dst, src_rel)

    # 3. Удаляем временные директории
    print("\n[CLEANUP] Removing temporary directories...")
    for temp_name in TEMP_DIRS:
        # Check in script dir
        p1 = os.path.join(script_dir, temp_name)
        if os.path.exists(p1):
            try:
                shutil.rmtree(p1)
                print(f"[OK] Removed {p1}")
            except Exception as e:
                print(f"[ERROR] Failed to remove {p1}: {e}")
        
        # Check in project root
        p2 = os.path.join(project_root, temp_name)
        if os.path.exists(p2):
            try:
                shutil.rmtree(p2)
                print(f"[OK] Removed {p2}")
            except Exception as e:
                print(f"[ERROR] Failed to remove {p2}: {e}")

    print("\n" + "=" * 60)
    print(f"DONE! App location: {final_app_dir}")
    print("=" * 60)

    # 4. Запускаем приложение (опционально)
    # exe_path = os.path.join(final_app_dir, f"{APP_NAME}.exe")
    # if os.path.exists(exe_path):
    #     print(f"\n[EXEC] Launching {exe_path}...")
    #     try:
    #         os.startfile(exe_path)
    #     except Exception as e:
    #         print(f"[ERROR] Failed to launch exe: {e}")
    # else:
    #     print(f"[ERROR] Executable not found: {exe_path}")


if __name__ == "__main__":
    main()
