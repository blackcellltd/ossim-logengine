create database logarchive;
CREATE TABLE logarchive.new_ids (id BINARY(16) PRIMARY KEY);
DELIMITER $$
CREATE TRIGGER id_copier BEFORE INSERT ON alienvault_siem.acid_event FOR EACH ROW
BEGIN
    INSERT INTO logarchive.new_ids VALUES (NEW.id);
END $$
DELIMITER ;
INSERT IGNORE logarchive.new_ids (id) SELECT alienvault_siem.acid_event.id FROM alienvault_siem.acid_event;
CREATE USER ossim_logserver@127.0.0.1 IDENTIFIED BY 'USR_PW';
GRANT ALL PRIVILEGES on logarchive.new_ids TO ossim_logserver@127.0.0.1;
GRANT SELECT ON alienvault.plugin TO ossim_logserver@127.0.0.1;
GRANT SELECT ON alienvault.plugin_sid TO ossim_logserver@127.0.0.1;
GRANT SELECT ON alienvault_siem.extra_data TO ossim_logserver@127.0.0.1;
GRANT SELECT ON alienvault_siem.acid_event TO ossim_logserver@127.0.0.1;