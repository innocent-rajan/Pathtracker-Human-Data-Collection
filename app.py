import random
import string

from flask import Flask, session, render_template, request, redirect
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = str(os.getenv("secret_key"))
easy_count = int(os.getenv('easy'))
hard_count = int(os.getenv('hard'))

easy_file = 'static/sample_io.csv'
hard_file = 'static/sample_io.csv'
easy_df = pd.read_csv(easy_file)
hard_df = pd.read_csv(hard_file)

user_files = {}
user_len = 12


@app.route('/', methods=['GET'])
def hello_world():
    session.pop('user_id')
    session.pop('consent')
    session.pop('cur_idx')
    if 'consent' in session:
        if session['consent'] == 'accept':
            video_url = next_video(user_id=session['user_id'], cur=int(session['cur_idx']))
            return render_template('home.html', video_url=video_url, cur=session['cur_idx'])
    if 'cur_idx' not in session:
        session['cur_idx'] = 0
    return render_template('consent.html', cur=session['cur_idx'])


def get_video():
    user_id = str(session['user_id'])
    easy = list(easy_df.video_url.sample(n=easy_count, random_state=1).tolist())
    hard = list(hard_df.video_url.sample(n=hard_count, random_state=1).tolist())
    merged = easy + hard
    sequence = list(range(0, 10))
    random.shuffle(sequence)
    response = [-1] * 10
    # print(response)
    user_files[user_id] = {'easy': list(easy_df.video_url.sample(n=easy_count, random_state=1).tolist()),
                           'hard': list(hard_df.video_url.sample(n=hard_count, random_state=1).tolist()),
                           'merged': merged, 'sequence': sequence, 'response': response}


@app.route('/home', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        session['consent'] = request.form['consent']
        try:
            session['cur_idx'] = request.form['cur']
        except KeyError:
            session['cur_idx'] = 0
        if session['consent'] == 'accept':
            user_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=user_len))
            session['user_id'] = user_id
            if user_id not in user_files:
                get_video()
            video_url = next_video(user_id=session['user_id'], cur=int(session['cur_idx']))
            return render_template('home.html', video_url=video_url, cur=session['cur_idx'],
                                   total=easy_count + hard_count)
        else:
            return render_template('consent.html', message='Please consent before proceeding.')
    else:
        if 'consent' in session:
            if session['consent'] == 'accept':
                if session['user_id'] not in user_files:
                    get_video()
                video_url = next_video(user_id=session['user_id'], cur=int(session['cur_idx']))
                return render_template('home.html', video_url=video_url, cur=session['cur_idx'],
                                       total=easy_count + hard_count)
            else:
                return render_template('consent.html', message='Please consent before proceeding.')
        else:
            return render_template('consent.html', message='Please consent before proceeding.')


def next_video(user_id, cur):
    return user_files[user_id]['merged'][cur]


@app.route('/next', methods=['POST'])
def next_():
    user_id = session['user_id']
    cur = session['cur_idx']
    user_files[user_id]['response'][cur] = request.form['response']
    if cur + 1 < easy_count + hard_count:
        session['cur_idx'] = cur + 1
        return redirect('/home')
    else:
        df = pd.DataFrame()
        # user_files[session['user_id']]['easy'][0]
        for i in range(easy_count + hard_count):
            df = df.append(pd.Series(
                [user_id, user_files[user_id]['merged'][user_files[user_id]['sequence'][i]],
                 user_files[user_id]['response'][i]]), ignore_index=True)
            df.to_csv('static/user_files/'+user_id+'.csv', header=['user_id', 'video_link', 'response'], index=False)
        return f'Thank you for participating, your unique id is {user_id}'


if __name__ == '__main__':
    app.run()
