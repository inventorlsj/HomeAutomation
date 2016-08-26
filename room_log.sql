drop table if exists room_log;
create table room_log (
  id integer primary key autoincrement,
  check_datetime string not null,
  temperature integer not null,
  humidity integer not null,
  air_state integer not null
);