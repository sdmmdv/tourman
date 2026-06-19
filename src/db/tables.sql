DROP TABLE IF EXISTS Players CASCADE;
DROP TABLE IF EXISTS Results CASCADE;
DROP TABLE IF EXISTS Standings CASCADE;

CREATE TABLE Players (
    id VARCHAR(25) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL
);


CREATE TABLE Results (
    round_id INTEGER NOT NULL,
    player1_id VARCHAR(25) REFERENCES Players(id) NOT NULL,
    player1_name VARCHAR(255) NOT NULL,
    player1_score DECIMAL(2,1) NOT NULL,
    player2_score DECIMAL(2,1),
    player2_name VARCHAR(255),
    player2_id VARCHAR(25) REFERENCES Players(id),
    CONSTRAINT one_result_per_player CHECK (player1_id != player2_id)
);

CREATE TABLE Standings (
    id VARCHAR(25) REFERENCES Players(id),
    name VARCHAR(255),
    is_active BOOLEAN,
    is_bye BOOLEAN,
    matches INTEGER NOT NULL,
    tiebreaker_C DECIMAL(8,2),
    tiebreaker_B DECIMAL(8,2),
    tiebreaker_A DECIMAL(8,2),
    points DECIMAL(4,1),
    PRIMARY KEY (id)
);