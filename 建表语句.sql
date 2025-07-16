CREATE TABLE bills (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    amount DECIMAL(10,2) NOT NULL,
    notes VARCHAR(60),
    time INT NOT NULL,
    channel_id TINYINT NOT NULL,
    channel_type VARCHAR(6) NOT NULL,
    finished TINYINT(1) NOT NULL DEFAULT 0
);