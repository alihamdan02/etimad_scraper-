CREATE DATABASE etimad_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE etimad_db;

CREATE TABLE etimad_classifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    unit ENUM ('Data & Innovation', 'SAP', 'MANA Services', 'other') DEFAULT 'other' NOT NULL,
    name_en VARCHAR(255) NOT NULL,
    name_ar VARCHAR(255),
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE etimad_classification_keywords (
    id INT AUTO_INCREMENT PRIMARY KEY,
    classification_id INT NOT NULL,
    keyword_en VARCHAR(255) NOT NULL,
    keyword_ar VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (classification_id) REFERENCES etimad_classifications(id) ON DELETE CASCADE
);

CREATE TABLE tenders (
    id INT auto_increment primary key,
    link VARCHAR(255) not null,
    tender_name VARCHAR(255) not null ,
    tender_number VARCHAR(50) not null UNIQUE,
    reference_number VARCHAR(50),
    purpose TEXT,
    document_value DECIMAL(10, 2),
    status ENUM ('Under Evaluation', 'Under Development', 'Submitted', 'Technical DiscQ', 'Financial DiscQ', 'Won') NOT NULL DEFAULT 'Under Evaluation',
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
    attachment VARCHAR(255) DEFAULT NULL
);


CREATE TABLE tender_keywords (
    tender_id INT NOT NULL,
    keyword_id INT NOT NULL,
    PRIMARY KEY (tender_id, keyword_id),
    FOREIGN KEY (tender_id) REFERENCES tenders(id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES etimad_classification_keywords(id) ON DELETE CASCADE
);
