-- Удаление таблиц 
DROP TABLE IF EXISTS grades;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS teachers;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS groups;

-- 1. Таблица групп
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- 2. Таблица студентов
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    -- Проверка формата email через регулярное выражение
    email VARCHAR(100) UNIQUE CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    phone VARCHAR(20),
    group_id INT REFERENCES groups(id) ON DELETE SET NULL
);

-- 3. Таблица преподавателей
CREATE TABLE teachers (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    phone VARCHAR(20)
);

-- 4. Таблица предметов
-- Добавил поле category для выполнения задания про "математические/гуманитарные" предметы, да простите меня за такое деление
CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(20) CHECK (category IN ('humanities', 'math', 'other'))
);

-- 5. Таблица оценок (Связующая таблица)
CREATE TABLE grades (
    id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    teacher_id INT NOT NULL REFERENCES teachers(id) ON DELETE SET NULL,
    subject_id INT NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT, -- Запрет удаления предмета, если есть оценки
    grade_value INT NOT NULL CHECK (grade_value BETWEEN 1 AND 5), -- Ограничение оценки
    grade_date DATE NOT NULL DEFAULT CURRENT_DATE
);