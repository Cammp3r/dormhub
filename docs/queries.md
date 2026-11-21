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
