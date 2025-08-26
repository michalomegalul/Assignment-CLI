INSERT INTO domain (fqdn, registered_at, unregistered_at) VALUES
('example.com', '2024-01-01 00:00:00+00', NULL),
('test.org', '2024-02-01 00:00:00+00', NULL),
('expired-domain.net', '2023-01-01 00:00:00+00', '2024-01-01 00:00:00+00'),
('active-domain.com', '2024-03-01 00:00:00+00', NULL),
('flagged-domain.org', '2024-01-15 00:00:00+00', NULL);


INSERT INTO domain_flag (domain_id, flag, valid_from, valid_to) VALUES

(3, 'EXPIRED', '2024-01-01 00:00:00+00', NULL),

(5, 'OUTZONE', '2024-02-01 00:00:00+00', NULL),

(5, 'EXPIRED', '2024-02-15 00:00:00+00', '2024-03-01 00:00:00+00'),

(3, 'DELETE_CANDIDATE', '2024-01-02 00:00:00+00', NULL);

SELECT d.fqdn
FROM domain d
WHERE d.unregistered_at IS NULL
  AND d.id NOT IN (
    SELECT df.domain_id 
    FROM domain_flag df 
    WHERE df.flag = 'EXPIRED' 
        AND df.valid_to IS NULL
  )
ORDER BY d.fqdn;

SELECT DISTINCT d.fqdn
FROM domain d
JOIN domain_flag df1 ON d.id = df1.domain_id
JOIN domain_flag df2 ON d.id = df2.domain_id
WHERE df1.flag = 'EXPIRED'
  AND df2.flag = 'OUTZONE'
ORDER BY d.fqdn;