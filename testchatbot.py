from flask import *
from dbconnection import *
from flask_socketio import SocketIO


app = Flask(__name__)
app.secret_key="abc"

socketio = SocketIO(app)

@app.route('/',methods=['get','post'])
def page():
    return render_template('login.html')




@app.route('/reg',methods=['get','post'])
def reg():
    return render_template('register.html')


@app.route('/home',methods=['get','post'])
def home():
    return render_template('home_page.html')

@app.route('/register',methods=['post'])
def register():
    uname = request.form['name']
    pswd = request.form['password']

    res = selectone("select * from `user` where uname=%s",uname)
    if res:
        return '''<script>alert("Username already Exist");window.location="/"</script>'''
    else:
        iud("insert into `user` values(null,%s,%s,%s)",(uname,pswd,'pending'))
        return '''<script>alert("Registered Sucessfully");window.location="/"</script>'''


@app.route('/login',methods=['post'])
def login():
    uname = request.form['username']
    pswd = request.form['password']
    res = selectone("select * from `user` where uname=%s and passwrd=%s",(uname,pswd))
    if res is not None:
        session['lid']=res['id']
        iud("update `user` set `status`='active' where id=%s",res['id'])
        return '''<script>alert("Login Success");window.location="/home"</script>'''
    else:
        return '''<script>alert("Incorrect username or password");window.location="/"</script>'''







@app.route('/add_chatroom',methods=['get','post'])
def add_chatroom():

    if request.method=="POST":
        room = request.form['room']
        iud("insert into room values(null,%s,%s)",(room,session['lid']))
        return '''<script>alert("Added Successfully");window.location="/add_chatroom"</script>'''



    res = selectall2("select * from room where uid=%s",session['lid'])
    return render_template('add_chatroom.html',data = res)




@app.route('/delete_room',methods=['get','post'])
def delete_room():
    id = request.args.get('id')
    iud("delete from room where id = %s",id)
    return '''<script>alert("Deleted Successfully");window.location="/add_chatroom"</script>'''


@app.route('/view_chatroom',methods=['get','post'])
def view_chatroom():
    res1  =selectall2("select * from room where uid=%s",session['lid'])
    res = []
    for i in res1:
        i['status']='accepted'
        res.append(i)
    print(res)
    res2 = selectall2("select *,room.id as rid from room left join room_request on room.id=room_request.roomid where room.uid!=%s",(session['lid']))
    return render_template('view_room.html', data=res,data2 = res2)



@app.route('/approve_roomreq',methods=['get','post'])
def approve_roomreq():
    res = selectall2("select user.uname,room_request.id,room.room,room_request.status from room_request join room on room_request.roomid=room.id join `user` on room_request.uid=user.id where room.uid=%s",(session['lid']))
    return render_template('approve_joinrequest.html',data=res)



@app.route('/acceptjoinrequest',methods=['get','post'])
def acceptjoinrequest():
    id = request.args.get('id')
    iud("update room_request set status='accepted' where id=%s",id)
    return '''<script>alert("Accepted Successfully");window.location="/approve_roomreq"</script>'''



@app.route('/send_joinreq',methods=['get','post'])
def send_joinreq():
    id = request.args.get('id')

    res = selectone("select * from room_request where roomid=%s and uid = %s",(id,session['lid']))
    if res is  None:
        iud("insert into room_request values(null,%s,%s,'pending')",(id,session['lid']))
        return '''<script>alert("Request send Successfully");window.location="/view_chatroom"</script>'''
    else:
        return '''<script>alert("Already Requested");window.location="/view_chatroom"</script>'''


@app.route('/logout',methods=['get','post'])
def logout():
    iud("update `user` set `status`='inactive' where id=%s",session['lid'])
    return '''<script>alert("Logout Success");window.location="/"</script>'''


@app.route('/chat_page',methods=['get','post'])
def chat_page():
    id = request.args.get('id')
    session['rid'] = id
    admin = selectone("select user.uname,user.status from room join `user` on room.uid=user.id where room.id=%s",id)
    res = selectall2("select user.uname,user.status from room_request join `user` on room_request.uid=user.id where room_request.roomid=%s",id)
    # chat_messages = selectall2("select * from message where roomid=%s",id)
    return render_template('chat.html',user=res,rid=id,admin=admin)


@app.route("/chat_usr_chk",methods=['get','post'])        # refresh messages chatlist
def chat_usr_chk():
    roomid = request.args.get('id')
    chat_messages = selectall2("select message.*,user.uname from message join `user` on message.uid=user.id where message.roomid=%s", roomid)
    print("eeeeeee")
    return jsonify(chat_messages)



@app.route("/chat_usr_post",methods=['get','post'])        # refresh messages chatlist
def chat_usr_post():
    message = request.form['message']
    roomid = session['rid']

    if is_offensive(message):
        print('Offensive content detected!')
        return redirect(url_for('chat_page', id=session['rid']))
    else:
        iud("insert into message (uid,roomid,message,time) values(%s,%s,%s,curtime())", (session['lid'],roomid,message))
        print("eeeeeee")
        # return render_template("chat.html",toid = session['rid'])
        return redirect(url_for('chat_page', id= session['rid']))




from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()
def is_offensive(text):
    sentiment = analyzer.polarity_scores(text)
    compound_score = sentiment['compound']
    if compound_score < -0.5:
        return True
    return False

@app.route('/logout1',methods=['get','post'])
def logout1():
    iud("update `user` set `status`='inactive' where id=%s", session['lid'])
    return redirect('/')


# app.run()
if __name__ == '__main__':
    socketio.run(app,allow_unsafe_werkzeug=True)