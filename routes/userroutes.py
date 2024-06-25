
from flask import Blueprint, render_template
from database import db
from datetime import datetime
from forms import RatingForm
from flask import render_template, request, redirect, url_for, flash, session
from functools import wraps

user = Blueprint('user', __name__)

def auth(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first','error')
            return redirect (url_for('user.login'))
        return func(*args,**kwargs)
    return inner
    
@user.route('/')
@auth
def index():
    user=User.query.get(session['user_id'])
    role=User.query.get(session['role'])
    if user.username=='admin':
        return redirect(url_for('ad.dashboard'))
    else:
        return render_template("index.html", user=user)

@user.route('/profile', methods=['GET','POST'])
@auth
def profile():
    if request.method=="POST":
      user=User.query.get(session['user_id'])
      user.name=request.form.get('name')
      user.password=request.form.get('password')
      db.session.commit()
      flash ('Profile updated','success')
      return redirect(url_for('user.profile'))
    if request.method=="GET":
        return render_template('profile.html', user=User.query.get(session['user_id']))  


@user.route('/register', methods=['GET','POST'])
def register():
    if request.method=="POST":
        username = request.form['username']
        password = request.form['password']
        name=request.form['name']

        new_user = User(username=username, password=password, name=name)
        if username=='' or password=='':
            flash("Username or password cannot have missing values.",'error')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists.','error')
            return redirect(url_for("user.register"))
        db.session.add(new_user)
        db.session.commit()
       
        flash('User registered successfully','success')
        return redirect(url_for('user.login'))
    if request.method=="GET":
        return render_template('register.html')

    return render_template('login.html')

@user.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('pwd')

        user = User.query.filter_by(username=username).first()
        if not user:
            flash ('User does not exist.','error')
            return redirect(url_for('user.login'))

        if not user.check_password(password):
            flash ('Incorrect password','error')
            return redirect(url_for('user.login'))

        session["user_id"]=user.id
        session["role"]=user.role
        if session.get('role')=='admin':
            flash('This is not admin login page','error')
            return redirect(url_for('user.login'))
        return redirect(url_for('user.userdash')) 
    if request.method=="GET":
        return render_template('login.html')   

    
@user.route('/userdash', methods=['GET','POST'])
@auth
def userdash():
    user_id=session.get('user_id')
    albums = items(Albums, 3)
    songs = items(Songs, 3)
    playlists = items(Playlists, 3,user_id=user_id)
    playlistcount=Playlists.query.filter_by(user_id=user_id).count()
    albumscount=Albums.query.count()
    songscount=Songs.query.count()
    return render_template('userdash.html',
    playlistcount=playlistcount,albumscount=albumscount,songscount=songscount, user=User.query.get(session['user_id']), role=User.query.get(session['role']),albums=albums, songs=songs,playlists=playlists)

def items(models, limit, user_id=None):
    if models == Playlists and user_id is not None:
        items = models.query.filter_by(user_id=user_id).order_by(models.id.desc()).limit(limit).all()
    else:
        items = models.query.order_by(models.id.desc()).limit(limit).all()
    return items

@user.route('/register_creator', methods=["GET",'POST'])
@auth
def register_creator():
    if request.method == 'POST':
        user=User.query.get(session['user_id'])
        creator = Creator(user_id=user.id)
        user.role='creator'
        db.session.add(creator)
        db.session.commit()
        session['role']=user.role
        flash('Registered as creator successfully','success')
        return redirect(url_for('user.userdash'))
    if request.method=='GET':
        return render_template('register-creator.html', role=User.query.get(session['role']),user=User.query.get(session['user_id']))

@user.route('/create_playlist', methods=['GET', 'POST'])
@auth
def create_playlist():
    if request.method == 'POST':
        user=User.query.get(session['user_id'])
        name = request.form.get('playlist_name')
        date=request.form.get('date')
        song_ids = request.form.getlist('songs') 
        dateobj=datetime.strptime(date, '%Y-%m-%d')
        new_playlist = Playlists(name=name, date=dateobj, user_id=user.id)
        db.session.add(new_playlist)
        db.session.commit()

        for song_id in song_ids:
            song = Songs.query.get(song_id)
            playlist=Playlists.query.filter_by(id=new_playlist.id).first()
            if song:
                playlist_song_association_entry = playlist_song_association.insert().values(playlist_id=new_playlist.id, song_id=song.id)
                db.session.execute(playlist_song_association_entry)  

        db.session.commit()

        return redirect(url_for('user.userdash'))

    all_songs = Songs.query.all()
    return render_template('create_playlist.html', all_songs=all_songs, role=User.query.get(session['role']))

@user.route('/view_playlist/<int:playlist_id>', methods=['GET','POST'])
@auth
def view_playlist(playlist_id):
    playlist = Playlists.query.filter_by(id=playlist_id).first()
    return render_template ('view_playlist.html',role=User.query.get(session['role']), playlist=playlist)

@user.route('/all_songs')
@auth
def all_songs():
    all_songs = Songs.query.all()
    return render_template('viewall_songs.html', all_songs=all_songs, role=User.query.get(session['role']))

@user.route('/remove_from_playlist/<int:playlist_id>/<int:song_id>')
@auth
def remove_song_from_playlist(playlist_id, song_id):
    playlist = Playlists.query.filter_by(id=playlist_id).first()
    song = Songs.query.filter_by(id=song_id).first()
    if playlist and song and song in playlist.songs:
        if song in playlist.songs:
            playlist.songs.remove(song)
            db.session.commit()
        playlist_song_association_entry = playlist_song_association.delete().where(
            (playlist_song_association.c.playlist_id == playlist.id) &
            (playlist_song_association.c.song_id == song.id)
        )
        db.session.execute(playlist_song_association_entry)

        db.session.commit()
        flash('Song removed from the playlist.', 'success')
        return redirect(url_for('user.view_playlist', playlist_id=playlist.id))

@user.route('/viewuser_song/<int:song_id>', methods=['GET', 'POST'])
@auth
def viewuser_song(song_id):
    song = Songs.query.filter_by(id=song_id).first()
    form = RatingForm()
    albums =Albums.query.all()
    user=User.query.get(session['user_id'])
    creator = Creator.query.get(song.creator_id)
    user_rating = session.get(f'user_rating_{song_id}')

    if not user_rating:
        user_rating = Rating.query.filter_by(user_id=user.id, song_id=song_id).first()

    if form.validate_on_submit():
        rating_value = int(form.rating.data)

        if user_rating:
            user_rating.rating = rating_value
        else:
            new_rating = Rating(rating=rating_value, user_id=user.id, song_id=song_id, creator_id=creator.id)
            db.session.add(new_rating)

        db.session.commit()
        flash('Rating submitted successfully!', 'success')
        creator = Creator.query.get(song.creator_id)
        if creator:
            ratings_sum = sum([rating.rating for rating in song.ratings])
            num_ratings = len(song.ratings)
            creator.avg_rating = ratings_sum / num_ratings if num_ratings > 0 else 0.0
        session[f'user_rating_{song_id}'] = user_rating
        db.session.commit()
        
        return redirect(url_for('user.viewuser_song', song_id=song_id))

    return render_template('viewsongsuser.html',albums=albums, song=song, role=User.query.get(session['role']),user=User.query.get(session['user_id']), form=form, user_rating=user_rating)

@user.route('/all_albums', methods=['GET','POST'])
@auth
def all_albums():
    albums=Albums.query.all()
    return render_template('viewall_albums.html', role=User.query.get(session['role']), albums=albums)

@user.route('/viewuser_album/<int:album_id>', methods=['GET','POST'])
@auth
def viewuser_album(album_id):
    album=Albums.query.filter_by(id=album_id).first()
    return render_template('viewalbumuser.html',role=User.query.get(session['role']), album=album)

@user.route('/all_playlists', methods=['GET','POST'])
@auth
def all_playlists():
    user=User.query.get(session['user_id'])
    playlists=Playlists.query.filter_by(user_id=user.id).all()
    return render_template('viewall_playlists.html', role=User.query.get(session['role']), playlists=playlists)

@user.route('/report_song/<int:song_id>', methods=["GET",'POST'])
@auth
def report_song(song_id):
    user_id = session.get('user_id')
    existing_report = Reports.query.filter_by(user_id=user_id, song_id=song_id).first()
    if existing_report:
        flash('You have already reported this song.','error')
    else:
        new_report = Reports(user_id=user_id, song_id=song_id)
        db.session.add(new_report)
        db.session.commit()
        flash('Song reported successfully.','success')

    return redirect(url_for('user.all_songs', song_id=song_id,role=User.query.get(session['user_id'])))

@user.route('/delete_playlist/<int:playlist_id>', methods=["GET",'POST'])
@auth
def delete_playlist(playlist_id):
    playlist = Playlists.query.filter_by(id=playlist_id).first()
    db.session.delete(playlist)
    db.session.commit()
    return redirect(url_for('user.userdash', ))
from models import Songs, Playlists, Albums, Rating, Reports, playlist_song_association, Creator,User


@user.route('/search', methods=['GET'])
def search():
    category = request.args.get('category')
    parameter = request.args.get('parameter')
    query = request.args.get('query')

    if category == 'song':
        if parameter == 'name':
            results = Songs.query.filter(Songs.name.ilike(f"%{query}%")).all()
            return render_template('search_songs.html', category=category, parameter=parameter, query=query, results=results)
        elif parameter == 'genre':
            results = Songs.query.filter(Songs.genre.ilike(f"%{query}%")).all()
            return render_template('search_songs.html', category=category, parameter=parameter, query=query, results=results)
        elif parameter == 'artist':
            results = Songs.query.filter(Songs.artist.ilike(f"%{query}%")).all()
            return render_template('search_songs.html', category=category, parameter=parameter, query=query, results=results)
    elif category == 'album':
        if parameter == 'name':
            results = Albums.query.filter(Albums.name.ilike(f"%{query}%")).all()
            return render_template('search_songs.html', category=category, parameter=parameter, query=query, results=results)
        elif parameter == 'genre':
            results = Albums.query.filter(Albums.genre.ilike(f"%{query}%")).all()
            return render_template('search_songs.html', category=category, parameter=parameter, query=query, results=results)
        elif parameter == 'artist':
            results = Albums.query.filter(Albums.artist.ilike(f"%{query}%")).all()
            return render_template('search_songs.html', category=category, parameter=parameter, query=query, results=results)
        
    return render_template('search_songs.html', category=category, parameter=parameter, query=query, user=User.query.get(session['user_id']), role=session.get('role'))





