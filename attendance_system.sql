-- Create Database
CREATE DATABASE IF NOT EXISTS attendance_system
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE attendance_system;

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    face_encoding LONGBLOB,
    image_path VARCHAR(500),
    status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    image_path VARCHAR(500),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    emotion VARCHAR(50),
    emotion_confidence DECIMAL(5,4),
    spoofing_score DECIMAL(5,4),
    is_real_face BOOLEAN DEFAULT TRUE,
    lecture_id VARCHAR(100),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS face_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    face_encoding LONGBLOB NOT NULL,
    image_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_primary BOOLEAN DEFAULT FALSE,
    quality_score DECIMAL(5,4) DEFAULT 0.8000,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS unknown_faces (
    id INT AUTO_INCREMENT PRIMARY KEY,
    image_path VARCHAR(500) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    face_encoding LONGBLOB,
    processed BOOLEAN DEFAULT FALSE,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS lecture_sessions (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    course_code VARCHAR(50),
    instructor VARCHAR(255),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NULL,
    total_attendees INT DEFAULT 0,
    engagement_score DECIMAL(5,4) DEFAULT 0.0000,
    emotions_summary JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lecture_attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lecture_id VARCHAR(100) NOT NULL,
    student_id INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    emotion VARCHAR(50),
    emotion_confidence DECIMAL(5,4),
    FOREIGN KEY (lecture_id) REFERENCES lecture_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS attendance_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    student_id INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS emotion_analytics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    date DATE NOT NULL,
    time TIME NOT NULL,
    emotion VARCHAR(50) NOT NULL,
    confidence DECIMAL(5,4),
    context VARCHAR(100),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);
