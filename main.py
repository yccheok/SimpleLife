import webapp2
import jinja2
import facebook
import datetime

from google.appengine.ext import ndb
from webapp2_extras import sessions
from google.appengine.api import taskqueue

import json
import os

from config import *
from models.user import User
from models.album import Album
from models.image import Image

from handlers import FacebookHandler, fb_require_token

class CurrentUserHandler (FacebookHandler):
    def get (self):
        if self.current_user:
            self.response.out.write (json.dumps ({'uid': self.current_user['id']}))
        else:
            self.abort (401)

class MainPage (FacebookHandler):
    def get (self):
        self.display ()

class SignInPage (FacebookHandler):
    def get (self):
        response = {'success': False}

        if self.current_user:
            response["success"] = True
            response["id"] = self.current_user["id"]

        self.response.out.write (json.dumps (response));

class AlbumsHandler (FacebookHandler):
    def get (self, albumId):
        albums = []

        if self.current_user:
            user = User.get_user_by_id (self.current_user["id"])

            if albumId:
                result = Album.query (albumId, ancestor = user.key).fetch ()
            else:
                result = [
                    {"id": album.key.id(), "name": album.name} 
                    for album in user.albums
                ]
            """
            all_albums = self.graph ('me/albums')
            
            if all_albums:
                print albums
                albums = [
                    dict (
                        name = album["name"],
                        icon = self.graph (album["cover_photo"]),
                        dikt = album
                    ) for album in all_albums["data"]
                ]
            """
        else:
            pass

        self.response.out.write (json.dumps (result))

    def post (self, action):
        if self.current_user:
            data = json.loads (self.request.body)

            if self.current_user:
                user = User.get_user_by_id (self.current_user['id'])

            # for album in data["albums"]:
                #info = self.graph (album["id"])

                # album = user.add_album (info)

            if data:
                album = user.add_album (data)
                taskqueue.add(url='/extractor', params = {'user': user.id, "album": album.key.id (), 'fb_albums': json.dumps (data["fb_albums"])})

class PictureExtractor (webapp2.RequestHandler):
    def post (self):
        user_id = self.request.get ('user')
        print 'task queue recevied user id: %s' % user_id

        album_key = self.request.get ('album')
        fb_albums = json.loads (self.request.get ('fb_albums'))
        images = []

        user = User.get_user_by_id (user_id)
        album = ndb.Key (Album, int(album_key), parent=user.key).get ()

        graph = facebook.GraphAPI (user.access_token)

        albums_count = len(fb_albums)

        for fb_album in fb_albums:
            images_list = graph.get_object ("%s/photos" % fb_album["id"],
                    fields="picture")

            if images_list:
                images.extend ([Image (source=image["picture"], id=image["id"])
                    for image in images_list["data"]])

        album.images = images
        album.put ()

class PicturesHandler (FacebookHandler):
    def get (self, albumId):
        images = []

        if self.current_user:
            user = User.get_user_by_id (self.current_user["id"])
            if user:

                album = ndb.Key ('Album', long(albumId), parent = user.key)
                print album
                images = album.get ().images

        self.response.out.write (json.dumps (images, cls=JsonAlbumEncode))

class JsonAlbumEncode (json.JSONEncoder):
    def default (self, obj):
        if isinstance (obj, Image):
            return {
                "id": obj.id,
                "source": obj.source,
                "width": obj.width,
                "height": obj.height
            }
        else:
            return json.JSONEncoder.default (self, obj)

class TokenHandler (FacebookHandler):
    def get (self):
        if 'code' in self.request.GET:
            token = self.get_token_from_code (self.request.GET['code'], self.request.path_url)

            print token, self.current_user
            user = User.get_user_by_id (self.current_user['id'])
            user.access_token = token["access_token"]
            user.put ()

            self.add_user_to_session (user)
            self.redirect (str(self.session["redirect"]["redirect_url"]))
        else:
            self.session["redirect"] = json.loads (self.request.body) if self.request.body else {"redirect_url": ""}
            print self.session["redirect"]

            script = self.get_renew_url (self.request.path_url);

            self.response.write (script)

    def post (self):
        self.session["redirect"] = json.loads (self.request.body) if self.request.body else {"redirect_url": ""}
        print self.session["redirect"]

        script = self.get_renew_url (self.request.path_url);

        self.response.write (script)


class LogoutHandler(FacebookHandler):
    def get(self):
        if self.current_user is not None:
            self.session['user'] = None

application = webapp2.WSGIApplication ([
    ('/', MainPage),
    ('/signin', SignInPage),
    ('/albums(/\d+)?', AlbumsHandler),
    ('/signout', LogoutHandler),
    ('/current_user', CurrentUserHandler),
    ('/([^/]+)/pictures', PicturesHandler),
    ('/renew_token', TokenHandler),
    ('/extractor', PictureExtractor),
    # ('/([^/]+)/list', AlbumHandler),
    # ('/([^/]+)/upload', AddPhoto)
], config = CONFIG, debug = True)

