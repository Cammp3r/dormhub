# Аналітичні запити

## Завантаженість кімнат

Бізнес-питання:

Скільки мешканців проживає в кожній кімнаті, скільки місць вільно і чи не перевищено
максимальну місткість 4?

```sql
SELECT d.dorm_number,
       r.room_id,
       r.room_number,
       r.floor,
       r.capacity,
       COUNT(DISTINCT s.student_id)::int AS resident_count,
       (r.capacity - COUNT(DISTINCT s.student_id))::int AS free_places
FROM dorms d
JOIN rooms r ON r.dorm_id = d.dorm_id
LEFT JOIN students s ON s.room_id = r.room_id
LEFT JOIN users u ON u.user_id = s.user_id
WHERE d.dorm_id = %s
  AND r.capacity <= 4
GROUP BY d.dorm_id, d.dorm_number,
         r.room_id, r.room_number, r.floor, r.capacity
HAVING COUNT(DISTINCT s.student_id) <= r.capacity
ORDER BY r.floor, r.room_number, r.room_id;
```

Пояснення:

- `JOIN dorms` і `JOIN rooms` зв’язують кожну кімнату з її гуртожитком.
- `LEFT JOIN students` зберігає порожні кімнати в звіті.
- `LEFT JOIN users` зв’язує мешканців із їхніми обліковими записами.
- `COUNT(DISTINCT s.student_id)` визначає кількість мешканців.
- `GROUP BY` групує рядки за кімнатою.
- `HAVING` залишає лише кімнати, які не перевищили власну місткість.
- Різниця `r.capacity - resident_count` показує кількість вільних місць.

## Повторювані ремонтні звернення

Бізнес-питання:

Які типи ремонтних звернень повторюються щонайменше двічі на певному поверсі,
скільки мешканців їх подавали та як поверхи ранжуються всередині кожної категорії?

```sql
WITH request_stats AS (
    SELECT q.category,
           r.floor,
           COUNT(*)::int AS request_count,
           COUNT(DISTINCT q.author_id)::int AS resident_count
    FROM maintenance_requests AS q
    JOIN rooms AS r
      ON r.room_id = q.room_id
     AND r.dorm_id = q.dorm_id
    JOIN users AS u
      ON u.user_id = q.author_id
    JOIN dorms AS d
      ON d.dorm_id = q.dorm_id
    WHERE q.dorm_id = %s
    GROUP BY q.category, r.floor
    HAVING COUNT(*) >= 2
),
ranked_requests AS (
    SELECT request_stats.*,
           RANK() OVER (
               PARTITION BY category
               ORDER BY request_count DESC,
                        resident_count DESC
           ) AS category_rank
    FROM request_stats
)
SELECT category,
       floor,
       request_count,
       resident_count,
       category_rank
FROM ranked_requests
ORDER BY request_count DESC,
         category,
         floor;
```

Пояснення:

- Чотири таблиці — `maintenance_requests`, `rooms`, `users` і `dorms` — зв’язуються
  через параметрізовану фільтрацію та первинні/зовнішні ключі.
- CTE `request_stats` агрегує звернення за категорією та поверхом.
- `COUNT(*)` рахує кількість звернень, а `COUNT(DISTINCT q.author_id)` рахує
  кількість різних мешканців.
- `HAVING COUNT(*) >= 2` залишає лише повторювані проблеми.
- CTE `ranked_requests` застосовує віконну функцію `RANK()` всередині кожної категорії.
- Звіт доступний лише адміністратору і обмежений гуртожитком поточного користувача.

## Заявки на вакансії

Бізнес-питання:

Скільки заявок і унікальних заявників має кожна вакансія та як заявки розподілені
за статусами?

```sql
WITH vacancy_application_stats AS (
    SELECT v.vacancy_id,
           v.company_name,
           v.job_name,
           COUNT(a.application_id)::int AS total_applications,
           COUNT(DISTINCT u.user_id)::int AS applicant_count,
           COUNT(a.application_id) FILTER (
               WHERE a.status = 'submitted'
           )::int AS submitted_count,
           COUNT(a.application_id) FILTER (
               WHERE a.status = 'accepted'
           )::int AS accepted_count,
           COUNT(a.application_id) FILTER (
               WHERE a.status = 'rejected'
           )::int AS rejected_count
    FROM vacancies AS v
    LEFT JOIN applications AS a ON a.vacancy_id = v.vacancy_id
    LEFT JOIN students AS s ON s.student_id = a.student_id
    LEFT JOIN users AS u ON u.user_id = s.user_id
    GROUP BY v.vacancy_id, v.company_name, v.job_name
)
SELECT vacancy_id,
       company_name,
       job_name,
       total_applications,
       applicant_count,
       submitted_count,
       accepted_count,
       rejected_count
FROM vacancy_application_stats
ORDER BY company_name, job_name, vacancy_id;
```

Пояснення:

- `applications`, `vacancies`, `students` і `users` зв’язуються, щоб підсумувати
  заявки за вакансією та порахувати унікальних заявників.
- CTE `vacancy_application_stats` групує записи за вакансією.
- `LEFT JOIN` зберігає у звіті вакансії, на які ще не подали заявок.
- `COUNT` рахує всі заявки та окремо заявки зі статусами `submitted`, `accepted`
  і `rejected`.
- Запит показує кількості, не розраховує відсоток прийняття і не формує рейтинг.
- Звіт доступний адміністраторам; вакансії не прив’язані до окремого гуртожитку,
  тому підсумок охоплює всі вакансії в базі.
