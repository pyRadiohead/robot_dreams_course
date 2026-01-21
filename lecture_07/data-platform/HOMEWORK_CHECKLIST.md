# ✅ Чеклист виконання домашнього завдання

## 📋 Вимоги завдання

### ✅ Вимога 1: Створити DAG з 3 тасками
- [x] **Task 1:** dbt трансформація (`dbt_transform_iris`)
  - Виконує `iris_processed.sql`
  - Створює таблицю з ~100+ features
- [x] **Task 2:** Тренування ML моделі (`train_ml_model`)
  - Запускає `python_scripts/train_model.py`
  - Зберігає результати в `ml_results` схему
- [x] **Task 3:** Email нотифікація (`send_success_email`)
  - Відправляє email про успіх
  - Альтернатива: логування (якщо SMTP не налаштований)

### ⚠️ Вимога 2: Перевірка статус-коду 201
**УВАГА:** Ця вимога незрозуміла, оскільки:
- dbt не повертає HTTP статус-коди
- train_model.py не робить HTTP запитів
- Можливо, мається на увазі успішне завершення (exit code 0)?

**Рекомендація:** Уточніть у викладача!

### ✅ Вимога 3: Обробка даних за 3 дні (22-24 квітня)
- [x] `start_date = datetime(2025, 4, 22)`
- [x] `end_date = datetime(2025, 4, 25)` (щоб включити 24-те)
- [x] `catchup = True` (обробити всі дати)

**Результат:** Airflow створить 3 DAG runs:
- 2025-04-22
- 2025-04-23
- 2025-04-24

### ✅ Вимога 4: Запуск о 1 ночі Київського часу
- [x] `schedule_interval = '0 22 * * *'`
- Київ (літній час) = UTC+3
- 01:00 Київ = 22:00 UTC ✅

**Cron пояснення:**
```
0 22 * * *
│ │  │ │ │
│ │  │ │ └─── день тижня (будь-який)
│ │  │ └───── місяць (будь-який)
│ │  └─────── день місяця (будь-який)
│ └────────── година (22 = 10 PM UTC)
└──────────── хвилина (0)
```

### ✅ Вимога 5: Обробка даних за конкретну дату
- [x] Використовується Airflow macro `{{ ds }}`
- [x] Передається в dbt через `vars={'execution_date': '{{ ds }}'}`

**Примітка:** Модель `iris_processed.sql` не фільтрує по даті, оскільки датасет Iris статичний (150 записів без дат).

## 🔧 Що потрібно зробити перед запуском

### 1. Налаштування SMTP (опціонально)

**Варіант A: MailHog (рекомендовано)**
```bash
# Додати в docker-compose.yaml сервіс mailhog
# Додати в .env:
AIRFLOW__SMTP__SMTP_HOST=mailhog
AIRFLOW__SMTP__SMTP_PORT=1025
```

**Варіант B: Gmail**
```bash
# Створити App Password
# Додати в .env налаштування Gmail
```

**Варіант C: Без email**
```python
# Розкоментувати в process_iris.py опцію 2 (log_success)
# Закоментувати EmailOperator
```

### 2. Запуск системи

```bash
cd lecture_07/data-platform

# Запустити всі сервіси
docker-compose up -d

# Перевірити статус
docker-compose ps

# Зачекати ~30 секунд для ініціалізації
```

### 3. Перевірка DAG

```bash
# Автоматичний тест
chmod +x test_dag.sh
./test_dag.sh

# Або вручну
docker exec airflow_webserver airflow dags list | grep process_iris
```

## 🧪 Тестування

### Швидкий тест (ручний запуск)

```bash
# Запустити DAG для однієї дати
docker exec airflow_webserver airflow dags trigger process_iris \
  --exec-date 2025-04-22

# Перевірити статус
docker exec airflow_webserver airflow dags list-runs -d process_iris
```

### Повний тест (catchup)

1. Відкрити http://localhost:8080
2. Знайти DAG `process_iris`
3. Увімкнути DAG (toggle switch)
4. Зачекати кілька хвилин
5. Перевірити, що створилося 3 runs

### Перевірка результатів

```bash
# Підключитися до БД
docker exec -it analytics_db psql -U etl_user -d analytics

# Перевірити результати
SELECT * FROM ml_results.iris_model_metrics ORDER BY run_timestamp DESC;
SELECT * FROM ml_results.iris_feature_importance ORDER BY importance DESC LIMIT 10;
```

## 📊 Очікувані результати

### DAG Structure
```
┌─────────────────────┐
│ dbt_transform_iris  │
│ (dbt run)           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  train_ml_model     │
│  (Python)           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ send_success_email  │
│ (Email/Log)         │
└─────────────────────┘
```

### Database Tables
- `homework.iris_dataset` - 150 rows (source)
- `homework.iris_processed` - 150 rows, ~100+ columns
- `ml_results.iris_model_metrics` - 2 rows per run
- `ml_results.iris_feature_importance` - ~100 rows per run

### DAG Runs
- 3 successful runs (зелені)
- Дати: 2025-04-22, 2025-04-23, 2025-04-24
- Кожен run: ~2-5 хвилин

## 🐛 Troubleshooting

### DAG не з'являється
```bash
docker exec airflow_webserver python /opt/airflow/dags/process_iris.py
```

### dbt падає
```bash
docker exec -it airflow_webserver bash
cd /opt/airflow/dags/dbt/homework
dbt run --models iris_processed --profiles-dir ../ --debug
```

### Email не працює
- Перевірте налаштування SMTP в `.env`
- Або використайте альтернативу (log_success)

## 📚 Додаткові ресурси

- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Детальний посібник з тестування
- [test_dag.sh](test_dag.sh) - Автоматичний тестовий скрипт
- Airflow UI: http://localhost:8080
- MailHog UI: http://localhost:8025 (якщо налаштовано)

