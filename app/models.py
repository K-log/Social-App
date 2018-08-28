from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5


friends = db.Table(
    'friends',
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('friended_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    about_me = db.Column(db.String(140))
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    friends_list = db.relationship(
        'User', secondary=friends,
        primaryjoin=(friends.c.friend_id == id),
        secondaryjoin=(friends.c.friended_id == id),
        backref=db.backref('friends', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.username.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def friend(self, user):
        if not self.is_friend(user):
            self.friends_list.append(user)

    def unfriend(self, user):
        if self.is_friend(user):
            self.friends_list.remove(user)

    def is_friend(self, user):
        return self.friends_list.filter(
            friends.c.friended_id == user.id).count() > 0

    def friend_posts(self):
        friends_list = Post.query.join(
            friends, (friends.c.friended_id == Post.author_id)).filter(
            friends.c.friend_id == self.id)
        own = Post.query.filter_by(author_id=self.id)
        return friends_list.union(own).order_by(Post.timestamp.desc())

    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), index=False, unique=False)
    body = db.Column(db.Text, index=False, unique=False)
    subject_name = db.Column(db.String(120), index=False, unique=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    edits = db.relationship('PostEdit', backref='edits', lazy='dynamic')

    def __repr__(self):
        return '<Post {}>'.format((self.title, self.body, self.subject_name))


class PostEdit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), index=False, unique=False)
    body = db.Column(db.Text, index=False, unique=False)
    subject_name = db.Column(db.String(120), index=False, unique=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    def __repr__(self):
        return '<PostEdit {}>'.format((self.title, self.body, self.subject_name))

