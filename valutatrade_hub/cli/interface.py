import argparse
import sys
from typing import Optional

from valutatrade_hub.core.usecases import use_cases
from valutatrade_hub.core.exceptions import (
    ValutatradeError, AuthenticationError, ValidationError,
    InsufficientFundsError, CurrencyNotFoundError
)


class ValutatradeCLI:
    """Основной класс CLI интерфейса."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description='Valutatrade Hub - Консольный валютный кошелек',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        subparsers = parser.add_subparsers(
            dest='command',
            title='Команды',
            description='Доступные команды'
        )
        
        register_parser = subparsers.add_parser('register', help='Регистрация нового пользователя')
        register_parser.add_argument('--username', '-u', required=True, help='Имя пользователя')
        register_parser.add_argument('--password', '-p', required=True, help='Пароль')
        
        login_parser = subparsers.add_parser('login', help='Вход в систему')
        login_parser.add_argument('--username', '-u', required=True, help='Имя пользователя')
        login_parser.add_argument('--password', '-p', required=True, help='Пароль')
        
        portfolio_parser = subparsers.add_parser('show-portfolio', help='Показать портфель пользователя')
        portfolio_parser.add_argument('--base', '-b', default='USD', help='Базовая валюта')
        
        buy_parser = subparsers.add_parser('buy', help='Купить валюту')
        buy_parser.add_argument('--currency', '-c', required=True, help='Код покупаемой валюты')
        buy_parser.add_argument('--amount', '-a', type=float, required=True, help='Количество')
        
        sell_parser = subparsers.add_parser('sell', help='Продать валюту')
        sell_parser.add_argument('--currency', '-c', required=True, help='Код продаваемой валюты')
        sell_parser.add_argument('--amount', '-a', type=float, required=True, help='Количество')
        
        rate_parser = subparsers.add_parser('get-rate', help='Получить курс валюты')
        rate_parser.add_argument('--from', '-f', dest='from_currency', required=True, help='Исходная валюта')
        rate_parser.add_argument('--to', '-t', dest='to_currency', required=True, help='Целевая валюта')
        
        subparsers.add_parser('logout', help='Выход из системы')
        subparsers.add_parser('status', help='Показать статус текущей сессии')
        
        return parser
    
    def run(self):
        args = self.parser.parse_args()
        
        if not args.command:
            self.parser.print_help()
            return
        
        try:
            method_name = f"cmd_{args.command.replace('-', '_')}"
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                method(args)
            else:
                print(f"Команда '{args.command}' пока не реализована")
                
        except ValutatradeError as e:
            print(f"Ошибка: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nЗавершение работы...")
            sys.exit(0)
        except Exception as e:
            print(f"Неожиданная ошибка: {type(e).__name__}: {e}")
            sys.exit(1)
    
    def cmd_register(self, args):
        print("Регистрация нового пользователя...")
        
        try:
            user = use_cases.register_user(args.username, args.password)
            print(f"Пользователь '{user.username}' зарегистрирован (ID: {user.user_id})")
            
        except ValidationError as e:
            print(f"Ошибка регистрации: {e}")
    
    def cmd_login(self, args):
        print("Вход в систему...")
        
        try:
            session = use_cases.login(args.username, args.password)
            print(f"Вы вошли как '{session.username}'")
            print(f"ID пользователя: {session.user_id}")
            print(f"Время входа: {session.login_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except AuthenticationError as e:
            print(f"Ошибка авторизации: {e}")
    
    def cmd_show_portfolio(self, args):
        print("Загрузка портфеля...")
        
        try:
            portfolio_info = use_cases.get_portfolio_info(args.base)
            print("\n" + portfolio_info)
            
        except ValutatradeError as e:
            print(f"Ошибка: {e}")
    
    def cmd_buy(self, args):
        print(f"Покупка {args.amount} {args.currency}...")
        
        try:
            result = use_cases.buy_currency(args.currency, args.amount)
            print(f"{result['message']}")
            print(f"Курс: {result['rate']:.4f}")
            print(f"Стоимость: {result['cost_usd']:.2f} USD")
            print(f"Новый баланс {args.currency}: {result['new_balance']:.4f}")
            
        except ValutatradeError as e:
            print(f"Ошибка покупки: {e}")
    
    def cmd_sell(self, args):
        print(f"Продажа {args.amount} {args.currency}...")
        
        try:
            result = use_cases.sell_currency(args.currency, args.amount)
            print(f"{result['message']}")
            print(f"Курс: {result['rate']:.4f}")
            print(f"Выручка: {result['revenue_usd']:.2f} USD")
            print(f"Новый баланс {args.currency}: {result['new_balance']:.4f}")
            
        except ValutatradeError as e:
            print(f"Ошибка продажи: {e}")
    
    def cmd_get_rate(self, args):
        print(f"Получение курса {args.from_currency} → {args.to_currency}...")
        
        try:
            rate_info = use_cases.get_exchange_rate(args.from_currency, args.to_currency)
            
            print(f"\nКурс {rate_info['from']} → {rate_info['to']}:")
            print(f"Значение: {rate_info['rate']:.6f}")
            print(f"Источник: {rate_info['source']}")
            print(f"Обновлено: {rate_info['updated_at']}")
            
        except ValutatradeError as e:
            print(f"Ошибка получения курса: {e}")
    
    def cmd_logout(self, args):
        use_cases.logout()
        print("Вы вышли из системы")
    
    def cmd_status(self, args):
        if use_cases.is_authenticated:
            print(f"Авторизован как: {use_cases.current_session.username}")
            print(f"ID пользователя: {use_cases.current_session.user_id}")
            print(f"Время входа: {use_cases.current_session.login_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("Не авторизован")
            print("Используйте команду 'login' для входа в систему")


def main():
    cli = ValutatradeCLI()
    cli.run()


if __name__ == "__main__":
    main()
