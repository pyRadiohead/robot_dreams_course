#!/bin/bash

# Скрипт для тестування DAG process_iris
# Використання: ./test_dag.sh

set -e  # Зупинитися при помилці

echo "🚀 Тестування DAG process_iris"
echo "================================"

# Кольори для виводу
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функція для перевірки
check_step() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
        exit 1
    fi
}

echo ""
echo "📦 Крок 1: Перевірка Docker контейнерів"
docker compose ps | grep -E "airflow_webserver|airflow_scheduler|analytics_db"
check_step "Docker контейнери запущені"

echo ""
echo "🔍 Крок 2: Перевірка DAG в Airflow"
docker exec airflow_webserver airflow dags list | grep process_iris
check_step "DAG process_iris знайдено"

echo ""
echo "📝 Крок 3: Перевірка синтаксису DAG"
docker exec airflow_webserver python /opt/airflow/dags/process_iris.py
check_step "Синтаксис DAG правильний"

echo ""
echo "🗄️ Крок 4: Перевірка з'єднання з БД"
docker exec analytics_db psql -U etl_user -d analytics -c "SELECT 1;" > /dev/null
check_step "З'єднання з БД працює"

echo ""
echo "📊 Крок 5: Перевірка наявності даних iris"
COUNT=$(docker exec analytics_db psql -U etl_user -d analytics -t -c "SELECT COUNT(*) FROM homework.iris_dataset;" | xargs)
if [ "$COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Знайдено $COUNT записів в iris_dataset${NC}"
else
    echo -e "${RED}❌ Немає даних в iris_dataset${NC}"
    exit 1
fi

echo ""
echo "🧪 Крок 6: Тестування dbt моделі"
docker exec airflow_webserver bash -c "cd /opt/airflow/dags/dbt/homework && dbt run --models iris_processed --profiles-dir ../"
check_step "dbt модель виконалася успішно"

echo ""
echo "🎯 Крок 7: Перевірка результату dbt"
COUNT=$(docker exec analytics_db psql -U etl_user -d analytics -t -c "SELECT COUNT(*) FROM homework.iris_processed;" | xargs)
if [ "$COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Таблиця iris_processed містить $COUNT записів${NC}"
else
    echo -e "${RED}❌ Таблиця iris_processed порожня${NC}"
    exit 1
fi

echo ""
echo "🤖 Крок 8: Тестування train_model.py"
docker exec airflow_webserver python /opt/airflow/dags/python_scripts/train_model.py
check_step "Скрипт train_model.py виконався успішно"

echo ""
echo "📧 Крок 9: Перевірка EmailOperator (пропуск, якщо SMTP не налаштований)"
echo -e "${YELLOW}⚠️  Для тестування email налаштуйте SMTP або використайте MailHog${NC}"

echo ""
echo "🎉 Крок 10: Ручний запуск DAG"
echo -e "${YELLOW}Запускаємо DAG для дати 2025-04-22...${NC}"
docker exec airflow_webserver airflow dags trigger process_iris --exec-date 2025-04-22

echo ""
echo "⏳ Зачекайте 30 секунд, поки DAG виконається..."
sleep 30

echo ""
echo "📊 Крок 11: Перевірка статусу DAG run"
docker exec airflow_webserver airflow dags list-runs -d process_iris --state success | grep 2025-04-22
check_step "DAG run для 2025-04-22 завершився успішно"

echo ""
echo -e "${GREEN}🎉 ВСІ ТЕСТИ ПРОЙШЛИ УСПІШНО!${NC}"
echo ""
echo "📌 Наступні кроки:"
echo "1. Відкрийте http://localhost:8080 для перегляду Airflow UI"
echo "2. Перевірте Graph View для DAG process_iris"
echo "3. Подивіться логи кожної таски"
echo "4. Перевірте результати в БД:"
echo "   docker exec -it analytics_db psql -U etl_user -d analytics"
echo "   SELECT * FROM ml_results.iris_model_metrics;"
echo ""

