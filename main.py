from flask import Flask,render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail
import json
import os
import math
from datetime import datetime

#to load and open json file
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

#loacal sever used in config.json
local_server = True

#start flask app obj
app = Flask(__name__)

#secretkey for file uploader in werkzeug.utils
app.secret_key = 'super-secret-key'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER']= params['upload_location'] #folder uploader locatio in config file

#mail server ports configuration along wiht email id and password given in config.json
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD=  params['gmail-password']
)
mail = Mail(app) #imported Mail using app obj created above
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri'] #db uri in config j.son for database connection
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

#connect to database with sql alchemy using object db which created below
db = SQLAlchemy(app)

#create class for table getintouch
class Getintouch(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)


#create table for posts
class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=False)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all() #show all posts
    last = math.ceil(len(posts)/int(params['no_of_posts'])) #show only no of posts in config file


    page = request.args.get('page') #get the page
    if (not str(page).isnumeric()):
        page = 1 #initial page
    page = int(page) #number of the page

    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]


     #pagination logic

    #first pg
    if(page==1):
        prev = "#" #if on pg 1 next page will be 2 go back then prev will be # ie home
        next = "/?page="+ str(page + 1)  #slug will be +1

    elif(page == last):
        prev = "/?page=" + str(page - 1) #if on last paeg then next will be #ie that pg only prev will be -1
        next = "#"

    else:
        prev = "/?page=" + str(page - 1) #middle pages then slug will be prev is -1 next will be +1
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)
#return index.html with posts chk wether prev next



#create posts page
@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first() #filter posts by slug and not sno
    return render_template('post.html', params=params, post=post)

#go to about page
@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']): #if only user in session
        posts = Posts.query.all() #show all post dont filter
        return render_template('dashboard.html', params=params, posts = posts) #to dashbaoard

    if request.method == 'POST': #create username and userpass var to use in if statemtn
        username = request.form.get('uname') #take the username and password uname pass just a var created
        userpass = request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_password']): #chk if usernam and password is same as in cofig.json
            session['user'] = username #username match then show all posts
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts = posts)

    return render_template('login.html', params=params)

#edit pg
@app.route("/edit/<string:sno>", methods=['GET','POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']): #if only user in session
        if request.method == 'POST':
            box_title = request.form.get('title') #take from user
            tline =request.form.get('tline')
            slug =request.form.get('slug')
            content =request.form.get('content')
            img_file =request.form.get('img_file')
            date = datetime.now()

            if sno=='0': #adding a post is 0 in slug
                post = Posts(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file, date= date) #taken from user inptu abv
                db.session.add(post) #add in db
                db.session.commit() #save
            else:
                post = Posts.query.filter_by(sno = sno).first()   #filer post by sno =first
                post.title = box_title #already made post just edit as per
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                db.session.commit() #save the current change
            return redirect('/edit/'+sno)
        post = Posts.query.filter_by(sno=sno).first()  #filer post by sno =first
        return render_template('edit.html', params=params, post=post, sno=sno ) #return to edit.html


#file uploader
@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']): #if user in session only then
        if (request.method == 'POST'):
            f=request.files['file1'] #craete var f
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename))) #use f.save to save the file using os module imported abv and
            # app.config(ipload folder) =params (upload loc) in config , secure filename states that fil uploaded is secure. imported from wekzeug

            return "uploaded successfully"

#logout
@app.route("/logout")
def logout():
    session.pop('user') #remove user from session
    return redirect('/dashboard')


#deleting post string:sno is slug
@app.route("/delete/<string:sno>", methods =['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']): #if admin is in session only then
        post = Posts.query.filter_by(sno=sno).first() #filetr post by sno = first
        db.session.delete(post) #del post
        db.session.commit() #save in db
    return redirect('/dashboard')




#creating contact pg
@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        name = request.form.get('name') #input taking from user
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        #create var entry to put the data in db
        entry = Getintouch(name=name, phone_num = phone, msg = message, date= datetime.now(),email = email )
        db.session.add(entry) #add the data collected into db
        db.session.commit() #save
        mail.send_message('New message from ' + name,
                          sender = email,
                          recipients = [params['gmail-user']], #gmail user in cofig file
                          body = message + "\n" + phone
                          ) #sending mail to me
        flash("Thanks for your details . we will get back to you soon :)", "success") #flash msg
    return render_template('contact.html', params=params )  #after sending msg return to cntact


app.run(debug=True) #run the appp object created abv




