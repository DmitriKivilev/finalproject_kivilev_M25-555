#!/usr/bin/env python3
"""Тестирование исправлений"""

import os
import json
from datetime import datetime

print("=== Тест системы сессий ===")

# 1. Проверяем что можем создавать файлы
test_file = "test_file.json"
test_data = {"test": "data", "time": datetime.now().isoformat()}

with open(test_file, 'w') as f:
    json.dump(test_data, f)

print(f"1. Файл создан: {os.path.exists(test_file)}")

# 2. Читаем файл
with open(test_file, 'r') as f:
    loaded_data = json.load(f)
print(f"2. Данные прочитаны: {loaded_data}")

# 3. Удаляем файл
os.remove(test_file)
print(f"3. Файл удален: {not os.path.exists(test_file)}")

print("\n=== Тест Path из pathlib ===")
from pathlib import Path

p = Path("test_path.txt")
p.write_text("test content")
print(f"Path создан: {p.exists()}")
print(f"Содержимое: {p.read_text()}")
p.unlink()
print(f"Path удален: {not p.exists()}")

print("\n=== Тест завершен ===")
