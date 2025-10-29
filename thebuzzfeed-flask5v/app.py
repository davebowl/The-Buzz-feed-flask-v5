
import os, sqlite3, uuid, shutil
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, g, flash, jsonify
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'instance', 'buzz.db')
UPLOADS = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOADS, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'dev-secret-change-me'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    with open(os.path.join(BASE_DIR, 'schema.sql')) as f:
        db.executescript(f.read())
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    db = get_db()
    vids = db.execute('SELECT id,title,filename,uploader,created_at,likes FROM videos ORDER BY created_at DESC').fetchall()
    return render_template('index.html', videos=vids, user=session.get('user'))

@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == 'POST':
        if 'user' not in session:
            return redirect(url_for('login'))
        f = request.files.get('file')
        title = request.form.get('title') or (f.filename if f else 'untitled')
        allow_comments = 1 if request.form.get('comments')=='on' else 0
        if not f:
            flash('No file')
            return redirect(url_for('upload'))
        fn = secure_filename(f.filename)
        vid_id = 'v_' + uuid.uuid4().hex[:10]
        outname = f"{vid_id}_{fn}"
        dest = os.path.join(UPLOADS, outname)
        f.save(dest)
        db = get_db()
        db.execute('INSERT INTO videos (id,title,filename,uploader,created_at,comments_enabled) VALUES (?,?,?,?,?,?)',
                   (vid_id, title, outname, session['user'], datetime.utcnow().isoformat(), allow_comments))
        db.commit()
        return redirect(url_for('watch', video_id=vid_id))
    return render_template('upload.html', user=session.get('user'))

@app.route('/watch/<video_id>')
def watch(video_id):
    db = get_db()
    v = db.execute('SELECT * FROM videos WHERE id=?', (video_id,)).fetchone()
    if not v:
        return 'Not found',404
    comments = db.execute('SELECT * FROM comments WHERE video_id=? AND visible=1 ORDER BY created_at DESC', (video_id,)).fetchall()
    return render_template('watch.html', video=v, comments=comments, user=session.get('user'))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOADS, filename, as_attachment=False)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cur = db.execute('SELECT username FROM users WHERE username=?', (username,)).fetchone()
        if cur:
            flash('Username taken'); return redirect(url_for('register'))
        db.execute('INSERT INTO users (username, password) VALUES (?,?)', (username, password))
        db.commit()
        flash('Account created. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        username = request.form['username']; password = request.form['password']
        db = get_db()
        cur = db.execute('SELECT username FROM users WHERE username=? AND password=?',(username,password)).fetchone()
        if cur:
            session['user']=username; return redirect(url_for('index'))
        flash('Invalid credentials'); return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None); return redirect(url_for('index'))

@app.route('/comment/<video_id>', methods=['POST'])
def comment(video_id):
    if 'user' not in session: return redirect(url_for('login'))
    text = request.form.get('text')
    db = get_db()
    db.execute('INSERT INTO comments (video_id, username, text, created_at) VALUES (?,?,?,?)',
               (video_id, session['user'], text, datetime.utcnow().isoformat()))
    db.commit()
    return redirect(url_for('watch', video_id=video_id))

@app.route('/like/<video_id>', methods=['POST'])
def like(video_id):
    db = get_db()
    db.execute('UPDATE videos SET likes = likes+1 WHERE id=?', (video_id,))
    db.commit()
    return jsonify({'ok':True})

if __name__=='__main__':
    if not os.path.exists(DB_PATH):
        with app.app_context():
            init_db()
    app.run(host='127.0.0.1', port=5000, debug=True)
