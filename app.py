from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO, join_room, emit
import random
import os
import google.generativeai as genai

GOOGLE_API_KEY = "AIzaSyD8DpGZteOzYzhVf4IVVTbyuL5NddS3obI"

model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)
socketio = SocketIO(app)

rooms = {}

# -----------------------------
# [NEW] 루트에서 client.html 띄우기
@app.route('/')
def index():
    return send_from_directory('static', 'client.html')
# -----------------------------

@socketio.on('join')
def handle_join(data):
    room = data['room']
    username = data['username']
    join_room(room)
    if room not in rooms:
        response = model.generate_content("스무고개 놀이를 하려고 해 쉬움 난이도의 동물 이름을 하나만 말해줘 다른 미사여구 붙이지 말고 딱 이름만 정확하게 말해줘")
        rooms[room] = {'word': response.text,'categorie': "동물", 'difficulty': '쉬움'}
    emit('message', {'msg': f"{username}님이 입장했습니다."}, room=room)

@socketio.on('categorie')
def categorie_change(data):
    room = data['room']
    categorie = data['categorie']
    username = data['username']
    difficulty = rooms[room]['difficulty']

    response = model.generate_content("스무고개 놀이를 하려고 해 " + difficulty +" 난이도의 " + categorie + " 이름을 하나만 말해줘 다른 미사여구 붙이지 말고 딱 이름만 정확하게 말해줘")
    rooms[room] = {'word': response.text, 'categorie': categorie, 'difficulty': difficulty}

    emit('message', {'msg': f"카테고리가 {categorie}로 변경되었습니다."}, room=room)

@socketio.on('difficulty')
def difficulty_change(data):
    room = data['room']
    categorie = rooms[room]['categorie']
    difficulty = data['difficulty']
    username = data['username']

    response = model.generate_content("스무고개 놀이를 하려고 해" + difficulty + " 난이도의" + categorie + " 이름을 하나만 말해줘 다른 미사여구 붙이지 말고 딱 이름만 정확하게 말해줘")
    rooms[room] = {'word': response.text, 'categorie': categorie, 'difficulty': difficulty}

    #emit('message', {'msg': f"난이도가 {difficulty}로 변경되었습니다."}, room=room)

@socketio.on('ask')
def handle_question(data):
    room = data['room']
    question = data['question']
    response = model.generate_content(question + "에" + rooms[room]['word'] + "가 해당하니? 다른 미사여구 붙이지 말고 예, 아니오로 답해줘")
    answer = response.text

    emit('answer', {'question': question, 'answer': answer}, room=room)

@socketio.on('guess')
def handle_guess(data):
    room = data['room']
    guess = data['guess']
    username = data['username']
    if data['guess'] == "포기":
        emit('result', {'msg': f"정답은 ( {rooms[room]['word']})입니다."})
        return
    response = model.generate_content(guess + "와 " + rooms[room]['word'] + "가 같은 뜻을 나타내는 단어야? 다른 미사여구 붙이지 말고 yes나 no중 하나로 답해줘.")
    if len(response.text) == 4:
        emit('result', {'msg': f"{username}님이 정답을 맞혔습니다! ( {rooms[room]['word']})"}, room=room)
    else:
        emit('result', {'msg': f"{username}님의 정답 시도 실패! ( {guess} )"}, room=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
