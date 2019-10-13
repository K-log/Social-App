from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5

from app import db, login

FRIENDS = db.Table(
    'friends',
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('friended_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    """
        Primary Identifier: 
            id            (integer)

        Data:
            username      (string)
            about_me      (string)
            password_hash (string)

        Connections:
            posts         (List of posts whose author_id == id)
            friends_list  (Join of all friends in FRIENDS whose friended_id == id)
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    about_me = db.Column(db.String(140))
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    friends_list = db.relationship(
        'User', secondary=FRIENDS,
        primaryjoin=(FRIENDS.c.friend_id == id),
        secondaryjoin=(FRIENDS.c.friended_id == id),
        backref=db.backref('FRIENDS', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        # Default data to return for this model
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        # Set a new password
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # Check the given password against the one stored in the database
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        # Use gravatar to generate cool profile pictures based on usernames
        digest = md5(self.username.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def friend(self, user):
        # Add the given user as a friend
        if not self.is_friend(user):
            self.friends_list.append(user)

    def unfriend(self, user):
        # Remove the given user as a friend
        if self.is_friend(user):
            self.friends_list.remove(user)

    def is_friend(self, user):
        # Check if a user is a friend
        return self.friends_list.filter(
            FRIENDS.c.friended_id == user.id).count() > 0

    def friend_posts(self):
        # Get all posts authored by friends
        friends_list = Post.query.join(
            FRIENDS, (FRIENDS.c.friended_id == Post.author_id)).filter(
            FRIENDS.c.friend_id == self.id)
        own = Post.query.filter_by(author_id=self.id)
        return friends_list.union(own).order_by(Post.timestamp.desc())

    @login.user_loader
    def load_user(id):
        # Get the current user from the database
        return User.query.get(int(id))


class Post(db.Model):
    """
        Primary Identifier: 
            id           (integer)

        Data:
            title        (string)
            body         (string)
            timestamp    (object)
        
        Connections:
            author_id    (integer)
            edits        (integer)
        
        Unused:
            subject_name (string)
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), index=False, unique=False)
    body = db.Column(db.Text, index=False, unique=False)
    subject_name = db.Column(db.String(120), index=False, unique=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    edits = db.relationship('PostEdit', backref='edits', lazy='dynamic')

    def __repr__(self):
        # Default data to return for this model
        return '<Post {}>'.format((self.title, self.body, self.subject_name))

    def get_timestamp(self):
        # Return the timestamp in an easier to display format
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")


class PostEdit(db.Model):
    """
        Primary Identifier: 
            id           (integer)

        Data:
            title        (string)
            body         (string)
            timestamp    (object)
        
        Connections:
            author_id    (integer)
            post_id      (integer)
        
        Unused:
            subject_name (string)
    """


    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), index=False, unique=False)
    body = db.Column(db.Text, index=False, unique=False)
    subject_name = db.Column(db.String(120), index=False, unique=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    def __repr__(self):
        # Default data to return for this model
        return '<PostEdit {}>'.format((self.title, self.body, self.subject_name))
