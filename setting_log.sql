drop table if exists setting_log;
create table setting_log (
  id integer primary key autoincrement,
  datetime string not null,
  temperature integer not null,
  humidity integer not null,
  set_wait_time integer not null,
  set_runTime_min integer not null,
  set_runTime_max integer not null,
  control_mode integer not null
);