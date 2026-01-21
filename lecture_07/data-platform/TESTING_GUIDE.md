# 🧪 Посібник з тестування DAG process_iris

## 📋 Передумови

1. Docker та Docker Compose встановлені
2. Порти 5432, 5433, 8080 вільні
3. Мінімум 4GB RAM для Docker

## 🚀 Швидкий старт

### 1. Запуск всього стеку

```bash
cd lecture_07/data-platform

# Запустити всі сервіси
docker-compose up -d

# Перевірити статус
docker-compose ps

# Подивитися логи
docker-compose logs -f airflow-webserver
```

### 2. Автоматичне тестування

```bash
# Зробити скрипт виконуваним
chmod +x test_dag.sh

# Запустити тести
./test_dag.sh
```

### 3. Доступ до Airflow UI

1. Відкрити: http://localhost:8080
2. Логін: `admin` / `admin` (або перевірте логи)
3. Знайти DAG: `process_iris`

## 🔍 Ручне тестування

### Крок 1: Перевірка dbt моделі

```bash
# Увійти в контейнер
docker exec -it airflow_webserver bash

# Перейти в папку dbt
cd /opt/airflow/dags/dbt/homework

# Перевірити з'єднання
dbt debug --profiles-dir ../

# Запустити модель
dbt run --models iris_processed --profiles-dir ../

# Подивитися результат
dbt show --select iris_processed --profiles-dir ../ --limit 5
```

### Крок 2: Перевірка Python скрипта

```bash
# Увійти в контейнер
docker exec -it airflow_webserver bash

# Запустити скрипт
python /opt/airflow/dags/python_scripts/train_model.py
```

### Крок 3: Перевірка даних в БД

```bash
# Підключитися до БД
docker exec -it analytics_db psql -U etl_user -d analytics

# Перевірити дані
SELECT COUNT(*) FROM homework.iris_dataset;
SELECT COUNT(*) FROM homework.iris_processed;
SELECT * FROM ml_results.iris_model_metrics ORDER BY run_timestamp DESC LIMIT 5;

# Вийти
\q
```

### Крок 4: Запуск DAG

#### Через UI:
1. Відкрити http://localhost:8080
2. Знайти DAG `process_iris`
3. Натиснути кнопку ▶️ (Trigger DAG)
4. Вибрати дату: `2025-04-22`
5. Натиснути "Trigger"

#### Через CLI:
```bash
# Запустити для конкретної дати
docker exec airflow_webserver airflow dags trigger process_iris \
  --exec-date 2025-04-22

# Подивитися статус
docker exec airflow_webserver airflow dags list-runs -d process_iris
```

### Крок 5: Перевірка логів

```bash
# Логи dbt таски
docker exec airflow_webserver airflow tasks logs \
  process_iris dbt_transform_iris 2025-04-22

# Логи ML таски
docker exec airflow_webserver airflow tasks logs \
  process_iris train_ml_model 2025-04-22

# Логи email таски
docker exec airflow_webserver airflow tasks logs \
  process_iris send_success_email 2025-04-22
```

## 📧 Налаштування Email (опціонально)

### Варіант 1: MailHog (рекомендовано для тестування)

1. Додати в `docker-compose.yaml`:
```yaml
  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"
      - "8025:8025"
    networks:
      - data_network
```

2. Додати в `.env`:
```bash
AIRFLOW__SMTP__SMTP_HOST=mailhog
AIRFLOW__SMTP__SMTP_PORT=1025
AIRFLOW__SMTP__SMTP_MAIL_FROM=airflow@localhost
```

3. Переглядати листи: http://localhost:8025

### Варіант 2: Gmail

1. Створити App Password: https://myaccount.google.com/apppasswords
2. Додати в `.env`:
```bash
AIRFLOW__SMTP__SMTP_HOST=smtp.gmail.com
AIRFLOW__SMTP__SMTP_STARTTLS=True
AIRFLOW__SMTP__SMTP_SSL=False
AIRFLOW__SMTP__SMTP_USER=your_email@gmail.com
AIRFLOW__SMTP__SMTP_PASSWORD=your_app_password
AIRFLOW__SMTP__SMTP_PORT=587
AIRFLOW__SMTP__SMTP_MAIL_FROM=your_email@gmail.com
```

## 🐛 Вирішення проблем

### DAG не з'являється в UI

```bash
# Перевірити помилки парсингу
docker exec airflow_webserver airflow dags list

# Перевірити синтаксис
docker exec airflow_webserver python /opt/airflow/dags/process_iris.py
```

### dbt модель падає

```bash
# Перевірити логи
docker logs airflow_webserver

# Протестувати dbt вручну
docker exec -it airflow_webserver bash
cd /opt/airflow/dags/dbt/homework
dbt run --models iris_processed --profiles-dir ../ --debug
```

### Немає даних в БД

```bash
# Перевірити, чи завантажилися seed дані
docker exec airflow_webserver bash -c \
  "cd /opt/airflow/dags/dbt/homework && dbt seed --profiles-dir ../"
```

## ✅ Чеклист перевірки

- [ ] Всі Docker контейнери запущені
- [ ] DAG `process_iris` з'явився в UI
- [ ] Немає помилок парсингу
- [ ] dbt модель виконується успішно
- [ ] train_model.py виконується успішно
- [ ] Таблиця `homework.iris_processed` створена
- [ ] Таблиця `ml_results.iris_model_metrics` містить дані
- [ ] DAG можна запустити вручну
- [ ] Всі 3 таски виконуються успішно
- [ ] Catchup створює 3 DAG runs (22, 23, 24 квітня)

## 📊 Очікувані результати

### Структура DAG:
```
dbt_transform_iris → train_ml_model → send_success_email
```

### Дані в БД:
- `homework.iris_dataset`: 150 записів
- `homework.iris_processed`: 150 записів, ~100+ колонок
- `ml_results.iris_model_metrics`: 2 записи на кожен run
- `ml_results.iris_feature_importance`: ~100 записів на кожен run

### DAG runs:
- 3 runs для дат: 2025-04-22, 2025-04-23, 2025-04-24
- Кожен run має 3 успішні таски (зелені)

