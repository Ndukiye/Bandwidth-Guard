-- CREATE TABLE "user"(
-- id SERIAL PRIMARY KEY,
-- name VARCHAR(255),
-- email VARCHAR(255),
-- password TEXT,
-- age INT
-- );

-- INSERT INTO "user" (email, name, age, password) VALUES ('shoko@bla.email','Otumba lavish',20,'shokolocobangoshay');

-- -- UPDATE "user" SET age = 30 WHERE ID

-- CREATE TABLE post(
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(255),
--     content TEXT,
--     user_id INT,
--     CONSTRAINT fk_user
--         FOREIGN KEY(user_id)
--             REFERENCES "user"(id)
-- )

-- SELECT "user".*, post.id, post.name AS tile, post.content, post.user_id FROM "user" JOIN post ON post.user_id = "user".id;

CREATE TABLE process(
    id SERIAL PRIMARY KEY,
    pid INT,
    name VARCHAR(255)
);

CREATE TABLE process_logs(
    id SERIAL PRIMARY KEY,
    process_id INT REFERENCES process(id),
    bytes_in BIGINT,
    bytes_out BIGINT,
    CPU_USAGE FLOAT,
    memory_usage FLOAT,
    timestamp TIMESTAMP DEFAULT NOW()
);

INSERT INTO process(pid, name) VALUES (303,'Disney Channel'),(304,Disney Junior);
INSERT INTO process_logs(process_id,bytes_in,bytes_out,CPU_USAGE,memory_usage);
