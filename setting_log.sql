drop table if exists setting_log;
create table setting_log (
  id integer primary key autoincrement,
  datetime string not null,
  temperature integer not null,
  humidity integer not null,
  wait_time integer not null,
  run_time integer not null,
  control_mode integer not null
);