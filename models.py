from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

class User(db.Model):
    __tablename__='User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    name=db.Column(db.String(30), nullable=False)
    passhash= db.Column(db.String(512), nullable=False)
    role=db.Column(db.String(15),nullable=False, default='user')
    playlists = db.relationship('Playlists', backref='user', lazy=True)
    ratings = db.relationship('Rating', backref='user', lazy=True)

    @property
    def password(self):
        return AttributeError('password is not readable')

    @password.setter
    def password(self,password):
        self.passhash=generate_password_hash(password)
   
    def check_password(self,password):
        return check_password_hash(self.passhash,password)
class Creator(db.Model):
    __tablename__='Creator'
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("User.id"),nullable=False)
    user = db.relationship('User', backref='creator', lazy=True)
    ratings = db.relationship('Rating', backref='creator', lazy=True)
    avg_rating = db.Column(db.Float, default=0.0)
    blacklisted = db.Column(db.Boolean, default=False)

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('Songs.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('Creator.id'), nullable=False)

playlist_song_association = db.Table(
    'playlist_song_association',
    db.Column('playlist_id', db.Integer, db.ForeignKey('Playlists.id')),
    db.Column('song_id', db.Integer, db.ForeignKey('Songs.id'))
)
class Songs(db.Model):
    __tablename__="Songs"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(30), unique=True, nullable=False)
    artist=db.Column(db.String(50),nullable=False)
    duration=db.Column(db.Integer, nullable=False)
    lyrics=db.Column(db.Text, nullable=False)
    genre=db.Column(db.String(20), nullable=False)
    date=db.Column(db.Date, nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('Albums.id'), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('Creator.id'), nullable=True)
    creator = db.relationship('Creator', backref='songs', lazy=True)
    playlists = db.relationship('Playlists', secondary=playlist_song_association, back_populates='songs')
    ratings = db.relationship('Rating', backref='song', lazy=True)
    flagged = db.Column(db.Boolean, default=False)

class Albums(db.Model):
    __tablename__="Albums"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(30), nullable=False)
    genre=db.Column(db.String(20), nullable=False)
    artist=db.Column(db.String(40), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('Creator.id'), nullable=False)
    creator = db.relationship('Creator', backref='albums')
    songs = db.relationship('Songs', backref='album', lazy=True)
    flagged = db.Column(db.Boolean, default=False)

class Reports(db.Model):
    __tablename__ = "Reports"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('Songs.id'), nullable=False)
  


class Playlists(db.Model):
    __tablename__="Playlists"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(30),nullable=False)
    date=db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    songs = db.relationship('Songs', secondary=playlist_song_association, back_populates='playlists')


