from flask import Flask
from flask import request
from aaologinandgetpages import *
from flaskfilelock import Lock
app = Flask(__name__)
app.lock = Lock.get_file_lock()


demo_html = '''
<!DOCTYPE HTML><html><head><meta charset="UTF-8"/>
<title>DEMO</title></head><body onload="addnewline()">
<form action='/' method='post' onsubmit="return getjsonstr()" >
<input name="data" style="display: none" id="jsonstr" />
<span>学号</span><input id='student_id' type='text' /><br/>
<span>密码</span><input id='password' type='password' /><br/>
<input type='submit' /><br/></form><script>var line_con = -1;function addnewline(){
line_con ++;var newdiv = document.createElement("div");
newdiv.setAttribute('id','line'+line_con);
var newinput = document.createElement('input');newinput.setAttribute('type','text');
newinput.setAttribute('id','text'+line_con);newdiv.appendChild(newinput);
lines.appendChild(newdiv);}function minusnewline(){if(line_con === 0)return;
lines.removeChild(document.getElementById('line'+line_con--));}
function getjsonstr() {res = {};res.student_id = student_id.value;
res.password = password.value;jsonstr.value = JSON.stringify(res);}</script></body></html>
'''


@app.route('/DEMO', methods=['GET', 'POST'])
def demo_page():
    return demo_html, 200, {'Content-Type': 'text/html'}


@app.route('/', methods=['GET', 'POST'])
def login_and_get_pages_api_caller():
    # print(request.form.to_dict())
    if 'data' in request.form:
        json_str = request.form['data']
        # print(request.form['data'])
        app.lock.acquire()
        print('in')
        res = login_and_get_pages_api(json_str)
        app.lock.release()
        print('out')
        return res, 200, {'Content-Type': 'text/html; charset=utf-8'}
    return '', 400, {'Content-Type': 'text/plain'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1999, threaded=True)
