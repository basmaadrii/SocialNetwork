DELIMITER $$

CREATE TABLE `SocialNetwork`.`users` (
  `user_id` BIGINT NULL,
  `user_name` VARCHAR(50) NULL,
  PRIMARY KEY (`user_id`));


CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_createUser`(
    IN id BIGINT,
    IN name VARCHAR(50)
)

BEGIN

    if ( select exists (select 1 from users where user_id = id) ) THEN

        select 'user exists';

    ELSE

        insert into users
        (
            user_id,
            user_name
        )
        values
        (
            id,
            name
        );

    END IF;

END$$
DELIMITER ;