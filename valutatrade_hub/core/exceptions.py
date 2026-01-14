class ValutatradeError(Exception):
    """Базовое исключение для всех ошибок проекта"""
    pass


class InsufficientFundsError(ValutatradeError):
    """Исключение при недостатке средств"""
    
    def __init__(self, available: float, required: float, code: str):
        message = f"Недостаточно средств: доступно {available} {code}, требуется {required} {code}"
        super().__init__(message)
        self.available = available
        self.required = required
        self.code = code


class CurrencyNotFoundError(ValutatradeError):
    """Исключение при неизвестной валюте"""
    
    def __init__(self, code: str):
        message = f"Неизвестная валюта '{code}'"
        super().__init__(message)
        self.code = code


class ApiRequestError(ValutatradeError):
    """Исключение при ошибке API"""
    
    def __init__(self, reason: str):
        message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)
        self.reason = reason


class UserNotFoundError(ValutatradeError):
    """Исключение при отсутствии пользователя"""
    
    def __init__(self, identifier: str):
        message = f"Пользователь '{identifier}' не найден"
        super().__init__(message)
        self.identifier = identifier


class AuthenticationError(ValutatradeError):
    """Исключение при ошибке аутентификации"""
    
    def __init__(self, message: str = "Ошибка аутентификации"):
        super().__init__(message)


class ValidationError(ValutatradeError):
    """Исключение при ошибке валидации"""
    
    def __init__(self, field: str, message: str):
        super().__init__(f"Ошибка валидации поля '{field}': {message}")
        self.field = field
        self.detail = message


class DatabaseError(ValutatradeError):
    """Исключение при ошибке работы с базой данных"""
    
    def __init__(self, message: str = "Ошибка базы данных"):
        super().__init__(message)


class ConfigurationError(ValutatradeError):
    """Исключение при ошибке конфигурации"""
    
    def __init__(self, message: str = "Ошибка конфигурации"):
        super().__init__(message)
