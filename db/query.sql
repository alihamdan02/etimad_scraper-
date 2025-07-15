SELECT 
    t.id AS tender_id,
    t.tender_name,
    t.tender_number,
    t.status,
    t.government_entity,
    ec.name_en AS classification_name,
    eck.keyword_en AS keyword
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