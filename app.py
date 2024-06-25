from functools import wraps
from datetime import datetime, timedelta
import os
from flask import Flask
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from forms import RatingForm
current_dir=os.path.abspath(os.path.dirname(__file__))
from models import db, User, Rating, Songs, Albums, Playlists,Creator, Reports, playlist_song_association
from routes.creatorroutes import creator
from routes.userroutes import user
from routes.adminroutes import ad

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+ os.path.join(current_dir,'testdb.sqlite3')
db.init_app(app)
app.app_context().push
app.secret_key='2jglihabghfnjkseyirrjkwlyvnskuzhfksuhnqhdbvvdpooiwnbbvdjhsfbsbvgeknrkle'
app.register_blueprint(creator)
app.register_blueprint(user)  
app.register_blueprint(ad) 

def auth(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first')
            return redirect (url_for('user.login'))
        return func(*args,**kwargs)
    return inner
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('user.index'))



with app.app_context():
    db.create_all()

    admin=User.query.filter_by(username='admin').first()
    if admin is None:
        try:
            admin=User(username='admin',name='admin',passhash=generate_password_hash('kashish'),role='admin')
            db.session.add(admin)
            db.session.commit()
        except:
            db.session.rollback()
if __name__=='__main__':
    app.run(debug=True)
