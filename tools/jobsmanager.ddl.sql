USE workflow;

DROP TABLE IF EXISTS jm_syslog;
DROP TABLE IF EXISTS jm_update_info;
DROP TABLE IF EXISTS jm_jobs;

CREATE TABLE IF NOT EXISTS jm_syslog (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    level VARCHAR(16) NOT NULL,
    logger_name VARCHAR(64) NOT NULL,
    message TEXT NOT NULL,
    PRIMARY KEY (id),
    KEY idx_created_at (created_at),
    KEY idx_level (level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE jm_update_info (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  updated TINYINT(1) NOT NULL DEFAULT 0,
  insert_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  jobs_before_update JSON NULL,
  jobs_after_update JSON NULL,
  PRIMARY KEY (id),
  KEY idx_updated_insert_time (updated, insert_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

