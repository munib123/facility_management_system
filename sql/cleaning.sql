-- 0. SELECT DATABASE AND DISABLE SAFE UPDATE MODE
-- This allows us to update rows without strict key limitations temporarily
USE database_;
SET SQL_SAFE_UPDATES = 0;

-- ====================================================
-- PART 1: CLEANING 'tasks' TABLE
-- ====================================================

-- 1.1 Handle NULL values
-- If status is missing, default it to 'Planned'
UPDATE tasks 
SET status = 'Planned' 
WHERE status IS NULL OR status = '';

-- If notes are missing, set to 'N/A'
UPDATE tasks 
SET notes = 'N/A' 
WHERE notes IS NULL;

-- 1.2 Standardize Text Formatting
-- Remove extra spaces from the start/end of text fields
UPDATE tasks 
SET task_type = TRIM(task_type),
    notes = TRIM(notes);

-- 1.3 Logic Checks
-- Duration cannot be negative. Set negative values to 0 (or you could DELETE them)
UPDATE tasks 
SET duration_mins = 0 
WHERE duration_mins < 0;

-- ====================================================
-- PART 2: CLEANING 'inspections' TABLE
-- ====================================================

-- 2.1 Handle NULL/Empty Feedback
UPDATE inspections 
SET feedback = 'No comments' 
WHERE feedback IS NULL OR feedback = '';

-- 2.2 Fix Out-of-Range Hygiene Scores
-- Hygiene score should be 1-10. If it's higher than 10, cap it at 10.
UPDATE inspections 
SET hygiene_score = 10 
WHERE hygiene_score > 10;

-- If it's lower than 1 (or negative), set it to 1.
UPDATE inspections 
SET hygiene_score = 1 
WHERE hygiene_score < 1;

-- 2.3 Standardize Text
UPDATE inspections 
SET issues_found = TRIM(issues_found),
    corrective_actions = TRIM(corrective_actions);

-- ====================================================
-- PART 3: CLEANING 'consumables' TABLE
-- ====================================================

-- 3.1 Standardize Text Case
-- Make all resource types Uppercase (e.g., 'Soap' -> 'SOAP') to avoid duplicates like 'Soap' vs 'soap'
UPDATE consumables 
SET resource_type = UPPER(TRIM(resource_type));

-- 3.2 Remove Bad Data
-- Remove rows where quantity or cost is zero or negative (useless data)
DELETE FROM consumables 
WHERE quantity_used <= 0 OR total_cost <= 0;

-- ====================================================
-- PART 4: REMOVING DUPLICATES (Advanced)
-- ====================================================
-- Note: Run this ONLY if you don't have a Primary Key set yet. 
-- If you already created the tables with the Primary Keys I gave you earlier, 
-- the database would have automatically prevented duplicates.

-- Example for 'consumables' (Finding and deleting exact duplicates based on date, location, and resource)
DELETE t1 FROM consumables t1
INNER JOIN consumables t2 
WHERE 
    t1.usage_id < t2.usage_id AND 
    t1.usage_date = t2.usage_date AND 
    t1.location_id = t2.location_id AND 
    t1.resource_type = t2.resource_type;

-- ====================================================
-- 5. RE-ENABLE SAFE UPDATE MODE
-- ====================================================
SET SQL_SAFE_UPDATES = 1;

-- Check your results
SELECT * FROM tasks LIMIT 10;
SELECT * FROM inspections LIMIT 10;
SELECT * FROM consumables LIMIT 10;