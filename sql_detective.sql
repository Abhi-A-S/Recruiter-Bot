-- Part 2 — The SQL Detective Challenge

-- 1. List all currently open job postings, along with the name of the recruiter who owns each one.
SELECT
    jp.id AS "Job ID",
    jp.title AS "Job Title",
    jp.department AS "Department",
    r.name AS "Recruiter Name"
FROM job_postings jp
JOIN recruiters r ON jp.recruiter_id = r.id
WHERE jp.status = 'open'
ORDER BY jp.id;

-- 2. For each job posting, how many applicants reached the Final interview stage?
SELECT
    jp.id AS "Job ID",
    jp.title AS "Job Title",
    COUNT(DISTINCT i.applicant_id) AS "Applicant Count"
FROM job_postings jp
LEFT JOIN interviews i
    ON jp.id = i.job_posting_id
    AND i.stage = 'Final'
GROUP BY jp.id, jp.title
ORDER BY jp.id;

-- 3. Find every person who effectively applied to more than one job posting.
SELECT
    LOWER(TRIM(a.email)) AS "Email",
    MIN(a.full_name) AS "Name",
    COUNT(DISTINCT i.job_posting_id) AS "Application Count",
    GROUP_CONCAT(DISTINCT i.job_posting_id) AS "Jobs Applied To"
FROM applicants a
JOIN interviews i ON a.id = i.applicant_id
GROUP BY LOWER(TRIM(a.email))
HAVING COUNT(DISTINCT i.job_posting_id) > 1
ORDER BY "Name";

-- 4. For each recruiter, compute their Final-stage conversion rate
SELECT
    r.id AS "Recruiter ID",
    r.name AS "Recruiter Name",
    COUNT(*) AS "Total Final Interviews",
    SUM(CASE WHEN i.outcome = 'passed' THEN 1 ELSE 0 END) AS passed_final_interviews,
    ROUND(
        SUM(CASE WHEN i.outcome = 'passed' THEN 1.0 ELSE 0.0 END) / COUNT(*),
        2
    ) AS "Conversion Rate"
FROM recruiters r
JOIN job_postings jp ON r.id = jp.recruiter_id
JOIN interviews i ON jp.id = i.job_posting_id
WHERE i.stage = 'Final'
GROUP BY r.id, r.name
HAVING COUNT(*) >= 3
ORDER BY "Conversion Rate" DESC, r.name ASC;

-- 5. Using a window function, find the recruiter with the most successful placements per department.
WITH department_recruiter_placements AS (
    SELECT
        jp.department,
        r.id AS recruiter_id,
        r.name AS recruiter_name,
        COUNT(i.id) AS successful_placements,
        DENSE_RANK() OVER (
            PARTITION BY jp.department
            ORDER BY COUNT(i.id) DESC
        ) AS rank_in_department
    FROM recruiters r
    JOIN job_postings jp ON r.id = jp.recruiter_id
    JOIN interviews i ON jp.id = i.job_posting_id
    WHERE i.stage = 'Final' AND i.outcome = 'passed'
    GROUP BY jp.department, r.id, r.name
)
SELECT
    department as "Department",
    recruiter_id as "Recruiter ID",
    recruiter_name as "Recruiter Name",
    successful_placements as "Successful Placements"
FROM department_recruiter_placements
WHERE rank_in_department = 1
ORDER BY "Department";