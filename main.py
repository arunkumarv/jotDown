import os
from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote_plus
from datetime import datetime
from dotenv import load_dotenv

import random, string, re

app = Flask(__name__)
load_dotenv()

mysql_username = os.getenv("MYSQL_USER")
mysql_password = quote_plus(os.getenv("MYSQL_PASSWORD"))
mysql_host = os.getenv("MYSQL_HOST")
mysql_db = os.getenv("MYSQL_DB")

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{mysql_username}:{mysql_password}@{mysql_host}/{mysql_db}'

db = SQLAlchemy(app)

class Paste(db.Model):
    id = db.Column(db.String(6), primary_key=True)
    content = db.Column(db.Text, nullable=False)
    create_date = db.Column(db.DateTime, default=datetime.utcnow)

def extract_snippet(content, query, window=50):
    match = re.search(re.escape(query), content, re.IGNORECASE)
    if match:
        start = max(match.start() - window, 0)
        end = min(match.end() + window, len(content))
        snippet = content[start:end]
        if start > 0:
            snippet = '...' + snippet
        if end < len(content):
            snippet = snippet + '...'
        return snippet
    return None

def generate_id(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form['content']
        paste_id = generate_id()
        new_paste = Paste(id=paste_id, content=content)
        db.session.add(new_paste)
        db.session.commit()
        return redirect(url_for('view_paste', paste_id=paste_id))
    pastes = Paste.query.order_by(Paste.create_date.desc()).limit(10).all()
    return render_template('index.html', pastes=pastes)

@app.route('/<paste_id>')
def view_paste(paste_id):
    paste = Paste.query.get(paste_id)
    if paste:
        return render_template('view.html', paste=paste.content)
    return "Paste not found", 404

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    results = []
    if query:
        pastes = Paste.query.filter(Paste.content.like(f"%{query}%")).all()
        for paste in pastes:
            snippet = extract_snippet(paste.content, query)
            results.append({'id': paste.id, 'snippet': snippet})
    return render_template('search.html', results=results, query=query)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
