from flask_socketio import SocketIO, disconnect
from flask import session, request
from collections import defaultdict
from main import app

socketio = SocketIO(app)

# === Real-time quiz logic ===
live_results = defaultdict(int)
correct_answer = None
player_scores = {}
player_names = {}
last_answers = {} 
current_question = None

@socketio.on('connect')
def on_connect():
    if request.sid in player_names:
        print(f"{player_names[request.sid]} connected")
    else:
        print(f"Unknown user connected: {request.sid}")

@socketio.on('register_name')
def handle_register_name(name):
    sid = request.sid
    player_names[sid] = name[0:20]
    player_scores[sid] = 0

    if current_question:
        socketio.emit('broadcast_question', current_question)

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    player_scores.pop(sid, None)
    player_names.pop(sid, None)

@socketio.on('get_active_players')
def handle_get_active_players():
    player_list = [
        {'sid': sid, 'name': name}
        for sid, name in player_names.items()
    ]
    socketio.emit('active_players', player_list, to=request.sid)

@socketio.on('kick_player')
def handle_kick_player(data):
    sid_to_kick = data.get('sid')
    reason = data.get('reason', 'You have been kicked by the host.')
    if sid_to_kick in player_names:
        print(f"Kicking player: {player_names[sid_to_kick]} - Reason: {reason}")
        socketio.emit('kick_notice', {'reason': reason}, to=sid_to_kick)
        disconnect(sid_to_kick)

@socketio.on("message")
def handle_message(msg):
    print(msg)

@socketio.on('new_question')
def handle_new_question(data):
    global live_results, correct_answer, current_question
    if current_question:
        socketio.emit('error_message', {'error': 'You must release the current question first.'})
        return

    print("Broadcasting question:", data)
    current_question = data
    live_results = defaultdict(int)
    correct_answer = data['correct']
    socketio.emit('broadcast_question', data)

@socketio.on('clear_question')
def handle_clear_question():
    global current_question, live_results, correct_answer, last_answers
    print("Clearing current question")
    current_question = None
    live_results.clear()
    correct_answer = None
    last_answers.clear()
    socketio.emit('clear_question_ack')

@socketio.on('player_answer')
def handle_player_answer(answer):
    print("Updating live results...")
    sid = request.sid
    last_answers[sid] = answer 

    live_results[answer] += 1

    socketio.emit('live_results', dict(live_results))

@socketio.on('reveal_answer')
def handle_reveal_answer():
    global current_question
    print("Revealing answers")

    socketio.emit('answer_reveal', {'correct': correct_answer})

    choice_counts = defaultdict(int)
    for ans in last_answers.values():
        choice_counts[ans] += 1

    correct_sids_ordered = [
        sid for sid, ans in last_answers.items()
        if ans == correct_answer and sid in player_names
    ]
    player_points_this_round = {}

    for i, sid in enumerate(correct_sids_ordered):
        points = max(30 - i, 1)
        player_scores[sid] += points
        player_points_this_round[sid] = points

    for sid in player_names:
        socketio.emit('answer_summary', {
            'correct': correct_answer,
            'your_answer': last_answers.get(sid),
            'your_points': player_points_this_round.get(sid, 0),
            'answer_counts': dict(choice_counts)
        }, room=sid)

    leaderboard = [
        {'name': player_names[sid], 'score': player_scores[sid]}
        for sid in player_scores if sid in player_names
    ]
    leaderboard.sort(key=lambda x: x['score'], reverse=True)

    correct_count = len(correct_sids_ordered)
    total = len(player_names)
    percent_correct = int((correct_count / total) * 100) if total else 0

    socketio.emit('leaderboard_update', {
        'leaderboard': leaderboard,
        'percent_correct': percent_correct
    })

    current_question = None
    last_answers.clear()

@socketio.on('reset_leaderboard')
def handle_reset_leaderboard():
    global player_scores
    print("Resetting leaderboard")
    for sid in player_scores:
        player_scores[sid] = 0
    socketio.emit('leaderboard_reset')