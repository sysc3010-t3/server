create table users(
    id INTEGER PRIMARY KEY,
    name varchar(50) UNIQUE,
    salt varchar(32),
    password varchar(50)
);

create table cars(
    id integer PRIMARY KEY,
    name varchar(50),
    ip varchar(12),
    isOn integer,
    userID integer,
    FOREIGN KEY(userID) references users(id)
);
