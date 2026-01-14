import functools
import time
from typing import Callable, Any

from .logging_config import logger


def log_action(verbose: bool = False):
    """Декоратор для логирования действий пользователя."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            action_name = func.__name__
            
            try:
                if verbose:
                    logger.info(f"Starting {action_name} with args={args[1:] if len(args) > 1 else ()}, kwargs={kwargs}")
                else:
                    logger.info(f"Starting {action_name}")
                
                result = func(*args, **kwargs)
                
                duration = time.time() - start_time
                logger.info(f"Completed {action_name} in {duration:.3f}s")
                
                if verbose and result:
                    logger.debug(f"Result of {action_name}: {result}")
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Error in {action_name} after {duration:.3f}s: {type(e).__name__}: {str(e)}")
                raise
                
        return wrapper
    return decorator


def require_login(func: Callable) -> Callable:
    """Декоратор для проверки авторизации пользователя."""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'is_authenticated') or not self.is_authenticated:
            from .core.exceptions import AuthenticationError
            raise AuthenticationError("Сначала выполните вход в систему")
        return func(self, *args, **kwargs)
    return wrapper


def validate_currency(func: Callable) -> Callable:
    """Декоратор для валидации кода валюты."""
    @functools.wraps(func)
    def wrapper(self, currency_code: str, *args, **kwargs):
        currency_code = currency_code.upper()
        
        try:
            from .core.usecases import use_cases
            if not use_cases.validate_currency_code(currency_code):
                from .core.exceptions import CurrencyNotFoundError
                raise CurrencyNotFoundError(currency_code)
        except ImportError:
            if len(currency_code) not in (2, 3, 4):
                from .core.exceptions import ValidationError
                raise ValidationError("currency_code", "Код валюты должен быть 2-4 символа")
        
        return func(self, currency_code, *args, **kwargs)
    return wrapper


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Декоратор для повторной попытки при ошибке."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(delay)
            
            logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception
            
        return wrapper
    return decorator


def measure_performance(func: Callable) -> Callable:
    """Декоратор для измерения производительности функции."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            duration = time.time() - start_time
            logger.debug(f"Performance: {func.__name__} took {duration:.3f}s")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Performance error: {func.__name__} failed after {duration:.3f}s: {e}")
            raise
            
    return wrapper
