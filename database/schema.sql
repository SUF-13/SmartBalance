
CREATE TABLE IF NOT EXISTS departments (
    dept_id       VARCHAR(10) PRIMARY KEY,
    dept_name     VARCHAR(100) NOT NULL,
    faculty_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS students (
    student_id              VARCHAR(20) PRIMARY KEY,
    full_name               VARCHAR(100) NOT NULL,
    email                   VARCHAR(100) UNIQUE NOT NULL,
    password_hash           VARCHAR(255) NOT NULL,
    department              VARCHAR(50),
    semester                INTEGER,
    degree                  VARCHAR(100),
    batch                   VARCHAR(50),
    section                 VARCHAR(20),
    campus                  VARCHAR(100),
    gender                  VARCHAR(20),
    dob                     VARCHAR(20),
    cnic                    VARCHAR(25),
    mobile_no               VARCHAR(25),
    blood_group             VARCHAR(10),
    nationality             VARCHAR(50),
    address                 VARCHAR(255),
    home_phone              VARCHAR(30),
    postal_code             VARCHAR(20),
    city                    VARCHAR(50),
    country                 VARCHAR(50),
    warning_count           INTEGER DEFAULT 0,
    credits_earned          INTEGER DEFAULT 0,
    credits_attempted       INTEGER DEFAULT 0,
    cgpa                    DECIMAL(3,2),
    credit_hours_completed  INTEGER DEFAULT 0,
    enrolled_at             TIMESTAMP DEFAULT NOW(),
    is_active               BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS academic_calendars (
    id                 SERIAL PRIMARY KEY,
    semester_label     VARCHAR(50) NOT NULL,
    registration_start VARCHAR(30) NOT NULL,
    registration_end   VARCHAR(30) NOT NULL,
    classes_start      VARCHAR(30) NOT NULL,
    classes_end        VARCHAR(30) NOT NULL,
    withdrawal_start   VARCHAR(30) NOT NULL,
    withdrawal_end     VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    course_id    VARCHAR(20) PRIMARY KEY,
    course_name  VARCHAR(100) NOT NULL,
    dept_id      VARCHAR(10) REFERENCES departments(dept_id),
    credit_hours INTEGER NOT NULL,
    semester     INTEGER,
    seats_total  INTEGER NOT NULL,
    seats_filled INTEGER DEFAULT 0,
    instructor   VARCHAR(100),
    schedule     VARCHAR(100),
    room         VARCHAR(50),
    is_active    BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS registrations (
    registration_id SERIAL PRIMARY KEY,
    student_id      VARCHAR(20) REFERENCES students(student_id),
    course_id       VARCHAR(20) REFERENCES courses(course_id),
    registered_at   TIMESTAMP DEFAULT NOW(),
    status          VARCHAR(20) DEFAULT 'enrolled',
    grade           VARCHAR(5),
    UNIQUE(student_id, course_id)
);

CREATE TABLE IF NOT EXISTS servers (
    server_id   VARCHAR(20) PRIMARY KEY,
    server_name VARCHAR(50) NOT NULL,
    capacity    INTEGER DEFAULT 50,
    is_alive    BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS request_logs (
    log_id         SERIAL PRIMARY KEY,
    student_id     VARCHAR(20) REFERENCES students(student_id),
    course_id      VARCHAR(20) REFERENCES courses(course_id),
    server_id      VARCHAR(20) REFERENCES servers(server_id),
    algorithm_used VARCHAR(30),
    response_time  DECIMAL(6,3),
    status         VARCHAR(20),
    requested_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS traffic_logs (
    log_id             SERIAL PRIMARY KEY,
    requests_count     INTEGER NOT NULL,
    active_connections INTEGER DEFAULT 0,
    algorithm_used     VARCHAR(30),
    recorded_at        TIMESTAMP DEFAULT NOW()
);