#!/usr/bin/env python3
"""
Главный файл приложения Valutatrade Hub.
Поддерживает два режима:
1. Интерактивный (без аргументов)
2. CLI (с аргументами)
"""

import sys


def main():
    # Если запустили без аргументов - интерактивный режим
    if len(sys.argv) == 1:
        try:
            from valutatrade_hub.cli.interactive import interactive_main
            interactive_main()
        except ImportError as e:
            print(f"Ошибка импорта интерактивного режима: {e}")
            print("Запускаю CLI режим...")
            from valutatrade_hub.cli.interface import main as cli_main
            cli_main()
    else:
        # CLI режим с аргументами
        from valutatrade_hub.cli.interface import main as cli_main
        cli_main()


if __name__ == "__main__":
    main()
