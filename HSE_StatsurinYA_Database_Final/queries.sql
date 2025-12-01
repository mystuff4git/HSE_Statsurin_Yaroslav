-- 1. Вывести список студентов по предмету 'Высшая математика'
SELECT DISTINCT s.full_name, g.name AS group_name
FROM students s
JOIN grades gr ON s.id = gr.student_id
JOIN subjects sub ON gr.subject_id = sub.id
JOIN groups g ON s.group_id = g.id
WHERE sub.name = 'Высшая математика';

-- 2. Список предметов, которые ведёт 'Смирнов Алексей Владимирович'
SELECT DISTINCT sub.name
FROM subjects sub
JOIN grades gr ON sub.id = gr.subject_id
JOIN teachers t ON gr.teacher_id = t.id
WHERE t.full_name = 'Смирнов Алексей Владимирович';

-- 3. Средний балл студента по всем предметам
SELECT s.full_name, ROUND(AVG(gr.grade_value), 2) as average_score
FROM students s
JOIN grades gr ON s.id = gr.student_id
GROUP BY s.id, s.full_name;

-- 4. Рейтинг преподавателей по средней оценке студентов
SELECT t.full_name, ROUND(AVG(gr.grade_value), 2) as avg_student_score
FROM teachers t
JOIN grades gr ON t.id = gr.teacher_id
GROUP BY t.id, t.full_name
ORDER BY avg_student_score DESC;

-- 5. Преподаватели, которые вели > 3 предметов за последний год
SELECT t.full_name
FROM teachers t
JOIN grades gr ON t.id = gr.teacher_id
WHERE gr.grade_date >= CURRENT_DATE - INTERVAL '1 year'
GROUP BY t.id, t.full_name
HAVING COUNT(DISTINCT gr.subject_id) > 3;

-- 6. Студенты: ср. балл > 4 по математическим, но < 3 по гуманитарным
SELECT s.full_name
FROM students s
JOIN grades gr ON s.id = gr.student_id
JOIN subjects sub ON gr.subject_id = sub.id
GROUP BY s.id, s.full_name
HAVING 
    AVG(CASE WHEN sub.category = 'math' THEN gr.grade_value END) > 4
    AND 
    AVG(CASE WHEN sub.category = 'humanities' THEN gr.grade_value END) < 3;

-- 7. Предметы с наибольшим количеством двоек в текущем семестре
SELECT sub.name, COUNT(*) as count_of_twos
FROM subjects sub
JOIN grades gr ON sub.id = gr.subject_id
WHERE gr.grade_value = 2 
  AND gr.grade_date >= '2023-09-01' -- Дата начала семестра
GROUP BY sub.id, sub.name
ORDER BY count_of_twos DESC
LIMIT 1;

-- 8. Студенты-отличники (все 5) и их преподаватели
SELECT s.full_name AS student, t.full_name AS teacher, sub.name AS subject
FROM students s
JOIN grades gr ON s.id = gr.student_id
JOIN teachers t ON gr.teacher_id = t.id
JOIN subjects sub ON gr.subject_id = sub.id
WHERE s.id NOT IN (
    SELECT student_id FROM grades WHERE grade_value < 5
);

-- 9. Изменение среднего балла студента по годам
SELECT s.full_name, EXTRACT(YEAR FROM gr.grade_date) as year, ROUND(AVG(gr.grade_value), 2) as avg_score
FROM students s
JOIN grades gr ON s.id = gr.student_id
GROUP BY s.id, s.full_name, year
ORDER BY s.full_name, year;

-- 10. Группы с более высоким средним баллом, чем в среднем по вузу по этому предмету
SELECT g.name as group_name, sub.name as subject, ROUND(AVG(gr.grade_value), 2) as group_avg
FROM groups g
JOIN students s ON g.id = s.group_id
JOIN grades gr ON s.id = gr.student_id
JOIN subjects sub ON gr.subject_id = sub.id
GROUP BY g.id, g.name, sub.id, sub.name
HAVING AVG(gr.grade_value) > (
    SELECT AVG(grade_value) FROM grades WHERE subject_id = sub.id
);

-- 11. Вставка нового студента
INSERT INTO students (full_name, birth_date, email, phone, group_id) 
VALUES ('Новиков Дмитрий Игоревич', '2005-02-28', 'novikov@example.com', '+79009991111', 1);

-- 12. Обновление контактов преподавателя
UPDATE teachers 
SET email = 'new_email@univ.ru', phone = '+70000000000'
WHERE full_name = 'Смирнов Алексей Владимирович';

-- 13. Удаление предмета (сначала удаляем оценки, т.к. стоит ограничение RESTRICT)
BEGIN;
DELETE FROM grades WHERE subject_id = (SELECT id FROM subjects WHERE name = 'История');
DELETE FROM subjects WHERE name = 'История';
COMMIT;

-- 14. Вставка новой оценки
INSERT INTO grades (student_id, subject_id, teacher_id, grade_value, grade_date)
VALUES (
    (SELECT id FROM students WHERE email = 'ivanov@example.com'),
    (SELECT id FROM subjects WHERE name = 'Линейная алгебра'),
    (SELECT id FROM teachers WHERE full_name = 'Смирнов Алексей Владимирович'),
    4,
    CURRENT_DATE
);