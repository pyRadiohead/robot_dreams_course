/*
 Завдання на SQL до лекції 03.
 */


/*
1.
Вивести кількість фільмів в кожній категорії.
Результат відсортувати за спаданням.
*/

SELECT
    c.name AS category_name,
    COUNT(f.film_id) AS film_count
FROM
    category AS c
JOIN
    film_category AS fc
    ON fc.category_id = c.category_id
JOIN
    film AS f
    ON f.film_id = fc.film_id
GROUP BY
    c.name
ORDER BY
    film_count DESC;
2.
Вивести 10 акторів, чиї фільми брали на прокат найбільше.
Результат відсортувати за спаданням.
*/
SELECT
    CONCAT(a.first_name, ' ', a.last_name) AS actor,
    COUNT(r.rental_id) AS rental_amount
FROM
    actor a
JOIN film_actor fa ON
    fa.actor_id = a.actor_id
JOIN inventory i ON
    i.film_id = fa.film_id
JOIN rental r ON
    r.inventory_id = i.inventory_id
GROUP BY
    actor
ORDER BY
    rental_amount DESC
LIMIT 10

/*
3.
Вивести категорія фільмів, на яку було витрачено найбільше грошей
в прокаті
*/
WITH CategorySales AS (
    -- Calculating total_sales for each film category as CategorySales temporary table
    SELECT
        c.name AS category_name,
        SUM(p.amount) AS total_sales
    FROM
        category c
    JOIN
        film_category fc ON fc.category_id = c.category_id
    JOIN
        inventory i ON i.film_id = fc.film_id
    JOIN
        rental r ON r.inventory_id  = i.inventory_id
    JOIN
        payment p ON r.inventory_id = p.rental_id
    GROUP BY
        c.name
)
SELECT
    category_name,
    total_sales
FROM (
    -- Subquery with the window function to apply DENSE_RANK() to create temporary ranked film categories based on CategorySales calculations
    SELECT
        category_name,
        total_sales,
        DENSE_RANK() OVER (ORDER BY total_sales DESC) AS sales_rank
    FROM
        CategorySales
) RankedSales
-- Filter for the top category (Rank 1)
WHERE
    sales_rank = 1;

/*
4.
Вивести назви фільмів, яких не має в inventory.
Запит має бути без оператора IN
*/
SELECT
    f.title AS non_inventory_films
FROM
    film f
LEFT JOIN inventory i ON
    i.film_id = f.film_id
WHERE
    i.film_id IS NULL

/*
5.
Вивести топ 3 актори, які найбільше зʼявлялись в категорії фільмів “Children”.
*/
WITH ChildrenCategoryActors AS (
    -- Calculating how many times each actor played in children category film
    SELECT
        CONCAT(a.first_name, ' ', a.last_name) AS actor,
        COUNT(c.category_id) AS played_in_children_category
    FROM
        actor a
    JOIN film_actor fa ON fa.actor_id = a.actor_id
    JOIN film f ON f.film_id = fa.film_id
    JOIN film_category fc ON fc.film_id = f.film_id
    JOIN category c ON c.category_id = fc.category_id
    WHERE
        c.name LIKE 'Children'
    GROUP BY
        actor
)
SELECT
    actor,
    children_category_played_rank,
    played_in_children_category
FROM
    (
        -- Subquery with the window function to apply ROW_NUMBER() as we need unique ranks
    SELECT
        actor,
        played_in_children_category,
        ROW_NUMBER() OVER(ORDER BY played_in_children_category DESC) AS children_category_played_rank
    FROM
        ChildrenCategoryActors
) ActorsRanked
WHERE
    children_category_played_rank <= 3
ORDER BY
    played_in_children_category DESC;