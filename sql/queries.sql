-- 1. Files imported
SELECT file_id, filename, sha256, imported_at
FROM file
ORDER BY filename;

-- 2. Stations and coordinates
SELECT n.code AS network,
       s.code AS station,
       s.latitude,
       s.longitude,
       s.elevation_m,
       s.site_name
FROM station s
JOIN network n ON n.network_id = s.network_id
ORDER BY n.code, s.code;

-- 3. Trace metadata
SELECT f.filename,
       n.code AS network,
       s.code AS station,
       c.location_code,
       c.code AS channel,
       ws.start_time,
       ws.end_time,
       ws.n_samples,
       ws.sample_rate_hz,
       ws.data_min,
       ws.data_max,
       ws.data_mean
FROM waveform_segment ws
JOIN file f ON f.file_id = ws.file_id
JOIN channel c ON c.channel_id = ws.channel_id
JOIN station s ON s.station_id = c.station_id
JOIN network n ON n.network_id = s.network_id
ORDER BY f.filename, n.code, s.code, c.code;

-- 4. Required stations of interest
SELECT n.code AS network,
       s.code AS station,
       s.latitude,
       s.longitude,
       s.elevation_m,
       s.site_name
FROM station s
JOIN network n ON n.network_id = s.network_id
WHERE s.code IN ('HOA', 'SUG')
ORDER BY s.code;

-- 5. Sample count by station
SELECT n.code AS network,
       s.code AS station,
       SUM(ws.n_samples) AS total_samples
FROM waveform_segment ws
JOIN channel c ON c.channel_id = ws.channel_id
JOIN station s ON s.station_id = c.station_id
JOIN network n ON n.network_id = s.network_id
GROUP BY n.code, s.code
ORDER BY total_samples DESC;
