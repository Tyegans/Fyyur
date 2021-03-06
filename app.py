#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
Migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String, nullable=False)
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.String, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='Venue', lazy=True)

    def __repr__(self):
        return f'<Venue {self.id} name: {self.name}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='Artist', lazy=True)

    def __repr__(self):
        return f'<Artist {self.id} name: {self.name}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


class Show(db.Model):
    ___tablename__ = 'show'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        "artist.id"), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Show {self.id}, Artist {self.artist_id}, Venue {self.venue_id}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ---------------------------------------------------------------------
# ------------------------------------------------------------------------
# venue Query
# ------------------------------------------------------------------------
@app.route('/venues')
def venues():
    data = []
    venues = Venue.query.all()
    locations = set()
    for venue in venues:
        locations.add((venue.city, venue.state))
    for location in locations:
        data.append({
            "city": location[0],
            "state": location[1],
            "venues": []
        })

    for venue in venues:
        num_upcoming_shows = 0
        shows = Show.query.filter_by(venue_id=venue.id).all()
        current_date = datetime.now()
        for show in shows:
            if show.start_time > current_date:
                num_upcoming_shows += 1
        for venue_location in data:
            if venue.state == venue_location['state'] and venue.city == venue_location['city']:
                venue_location['venues'].append({
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": num_upcoming_shows
                })
    return render_template('pages/venues.html', areas=data)

# ------------------------------------------------------
# search venue
# ------------------------------------------------------


@app.route('/venues/search', methods=['POST'])
def search_venues():
    query = request.form.get("search_term", "")
    response = {"count": 0, "data": []}

    venue_search_results = (
        db.session.query(Venue)
        .filter(Venue.name.ilike(f"%{query}%"))
        .all()
    )
    response["count"] = len(venue_search_results)
    for result in venue_search_results:
        item = {
            "id": result.id,
            "name": result.name,
        }
        response["data"].append(item)
        return render_template(
            "pages/search_venues.html",
            results=response,
            search_term=request.form.get("search_term", "")
        )


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)

    if not venue:
        flash("Venue not found.")
        return render_template("errors/404.html")

    newShows = []
    previousShows = []
    newShowsNums = set([])
    previousShowsNums = set([])
    query = db.session.query(Show).join(Artist).filter(
        Show.venue_id == venue_id, Show.start_time > datetime.now()).all()

    for show in query:
        newShows.append(
            {
                "artist_id": show.artist_id,
                "artist_name": show.artist_name,
                "artist_image_link": show.artist.image_link,
                "start_time": show.start_time.strftime("%x %X"),
            }
        )
        newShowsNums.add(show.artist_id)
    query1 = db.session.query(Show).join(Artist).filter(
        Show.venue_id == venue_id, Show.start_time < datetime.now()).all()
    for show in query1:
        previousShows.append(
            {
                "artist_id": show.artist_id,
                "artist_name": show.Artist.name,
                "artist_image_link": show.Artist.image_link,
                "start_time": show.start_time.strftime("%x %X"),
            }
        )
        previousShowsNums.add(show.artist_id)

    data = {
        "id": venue.id,
        "name": venue.name,
        "city": venue.city,
        "state": venue.state,
        "address": venue.address,
        "genres": (venue.genres).split(","),
        "phone": venue.phone,
        "website_link": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "upcoming_shows_count": len(newShowsNums),
        "upcoming_shows": newShows,
        "past_shows_count": len(previousShowsNums),
        "past_shows": previousShows,
    }

    return render_template("pages/show_venue.html", venue=data)

# ------------------------------------------------------------------
#  Create Venue form
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()
    error = False
    try:
        venue = Venue()
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        genres = request.form.getlist('genres')
        venue.genres = ','.join(genres)
        venue.facebook_link = request.form['facebook_link']
        venue.image_link = request.form['image_link']
        venue.website_link = request.form['website_link']
        venue.seeking_talent = request.form['seeking_talent']
        venue.seeking_description = request.form['seeking_description']
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occured. Venue ' +
                  request.form['name'] + ' Could not be listed!')
        else:
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    venue_id = request.form.get('venue_id')
    deleted_venue = Venue.query.get(venue_id)
    venueName = deleted_venue.name
    try:
        db.session.delete(deleted_venue)
        db.session.commit()
        flash('Venue ' + venueName + ' was successfully deleted!')
    except:
        db.session.rollback()
        flash('please try again. Venue ' + venueName + ' could not be deleted.')
    finally:
        db.session.close()
        return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
# Artist Query
# ------------------------------------------------------------------


@app.route('/artists')
def artists():
    artists = db.session.query(Artist.id, Artist.name)
    data = []

    for artist in artists:
        data.append({
            "id": artist[0],
            "name": artist[1]
        })
    return render_template('pages/artists.html', artists=data)


# ------------------------------------------------------------------
# Artist search
# ------------------------------------------------------------------


@app.route('/artists/search', methods=['POST'])
def search_artists():
    query = request.form.get("search_term", "")
    response = {"count": 0, "data": []}

    venue_search_results = (
        db.session.query(Artist)
        .filter(Artist.name.ilike(f"%{query}%"))
        .all()
    )
    response["count"] = len(venue_search_results)
    for result in venue_search_results:
        item = {
            "id": result.id,
            "name": result.name,
        }
        response["data"].append(item)
        return render_template(
            "pages/search_artists.html",
            results=response,
            search_term=request.form.get("search_term", "")
        )
# --------------------------------------------------------------
# shows Artist query
# --------------------------------------------------------------


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)

    if not artist:
        flash("Artist not found.")
        return render_template("errors/404.html")

    newShows = []
    previousShows = []
    query = db.session.query(Show).join(Venue).filter(
        Show.artist_id == artist_id, Show.start_time > datetime.now()).all()
    for show in query:
        newShows.append(
            {
                "venue_id": show.venue_id,
                "venue_name": show.venue_name,
                "venue_image_link": show.venue.image_link,
                "start_time": show.start_time.strftime("%x %X"),
            }
        )

    query1 = db.session.query(Show).join(Venue).filter(
        Show.artist_id == artist_id, Show.start_time > datetime.now()).all()
    for show in query1:
        previousShows.append(
            {
                "venue_id": show.venue_id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                "start_time": show.start_time.strftime("%x %X"),
            }
        )

    data = {
        "id": artist.id,
        "name": artist.name,
        "city": artist.city,
        "state": artist.state,
        "genres": (artist.genres).split(","),
        "phone": artist.phone,
        "website_link": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "upcoming_shows_count": len(newShows),
        "upcoming_shows": newShows,
        "past_shows_count": len(previousShows),
        "past_shows": previousShows,
    }

    return render_template("pages/show_artist.html", artist=data)

#  Update
#  ----------------------------------------------------------------
# Edit Artist
# ------------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get_or_404(artist_id)

    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website.data = artist.website
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description

    return render_template("forms/edit_artist.html", form=form, artist=artist)

# ----------------------------------------------------------------------------
# Edit Artist submission
# ----------------------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        tmp_genres = request.form.getlist('genres')
        artist.genres = ','.join(tmp_genres)
        artist.website = request.form['website']
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.seeking_description = request.form['seeking_description']
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            return redirect(url_for('server_error'))
        else:
            return redirect(url_for('show_artist', artist_id=artist_id))
# ------------------------------------------------------------------------------
# Edit venue
# ------------------------------------------------------------------------------


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get_or_404(venue_id)

    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

    return render_template("forms/edit_venue.html", form=form, venue=venue)

# ------------------------------------------------------------------------------
# Edit venue submission
# ------------------------------------------------------------------------------


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.get(venue_id)

    error = False
    try:
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        tmp_genres = request.form.getlist('genres')
        venue.genres = ','.join(tmp_genres)
        venue.facebook_link = request.form['facebook_link']
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be updated.')
        else:
            flash('Venue ' + request.form['name'] +
                  ' was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)

# ------------------------------------------------------------------------------
# Artist Form
# ------------------------------------------------------------------------------


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm()
    error = False
    try:
        artist = Artist()
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        genres = request.form.getlist('genres')
        artist.genres = ','.join(genres)
        artist.website_link = request.form['website_link']
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.seeking_description = request.form['seeking_description']
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be listed.')
        else:
            flash('Artist ' + request.form['name'] +
                  ' was successfully listed!')
        return render_template('pages/home.html')

#  Shows
#  ---------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# Shows Query
# ------------------------------------------------------------------------------


@app.route('/shows')
def shows():
    results = db.session.query(Show).join(Artist).join(Venue).all()
    response = {"data": []}
    for show in results:
        item = {
            "venue_id": show.Venue.id,
            "venue_name": show.Venue.name,
            "artist_id": show.Artist.id,
            "artist_name": show.Artist.name,
            "artist_image_link": show.Artist.image_link,
            "start_time": show.start_time.strftime("%x %X"),
        }
        response["data"].append(item)
        print(response)
        return render_template(
            "pages/shows.html",
            shows=response
        )


# ------------------------------------------------------------------
# Artist Query
# ------------------------------------------------------------------


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)

# ------------------------------------------------------------------------------
# Shows Form
# ------------------------------------------------------------------------------


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm()
    error = False
    try:
        show = Show()
        show.artist_id = request.form['artist_id']
        show.venue_id = request.form['venue_id']
        show.start_time = request.form['start_time']
        db.session.add(show)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Requested show could not be listed.')
    else:
        flash('Requested show was successfully listed')
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
