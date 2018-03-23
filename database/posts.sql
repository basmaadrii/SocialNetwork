DELIMITER $$

CREATE TABLE `SocialNetwork`.`posts` (
  `post_id` VARCHAR(100) NULL,
  `user_id` BIGINT NULL,
  `post_message` VARCHAR(100) NULL,
  `created_time` TIMESTAMP NULL,
  PRIMARY KEY (`post_id`));


CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_createPost`(
    IN p_id VARCHAR(100),
    IN u_id BIGINT,
    IN message VARCHAR(100),
    IN c_time TIMESTAMP
)

BEGIN

    if ( select exists (select 1 from posts where post_id = p_id) ) THEN

        select 'post exists';

    ELSE

        insert into posts
        (
            post_id,
            user_id,
            post_message,
            created_time
        )
        values
        (
            p_id,
            u_id,
            message,
            c_time
        );

    END IF;

END$$
DELIMITER ;