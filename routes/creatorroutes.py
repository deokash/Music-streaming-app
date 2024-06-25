from flask import Blueprint, render_template
from datetime import datetime, timedelta
from database import db
from flask import render_template, request, redirect, url_for, flash, session
from functools import wraps


creator = Blueprint('creator', __name__)
def auth(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first','error')
            return redirect (url_for('user.login'))
        return func(*args,**kwargs)
    return inner
@creator.route('/creator/create_song', methods=["GET",'POST'])
@auth
def create_song():
    if request.method == 'POST':
        user=User.query.get(session['user_id'])   
        current_creator = Creator.query.filter_by(user_id=user.id).first()
        if current_creator and not current_creator.blacklisted:
            name = request.form.get('title')
            lyrics = request.form.get('lyrics')
            genre=request.form.get('genre')
            duration= request.form.get('duration')
            date=request.form.get('date')
            artist=request.form.get('artist')
            date= datetime.strptime(date, '%Y-%m-%d')

            minutes, seconds = map(int, duration.split(':'))
            current_creator = Creator.query.filter_by(user_id=user.id).first()
            if current_creator:
                new_song = Songs(
                    name=name,
                    artist=artist,
                    duration=duration,
                    lyrics=lyrics,
                    date=date,
                    creator_id=current_creator.id ,
                    genre=genre
                )
                db.session.add(new_song)
                db.session.commit()
                flash('Song added successfully','success')
            return redirect(url_for('creator.creator_dashboard'))
        flash('You are not allowed to publish songs','error')
        return redirect(url_for('creator.creator_dashboard'))
    return render_template('createsong.html')

@creator.route('/albums', methods=["GET",'POST'])
@auth
def albums():
    user=session.get('user_id')
    creator=Creator.query.filter_by(user_id=user).first()
    albums = Albums.query.filter_by(creator_id=creator.id).all()
    if request.method=="POST":
        return render_template('create_album.html')
    return render_template('albums.html', albums=albums, creator_id=creator.id)

added_songs = []
@creator.route('/create_album', methods=["GET",'POST'])
@auth
def create_album():
    if request.method=="POST":
        user=User.query.get(session['user_id'])
        current_creator = Creator.query.filter_by(user_id=user.id).first()
        creator_id=current_creator.id
        album_name = request.form.get('name')
        genre = request.form.get('genre')
        album_artist = request.form.get('artist')

        new_album = Albums(
            name=album_name,
            genre=genre,
            artist=album_artist,
            creator_id=creator_id,
        )
        db.session.add(new_album)
        db.session.commit()
        flash('Album created successfully!','success')
        return redirect(url_for('creator.albums'))
    return render_template('create_album.html', added_songs=added_songs)

@creator.route('/view_album/<int:album_id>', methods=['GET','POST'])
def view_album(album_id):
    album=Albums.query.filter_by(id=album_id).first()
    referrer=request.referrer
    if referrer and referrer.endswith('/userdash'):
        return render_template('viewalbumuser.html', album=album, role=User.query.get(session['role']))
        
    if referrer and referrer.endswith('/albums'):
        return render_template('view_album.html', album=album, role=User.query.get(session['role']))



@creator.route('/edit_album/<int:album_id>', methods=['GET', 'POST'])
@auth
def edit_album(album_id):
    album = Albums.query.filter_by(id=album_id).first()

    if request.method == 'POST':
        new_name = request.form.get('name')
        album.genre=request.form.get('genre')
        album.name = new_name
        album.artist=request.form.get('artist')
        db.session.commit()
        return redirect(url_for('creator.albums'))

    return render_template('edit_album.html', album=album)

@creator.route('/add_song_to_album/<int:album_id>', methods=['GET','POST'])
@auth
def add_song_to_album(album_id):

    if request.method=="POST":
        user=session.get('user_id')
        name = request.form.get('title')
        lyrics = request.form.get('lyrics')
        genre=request.form.get('genre')
        duration= request.form.get('duration')
        date=request.form.get('date')
        artist=request.form.get('artist')
        date= datetime.strptime(date, '%Y-%m-%d')
        album_id=album_id
        minutes, seconds = map(int, duration.split(':'))
        current_creator = Creator.query.filter_by(user_id=user).first()
        if current_creator:
            new_song = Songs(
                name=name,
                artist=artist,
                duration=duration,
                lyrics=lyrics,
                date=date,
                genre=genre,
                creator_id=current_creator.id,
                album_id=album_id
            )
            db.session.add(new_song)
            db.session.commit()
        return redirect(url_for('creator.edit_album', album_id=album_id))
    return render_template('createsong.html')

@creator.route('/delete_album/<int:album_id>', methods=["GET",'POST'])
@auth
def delete_album(album_id):
    album = Albums.query.filter_by(id=album_id).first()
    db.session.delete(album)
    db.session.commit()
    return redirect(url_for('creator.albums'))

@creator.route('/view_song/<int:song_id>', methods=['GET', 'POST'])
def view_song(song_id):
    song = Songs.query.filter_by(id=song_id).first()
    albums =Albums.query.all()
    return render_template('view_song.html',albums=albums, song=song,user=User.query.get(session['user_id']))



@creator.route('/edit_song/<int:song_id>', methods=['GET', 'POST'])
@auth
def edit_song(song_id):
    song = Songs.query.filter_by(id=song_id).first()
    user=User.query.get(session['user_id'])
    current_creator = Creator.query.filter_by(user_id=user.id).first()
    creator_id=current_creator.id
    albums=Albums.query.filter_by(creator_id=creator_id).all()
    if request.method == 'POST':
        song.name = request.form.get('title')
        song.lyrics = request.form.get('lyrics')
        song.artist = request.form.get('artist')
        album_id = request.form.get('album_id')
        selected_album_id = request.form.get('album')

        if selected_album_id == "":
            song.album_id = None
        else:
            song.album_id = (selected_album_id)


        db.session.commit()
        flash('Saved changes', 'success')
        referrer = request.referrer
        if referrer and referrer.endswith('/creator_dashboard'):
            return redirect(url_for('creator_dashboard'))
        if referrer and referrer.endswith('/albums'):
            return redirect(url_for('creator.albums'))

    return render_template('edit_song.html', song=song, albums=albums)


@creator.route('/delete_song/<int:song_id>', methods=['GET', 'POST'])
def delete_song(song_id):
    song =Songs.query.filter_by(id=song_id).first()
    albums = Albums.query.filter(Albums.songs.any(id=Songs.id)).all()
    if song in albums:
        for album in albums:
            album.songs.remove(song)

    db.session.delete(song)
    db.session.commit()
    current_url = request.url
    if current_url and current_url.endswith("/edit_album"):
        return redirect(url_for('creator.edit_album'))
    else:
        return redirect(url_for('creator.creator_dashboard'))
  


@creator.route('/creator_dashboard', methods=['GET','POST'])
@auth
def creator_dashboard():
    user=User.query.get(session['user_id'])
    current_creator = Creator.query.filter_by(user_id=user.id).first()
    total_songs = Songs.query.filter_by(creator_id=current_creator.id).count()
    creator_id=current_creator.id
    avg_rating = get_avg_rating(creator_id)
    total_albums = Albums.query.filter_by(creator_id=current_creator.id).count()
    
    creator_songs = Songs.query.filter_by(creator_id=current_creator.id).all()

    return render_template('creator.html', total_songs=total_songs,avg_rating=avg_rating, total_albums=total_albums, creator_songs=creator_songs)
def get_avg_rating(creator_id):
    user=User.query.get(session['user_id'])
    creator = Creator.query.filter_by(id=creator_id).first()
    if creator:
        avg_rating = creator.avg_rating
        return avg_rating

from models import Songs, Playlists, Albums, Rating, Reports, playlist_song_association, Creator,User
