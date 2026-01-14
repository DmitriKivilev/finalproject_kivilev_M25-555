"""
Интерактивный режим Valutatrade Hub.
Запускается при вызове без аргументов.
"""

import sys
import readline  # Для истории команд в Linux/macOS
from .interface import ValutatradeCLI


def interactive_main():
    """Главная функция интерактивного режима."""
    print("\n" + "="*50)
    print("   VALUTATRADE HUB - Интерактивный режим")
    print("="*50)
    print("Введите команды (exit для выхода, help для справки)")
    print("="*50 + "\n")
    
    cli = ValutatradeCLI()
    
    while True:
        try:
            # Показываем приглашение
            user_input = input("valuta> ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Выход из интерактивного режима...")
                break
                
            if user_input.lower() == 'help':
                print("\nДоступные команды:")
                print("  register --username <name> --password <pass>")
                print("  login --username <name> --password <pass>")
                print("  show-portfolio [--base USD]")
                print("  buy --currency <code> --amount <num>")
                print("  sell --currency <code> --amount <num>")
                print("  get-rate --from <code> --to <code>")
                print("  logout")
                print("  status")
                print("  help - эта справка")
                print("  exit - выход\n")
                continue
            
            # Преобразуем ввод в аргументы командной строки
            args = ["main.py"] + user_input.split()
            sys.argv = args
            
            # Запускаем команду через CLI
            cli.run()
            
        except KeyboardInterrupt:
            print("\n\nВыход...")
            break
        except EOFError:
            print("\n\nВыход...")
            break
        except Exception as e:
            print(f"Ошибка: {e}")


if __name__ == "__main__":
    interactive_main()
