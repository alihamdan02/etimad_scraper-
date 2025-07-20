CREATE DATABASE etimad_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE etimad_db;

-- Classifications
CREATE TABLE IF NOT EXISTS etimad_classifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    unit ENUM ('Data & Innovation', 'SAP', 'MANA Services', 'other') DEFAULT 'other' NOT NULL,
    name_en VARCHAR(255) NOT NULL,
    name_ar VARCHAR(255),
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Classification Keywords
CREATE TABLE IF NOT EXISTS etimad_classification_keywords (
    id INT AUTO_INCREMENT PRIMARY KEY,
    classification_id INT NOT NULL,
    keyword_en VARCHAR(255) NOT NULL,
    keyword_ar VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (classification_id) REFERENCES etimad_classifications(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tenders Table
CREATE TABLE IF NOT EXISTS tenders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    link VARCHAR(255) NOT NULL,
    tender_name VARCHAR(255) NOT NULL,
    tender_number VARCHAR(50) NOT NULL UNIQUE,
    reference_number VARCHAR(50),
    purpose TEXT,
    document_value DECIMAL(10, 2),
    status VARCHAR(50) NOT NULL,
    status_company ENUM ('Under Evaluation', 'Under Development', 'Submitted', 'Technical DiscQ', 'Financial DiscQ', 'Won') NOT NULL DEFAULT 'Under Evaluation',
    contract_duration VARCHAR(50),
    insurance_required ENUM('نعم', 'لا') DEFAULT 'لا',
    tender_type VARCHAR(50) NOT NULL DEFAULT 'منافسة عامة',
    government_entity VARCHAR(255) NOT NULL,
    last_query_date DATETIME,
    last_submission_date DATETIME,
    opening_date DATETIME,
    evaluation_date DATETIME,
    suspension_period INT,
    expected_award_date DATETIME,
    start_date DATETIME,
    question_start_date DATETIME,
    max_query_response_time INT,
    opening_location TEXT,
    attachment VARCHAR(255) DEFAULT NULL,
    keyword_id INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (keyword_id) REFERENCES etimad_classification_keywords(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Scraping Logs Table
CREATE TABLE IF NOT EXISTS scraping_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_word_id INT,
    classification_id INT,
    tender_count INT NOT NULL,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (key_word_id) REFERENCES etimad_classification_keywords(id) ON DELETE SET NULL,
    FOREIGN KEY (classification_id) REFERENCES etimad_classifications(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
