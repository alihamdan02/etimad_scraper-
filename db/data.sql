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
    'Data Governance', 
    'حوكمة البيانات'
);

-- Insert into tenders
-- Adds the tender data, mapping JSON fields to table columns with Gregorian dates extracted
INSERT INTO tenders (
    link,
    tender_name,
    tender_number,
    reference_number,
    purpose,
    document_value,
    status,
    contract_duration,
    insurance_required,
    tender_type,
    government_entity,
    last_query_date,
    last_submission_date,
    opening_date,
    evaluation_date,
    suspension_period,
    expected_award_date,
    start_date,
    question_start_date,
    max_query_response_time,
    opening_location,
    attachment
) VALUES (
    'https://tenders.etimad.sa/Tender/DetailsForVisitor?STenderId=FQBfbgojPzEsnoIC5oPFew==',
    'تجديد رخص أدوات إدارة وحوكمة البيانات ودليل البيانات والدعم الفني',
    '107247',
    '250639011591',
    'تجديد رخص أدوات إدارة وحوكمة البيانات ودليل البيانات والدعم الفني ...عرض الأقل...',
    600.00,
    'Submitted',
    '12 شهر',
    'لا',
    'منافسة عامة',
    'وزارة الموارد البشرية والتنمية الاجتماعية',
    '2025-07-13 00:00:00',
    '2025-07-19 09:59:00',
    '2025-07-19 10:00:00',
    NULL,
    5,
    '2025-08-14 00:00:00',
    '2025-09-10 00:00:00',
    '2025-07-06 00:00:00',
    5,
    'ديوان الوزارة بالرياض مخرج 9 مبنى رقم 15 الدور الثالث سكرتير لجنة فتح العروض',
    NULL
);

-- Insert into tender_keywords
-- Links the tender to the keyword (assumes tender_id = 1 and keyword_id = 1)
INSERT INTO tender_keywords (tender_id, keyword_id)
VALUES (
    1,
    1
);



-- Second Example ---------------------
-- Assuming the above insert assigns id=3 to this classification

-- Insert into etimad_classification_keywords
-- Adds the keyword 'Cisco Networking' linked to the classification (classification_id=3)
INSERT INTO etimad_classification_keywords (classification_id, keyword_en, keyword_ar)
VALUES (
    1,
    'Cisco Networking', 
    'شبكات سيسكو'
);

-- Assuming the above insert assigns id=3 to this keyword

-- Insert into tenders
-- Adds the tender data for the network upgrade project
INSERT INTO tenders (
    link,
    tender_name,
    tender_number,
    reference_number,
    purpose,
    document_value,
    status,
    contract_duration,
    insurance_required,
    tender_type,
    government_entity,
    last_query_date,
    last_submission_date,
    opening_date,
    evaluation_date,
    suspension_period,
    expected_award_date,
    start_date,
    question_start_date,
    max_query_response_time,
    opening_location,
    attachment
) VALUES (
    'https://example.com/tender4',
    'Network Upgrade with Cisco Solutions',
    '109002',
    '250740056789',
    'Enhancing network infrastructure using Cisco solutions for improved reliability',
    1200.00,
    'Under Evaluation',
    '24 months',
    'نعم',
    'منافسة عامة',
    'وزارة الاتصالات',
    '2025-09-10 00:00:00',
    '2025-09-25 00:00:00',
    '2025-09-26 00:00:00',
    '2025-10-01 00:00:00',
    5,
    '2025-10-15 00:00:00',
    '2025-11-01 00:00:00',
    '2025-09-01 00:00:00',
    3,
    'مبنى وزارة الاتصالات، جدة',
    'network_upgrade_specs.pdf'
);

-- Assuming the above insert assigns id=4 to this tender

-- Insert into tender_keywords
-- Links the tender (tender_id=4) to the keyword 'Cisco Networking' (keyword_id=3)
INSERT INTO tender_keywords (tender_id, keyword_id)
VALUES (
    2,
    2
);


-- Third Example --------------------
-- Insert into etimad_classifications
-- Adds the classification 'Cloud Services' under the unit 'IT'
INSERT INTO etimad_classifications (unit, name_en, name_ar, description)
VALUES (
    'Data & Innovation', 
    'Cloud Services', 
    'خدمات السحابة', 
    'Projects related to cloud computing and services'
);

-- Assuming the above insert assigns id=5 to this classification
-- Insert into etimad_classification_keywords
-- Adds the keyword 'AWS Cloud Solutions' linked to the classification (classification_id=5)
INSERT INTO etimad_classification_keywords (classification_id, keyword_en, keyword_ar)
VALUES (
    3,
    'AWS Cloud Solutions', 
    'حلول سحابة أمازون'
);

-- Assuming the above insert assigns id=5 to this keyword
-- Insert into tenders
-- Adds the tender data for the cloud services project
INSERT INTO tenders (
    link,
    tender_name,
    tender_number,
    reference_number,
    purpose,
    document_value,
    status,
    contract_duration,
    insurance_required,
    tender_type,
    government_entity,
    last_query_date,
    last_submission_date,
    opening_date,
    evaluation_date,
    suspension_period,
    expected_award_date,
    start_date,
    question_start_date,
    max_query_response_time,
    opening_location,
    attachment
) VALUES (
    'https://example.com/tender5',
    'Cloud Migration Services',
    '110003',
    '250850067890',
    'Migrating existing services to AWS cloud for better scalability and performance',
    1500.00,
    'Under Development',
    '18 months',
    'لا',
    'منافسة عامة',
    'وزارة الاتصالات وتقنية المعلومات',
    '2025-10-01 00:00:00',
    '2025-10-15 00:00:00',
    '2025-10-16 00:00:00',
    NULL,
    7,
    '2025-11-30 00:00:00',
    '2025-12-15 00:00:00',
    '2025-09-20 00:00:00',
    4,
    'مبنى وزارة الاتصالات، الرياض',
    NULL
);

-- Assuming the above insert assigns id=5 to this tender
-- Insert into tender_keywords  
-- Links the tender (tender_id=5) to the keyword 'AWS Cloud Solutions' (keyword_id=5)
INSERT INTO tender_keywords (tender_id, keyword_id)
VALUES (
    3,
    3
);