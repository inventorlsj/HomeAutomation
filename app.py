# from sht_sensor import Sht
from __future__ import with_statement
from contextlib import closing
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g
import datetime
import threading
import time

# configuration
DATABASE = 'log.db'
MYPASSWORD = '7061lsj'

# default value
temperature = None
humidity = None
thre_t = 25
thre_rh = 50
wait_time = 3 # 시
run_time = 10 # 분
air_state = False  # False: 꺼짐, True: 켜짐
control_mode = True  # None
develop_air_state = False
error = None

app = Flask(__name__)
app.config.from_object(__name__)
# sht = Sht(11, 17)

def connect_db():
   return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('room_log.sql') as f:
            db.cursor().executescript(f.read().decode(encoding='utf-8'))
        db.commit()

def init_db2():
    with closing(connect_db()) as db:
        with app.open_resource('setting_log.sql') as f:
            db.cursor().executescript(f.read().decode(encoding='utf-8'))
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    g.db.close()

@app.route('/')
def room_state():
   global temperature, humidity, air_state, control_mode, error
   # t = sht.read_t()
   # rh = sht.read_rh(t)

   now = datetime.datetime.now()
   timeString = now.strftime("%Y-%m-%d %H:%M:%S")
   templateData = {
      'title' : 'HELLO!',
      'time' : timeString,
      't': temperature,
      'rh': humidity,
      'air_state': air_state,
      'control_mode': control_mode,
      'error': error
      }
   error = None
   return render_template('main.html', **templateData)

@app.route('/seting')
def seting():
   global  thre_t, thre_rh, wait_time, run_time, error

   templateData = {
      'error' : error,
      'thre_t': thre_t,
      'thre_rh': thre_rh,
      'wait_time': wait_time,
      'run_time': run_time
      }

   error = None

   return render_template('seting.html', **templateData)

@app.route('/control', methods=['POST'])
def control():
   global error, air_state, control_mode
   error = None

   if request.form['password'] != app.config['MYPASSWORD']:
      error = '암호가 틀리다.'
   else:
      if request.form['but'] == 'air':
         air_state = not air_state
      if request.form['but'] == 'mode':
         control_mode =  not control_mode
         now = datetime.datetime.now()
         timeString = now.strftime("%Y-%m-%d %H:%M:%S")
         g.db.execute(
            'insert into setting_log (datetime, temperature, humidity, wait_time, run_time, control_mode) values (?, ?, ?, ?, ?, ?)',
            [timeString, thre_t, thre_rh, wait_time, run_time, control_mode])
         g.db.commit()

   return redirect(url_for('room_state'))

@app.route('/set_change', methods=['POST'])
def set_change():
   global thre_t, thre_rh, wait_time, run_time, control_mode, error

   error = None

   if request.method == 'POST':
      if request.form['password'] != app.config['MYPASSWORD']:
         error = '암호가 틀리다.'
      else:
         thre_t = int(request.form['set_thre_t'])
         thre_rh = int(request.form['set_thre_rh'])
         wait_time = int(request.form['set_wait_time'])
         run_time = int(request.form['set_run_time'])

         now = datetime.datetime.now()
         timeString = now.strftime("%Y-%m-%d %H:%M:%S")
         g.db.execute('insert into setting_log (datetime, temperature, humidity, wait_time, run_time, control_mode) values (?, ?, ?, ?, ?, ?)',
                      [timeString, thre_t, thre_rh, wait_time, run_time,control_mode])
         g.db.commit()

   return redirect(url_for('seting'))

def set_read():
   global thre_t, thre_rh, wait_time, run_time, control_mode

   db = connect_db()
   cur = db.execute('select * from setting_log order by id desc limit 1')
   row = cur.fetchall()

   if len(row) < 1 :
      now = datetime.datetime.now()
      timeString = now.strftime("%Y-%m-%d %H:%M:%S")
      db.execute('insert into setting_log (datetime, temperature, humidity, wait_time, run_time, control_mode) values (?, ?, ?, ?, ?, ?)',
         [timeString, thre_t, thre_rh, wait_time, run_time, control_mode])
      db.commit()
   else:
      thre_t = row[0][2]
      thre_rh = row[0][3]
      wait_time = row[0][4]
      run_time = row[0][5]
      control_mode = row[0][6]


@app.route('/add_test')
def add_test():
   now = datetime.datetime.now()
   timeString = now.strftime("%Y-%m-%d %H:%M:%S")

   # sir_stat = {0:'꺼짐', 1:'켜짐', 2:'막 꺼짐', 3:'막 켜짐'}
   g.db.execute('insert into room_log (check_datetime, temperature, humidity, air_state) values (?, ?, ?, ?)',
                 [timeString, now.hour, now.minute, now.second % 4])

   g.db.commit()
   # flash('New entry was successfully posted')
   return redirect(url_for('state_log/0'))

@app.route('/state_log')
@app.route('/state_log/<int:page>')
def state_log(page=1):
   if page < 1: page = 1
   offset = (page - 1) * 50

   cur = g.db.execute('select * from room_log order by id desc limit 50 offset (?)',[offset]) #check_datetime, temperature, humidity, air_state
   entries = [dict(check_datetime=row[1], temperature=row[2], humidity=row[3], air_state=row[4]) for row in cur.fetchall()]

   nextpage = page + 1
   if len(entries) < 50: nextpage = 0
   prepage = page - 1

   return render_template('state_log.html', entries=entries, prepage = prepage, nextpage = nextpage)

def ir_commend():
   return True


# 반환 값 - False: 꺼짐, True: 켜짐
def air_check():
   if develop_air_state:
      return 1
   else :
      return -1

def air_commend_trans(control):
   if air_check() != control:
      if control > 0:
         print('켜저라')
      else:
         print('꺼져라')
      return ir_commend()
   else:
      return False

# 반환값 (온도, 습도)
def sensor_sensing():
   # 개발용 - 온습도 현제 시간으로
   now = datetime.datetime.now()
   return [20, now.second]

# 주기적으로 온습도를 측정하여 DB에 저장
def event_loop(checkTime):
   global temperature, humidity, thre_t, thre_rh, air_state, wait_time, run_time

   pre_now = datetime.datetime.now()
   air_onoff_period = 0 # -1: 꺼질 때, 1: 켜질 때, 0: 시작
   until_time = datetime.timedelta(seconds=86000) # 24시간이 넘어가면 seconds가 0이된다.

   # operate_state = {-5:'꺼라 함', -4:'다시 끔', -3:'그냥 꺼짐', -2:'꺼짐', -1:'막 꺼짐', 0:, 1:'막 켜짐', 2:'켜짐', 3:'그냥 켜짐', 4:'다시 켬', 5:'꺼라 함'}
   operate_state = -2
   if air_check() > 0:
      operate_state = 2
   pre_operate_state = operate_state

   while True:
      [temperature, humidity] = sensor_sensing()
      now = datetime.datetime.now()
      air_state = air_check()

      if (temperature >= thre_t or humidity >= thre_rh) and 1 != air_onoff_period and until_time.seconds > wait_time*60:
         air_onoff_period = 1
         print("켜질 때", operate_state)
      elif (temperature < thre_t and humidity < thre_rh) and -1 != air_onoff_period and until_time.seconds > run_time*60:
         air_onoff_period = -1
         print("꺼질 때", operate_state)

      if air_onoff_period == air_state:
         if 5 == abs(operate_state):
            if air_state > 0:
               operate_state = 1
            else:
               operate_state = -1
            until_time = datetime.timedelta(seconds=0)
         elif 1 == abs(operate_state) or 4 == abs(operate_state):
            if air_state > 0:
               operate_state = 2
            else:
               operate_state = -2
         elif 3 == abs(operate_state):
            if air_state > 0:
               operate_state = 4
            else:
               operate_state = -4
         until_time = (now - pre_now) + until_time
      else:
         if operate_state == 2 :
            if air_state < 0:
               operate_state = 3
            elif air_onoff_period < 0:
               operate_state = 5
         elif operate_state == -2:
            if air_state > 0:
               operate_state = -3
            elif air_onoff_period > 0:
               operate_state = -5

      pre_now = now

      if abs(operate_state) == 3 or abs(operate_state) == 5:
         air_commend_trans(air_onoff_period)

      db_commend = 0
      db_commend_string = {-4:'다시 끔', -3:'그냥 켜짐', -2:'꺼짐', -1:'막 꺼짐',  1:'막 켜짐', 2:'켜짐', 3:'그냥 꺼짐', 4:'다시 켬'}

      flag_db = False
      if operate_state != pre_operate_state and (abs(operate_state) == 1 or abs(operate_state) == 3 or abs(operate_state) == 4):
         pre_operate_state = operate_state
         db_commend = operate_state
         flag_db = True
      elif now.second % checkTime == 0:
         db_commend = 2 * air_state
         flag_db = True

      timeString = now.strftime("%Y-%m-%d %H:%M:%S")

      [temperature, humidity] = sensor_sensing()
      if flag_db:
         db = connect_db()
         #DB 입력 값: air_state = {0: '다시 끔', 1: '그냥 켜짐', 2: '꺼짐', 3: '막 꺼짐', 4: '시작', 5: '막 켜짐', 6: '켜짐', 7: '그냥 꺼짐', 8: '다시 켬'}
         db.execute('insert into room_log (check_datetime, temperature, humidity, air_state) values (?, ?, ?, ?)',
                    [timeString, temperature, humidity,db_commend+4 ])
         db.commit()
         db.close()

         print(temperature, humidity, "ut-", until_time, db_commend_string[db_commend] )

      time.sleep(1)

#개발용
@app.route('/develop', methods=['POST', 'GET'])
def develop():
   global develop_air_state

   if request.method == 'POST':
      if request.form['but'] == 'air':
         develop_air_state = not develop_air_state
         print('에어컨 상태 수동 제어', develop_air_state)

   return render_template('develop.html')

if __name__ == "__main__":
   #app.run()
   # 쓰레드로 온습도를 측정하는 함수를 따로 돌린다
   set_read()

   [temperature, humidity] = sensor_sensing()
   timeString = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
   db = connect_db()
   db.execute('insert into room_log (check_datetime, temperature, humidity, air_state) values (?, ?, ?, ?)',
              [timeString, temperature, humidity, 4])
   db.commit()
   db.close()

   t = threading.Thread(target=event_loop, args=(5,))
   t.start()

   app.run(host='0.0.0.0', port=8080, debug=False)

