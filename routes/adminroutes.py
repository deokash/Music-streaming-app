from flask import Blueprint, render_template
from database import db
from sqlalchemy import func
from flask import render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
from functools import wraps
ad = Blueprint('ad', __name__)

def auth(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first','error')
            return redirect (url_for('user.login'))
        return func(*args,**kwargs)
    return inner

@ad.route('/admin', methods=['GET','POST'])
def admin():
    if request.method=="POST":
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if not user.check_password(password):
            flash ('Incorrect password','error')
            return redirect(url_for('ad.admin'))

        if user and user.check_password(password):
            flash ("Login successful",'success')
            session['user_id']=user.id
            session['role']=user.role
            return redirect(url_for('ad.dashboard', role=session.get('role')))

    if request.method=='GET':
        return render_template('loginadmin.html')


@ad.route('/dashboard', methods=['GET','POST'])
def dashboard():
    userstotal=User.query.filter(User.role!='admin').count()
    creatortotal=Creator.query.count()
    songstotal=Songs.query.count()
    genretotal=Albums.query.group_by(Albums.genre).count()
    albumstotal=Albums.query.count()
    result = db.session.query(Songs.name, func.avg(Rating.rating).label('average_rating')).join(Rating, Songs.id == Rating.song_id).group_by(Songs.id).order_by(func.avg(Rating.rating).desc()).first()

    if result:
        highest_rated_song_name, average_rating = result

    return render_template('dashboard.html',highest_rated_song_name=highest_rated_song_name,
        average_rating=average_rating,
        role=session.get('role'),albumstotal=albumstotal, userstotal=userstotal, genretotal=genretotal,creatortotal=creatortotal, songstotal=songstotal)


@ad.route('/tracksadmin', methods=['GET'])
def tracksadmin():
    songs = Songs.query.all()

    return render_template('tracksadmin.html', songs=songs, role=User.query.get(session['user_id']))

@ad.route('/albumsadmin', methods=['GET'])
def albumsadmin():
    albums = Albums.query.all()

    return render_template('albums_admin.html', albums=albums, role=User.query.get(session['user_id']))

@ad.route('/admin/flag-song/<int:song_id>', methods=['GET'])
def flag_song(song_id):
    song = Songs.query.get(song_id)
    song.flagged = True
    db.session.commit()
    flash('Song flagged successfully!', 'success')
    return redirect(url_for('ad.tracksadmin'))

@ad.route('/admin/remove-song/<int:song_id>', methods=['GET'])
def remove_song(song_id):
    song = Songs.query.filter_by(id=song_id).first()
    albums = Albums.query.filter(Albums.songs.any(id=Songs.id)).all()
    ratings = Rating.query.filter_by(song_id=song_id).all()
    for rating in ratings:
        db.session.delete(rating)
    db.session.delete(song)

    db.session.commit()

    flash('Song removed successfully!', 'success')
    return redirect(url_for('ad.tracksadmin'))

@ad.route('/admin/flag-album/<int:album_id>', methods=['GET'])
def flag_album(album_id):
    album = Albums.query.filter_by(id=album_id).first()
    album.flagged = True
    db.session.commit()

    flash('Album flagged successfully!', 'success')
    return redirect(url_for('ad.albumsadmin'))

@ad.route('/admin/remove-album/<int:album_id>', methods=['GET'])
def remove_album(album_id):
    album = Albums.query.filter_by(id=album_id).first()
    db.session.delete(album)
    db.session.commit()

    flash('Album removed successfully!', 'success')
    return redirect(url_for('ad.albumsadmin'))

@ad.route('/admin/view_song/<int:song_id>', methods=['GET','POST'])
def viewadmin_song(song_id):
    song=Songs.query.filter_by(id=song_id).first()
    creator=Creator.query.filter_by(id=song.creator_id).first()
    report=Reports.query.filter_by(song_id=song.id).count()
    blacklisted=creator.blacklisted
    return render_template('viewadmin_song.html',blacklisted=creator.blacklisted,role=User.query.get(session['user_id']),song=song,creator=creator,report=report)


@ad.route('/admin/view_album/<int:album_id>', methods=['GET','POST'])
def viewadmin_album(album_id):
    return render_template('viewadmin_album.html',role=User.query.get(session['user_id']))

@ad.route('/blackwhitelist/<int:creator_id>', methods=['POST'])
def blackwhitelist(creator_id):
    status = request.form.get('status')
    creator = Creator.query.filter_by(id=creator_id).first()
    if status=="blacklist":
        creator.blacklisted = True
    elif status=="whitelist":
        creator.blacklisted=False
    else:
        creator.blacklisted=False
    db.session.commit()
    flash('Creator status updated','success')
    return redirect(url_for('ad.tracksadmin'))

@ad.route('/userslist', methods=['GET'])
def userslist():
    users=User.query.all()
    return render_template ('userslist.html', users=users, role=User.query.get(session['user_id']))
from models import Songs, Playlists, Albums, Rating, Reports, playlist_song_association, Creator,User