CREATE DATABASE etimad_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE etimad_db;


SELECT * FROM etimad_classifications;
SELECT * FROM etimad_classification_keywords;
SELECT * FROM tenders;
SELECT * FROM tender_keywords;
SELECT * FROM scraping_logs;


SELECT 
    ec.name_ar AS classification_name_ar,
    eck.keyword_ar,
    sl.tender_count,
    sl.status,
    sl.error_message
FROM 
    scraping_logs sl
LEFT JOIN 
    etimad_classifications ec ON sl.classification_id = ec.id
LEFT JOIN 
    etimad_classification_keywords eck ON sl.key_word_id = eck.id
ORDER BY 
    sl.created_at DESC;



-- First Example ---------------------

-- Insert into etimad_classifications
-- Adds the classification 'Data Management' under the unit 'Data & Innovation'
INSERT INTO etimad_classifications (unit, name_en, name_ar, description)
VALUES (
    'Data & Innovation', 
    'Data Management', 
    'إدارة البيانات', 
    'Projects related to data handling and analysis'
);

-- Insert into etimad_classification_keywords
-- Adds the keyword 'Data Governance' linked to the classification (assumes classification_id = 1)
INSERT INTO etimad_classification_keywords (classification_id, keyword_en, keyword_ar)
VALUES (
    1, 
    'usiness intelligence', 
    'حوكمة البيانات'
);


SELECT 
    t.id AS tender_id,
    t.tender_name,
    t.tender_number,
    t.status,
    t.government_entity,
    ec.name_ar AS classification_name,
    eck.keyword_ar AS keyword
FROM 
    tenders t
LEFT JOIN 
    tender_keywords tk ON t.id = tk.tender_id
LEFT JOIN 
    etimad_classification_keywords eck ON tk.keyword_id = eck.id
LEFT JOIN 
    etimad_classifications ec ON eck.classification_id = ec.id
ORDER BY 
    t.id, ec.name_en, eck.keyword_en;