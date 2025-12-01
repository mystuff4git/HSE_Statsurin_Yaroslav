-- Группы
INSERT INTO groups (name) VALUES ('101-A'), ('102-B');

-- Студенты
INSERT INTO students (full_name, birth_date, email, phone, group_id) VALUES
('Иванов Иван Иванович', '2003-05-15', 'ivanov@example.com', '+79001112233', 1),
('Стацурин Петр Петрович', '2004-01-20', 'petrov@example.com', '+79004445566', 1),
('Сидорова Анна Сергеевна', '2003-08-10', 'sidorova@example.com', '+79007778899', 2),
('Кузнецов Олег Дмитриевич', '2003-12-05', 'kuznetsov@example.com', '+79005554433', 2);

-- Преподаватели
INSERT INTO teachers (full_name, email, phone) VALUES
('Смирнов Алексей Владимирович', 'smirnov@univ.ru', '+79990000001'),
('Кузнецова Мария Павловна', 'kuznetsova@univ.ru', '+79990000002'),
('Попов Дмитрий Сергеевич', 'popov@univ.ru', '+79990000003');

-- Предметы
INSERT INTO subjects (name, category) VALUES
('Высшая математика', 'math'),
('Линейная алгебра', 'math'),
('Философия', 'humanities'),
('История', 'humanities'),
('Физкультура', 'other');

-- Оценки
INSERT INTO grades (student_id, teacher_id, subject_id, grade_value, grade_date) VALUES
-- Иванов (Отличник)
(1, 1, 1, 5, '2023-09-10'), 
(1, 1, 2, 5, '2023-09-15'), 
(1, 2, 3, 5, '2023-10-01'), 

-- Стацурин (Двоечник по мат, хорош в гум)
(2, 1, 1, 2, '2023-09-10'), 
(2, 1, 1, 2, '2023-09-20'),
(2, 2, 3, 4, '2023-10-05'),

-- Сидорова (Умная: >4 math, <3 humanities - для теста запроса)
(3, 1, 1, 5, '2023-09-12'), -- Мат 5
(3, 2, 3, 2, '2023-10-05'), -- Фил 2
(3, 2, 4, 2, '2023-10-06'); -- Ист 2