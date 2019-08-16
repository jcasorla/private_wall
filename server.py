from flask import Flask, render_template, request, redirect,session, flash
from mysqlconnection import connectToMySQL
import re	# the regex module
from flask_bcrypt import Bcrypt        



#secret key required for session
app = Flask(__name__)
app.secret_key = 'keep it secret, keep it safe' # set a secret key for security purposes
bcrypt = Bcrypt(app)     # we are creating an object called bcrypt, 
                         # which is made by invoking the function Bcrypt with our app as an argument

myDB='flask'

# create a regular expression object that we'll use later   
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/users', methods=['POST'])
def create_user():
    print("Got Post Info")
    print(request.form)
    
    failed=False
    
    if len(request.form['email']) < 1:
        flash("Email cannot be blank!")
        failed=True
    elif not EMAIL_REGEX.match(request.form['email']):    # test whether a field matches the pattern
        flash("Invalid email address!")
        failed=True
    else:
        query2="select * from users where email=%(em)s"
        data2 = {
        "em": request.form['email']            
        }
        mysql = connectToMySQL(myDB)
        emailv=mysql.query_db(query2,data2)
        if(bool(emailv)==True):            
            flash("Please chose another email")
            failed=True

    if len(request.form['first_name']) < 1:
        flash("first name cannot be blank!")
        failed=True
    if len(request.form['last_name']) < 1:
        flash("last name cannot be blank!")
        failed=True

    if len(request.form['pwd']) < 1:
        flash("password cannot be blank!")
        failed=True
    if len(request.form['cpwd']) < 1:
        flash("confirm password cannot be blank!")
        failed=True
    if request.form['pwd'] != request.form['cpwd']:
        flash("Passwords do not match")
        failed=True
        

    if(failed==True):
        return redirect("/")

    
    elif not '_flashes' in session.keys():	# no flash messages means all validations passed
        pw_hash = bcrypt.generate_password_hash(request.form['pwd'])
                
        query="insert into users (first_name,last_name,email,password,created_at,updated_at)  values (%(fn)s,%(ln)s,%(em)s,%(pw)s, NOW(),NOW());"

        data = {
            "fn": request.form['first_name'],
            "ln": request.form['last_name'],
            "em": request.form['email'],
            "pw": pw_hash
        }
        mysql = connectToMySQL(myDB)
        id=mysql.query_db(query,data)
        print(id)

        query2="select * from users where id=%(id)s"
        data2 = {
            "id": id            
        }

        mysql = connectToMySQL(myDB)
        user=mysql.query_db(query2,data2)[0]

        session['id']=id
        session['name']=user['first_name']
        return redirect('/show')

@app.route('/show')
def showUser():

    query="select * from users where id<>%(id)s"
    data = {
        "id": session['id']        
    }

    mysql = connectToMySQL(myDB)
    users=mysql.query_db(query,data)
    #select m.text,m.id,m.users_id, m.recipient_id,u.first_name, u.last_name from messages m join users u on u.id=m.recipient_id where m.users_id=
    query="select m.text,m.id,m.users_id, m.recipient_id,u.first_name, u.last_name from messages m join users u on u.id=m.recipient_id where m.recipient_id=%(id)s"
    data = {
        "id": session['id']            
    }

    mysql = connectToMySQL(myDB)
    messages=mysql.query_db(query,data)
    
    if(bool(session)):
        return render_template("show.html", all_users=users,messages=messages)
    else:
        return redirect("/")


@app.route('/login', methods=['POST'])
def login():
    failed=False
    if len(request.form['email']) < 1:
        flash("Email cannot be blank!")
        failed=True
    elif not EMAIL_REGEX.match(request.form['email']):    # test whether a field matches the pattern
        flash("Invalid email address!")
        failed=True
    else:
        query2="select * from users where email=%(em)s"
        data2 = {
        "em": request.form['email']            
        }
        mysql = connectToMySQL(myDB)
        emailv=mysql.query_db(query2,data2)
        if(bool(emailv)==False):            
            flash("Unable to Login")
            failed=True

    if len(request.form['pwd']) < 1:
        flash("password cannot be blank!")
        failed=True

    elif not '_flashes' in session.keys():
        print(request.form["email"])
        mysql = connectToMySQL(myDB)
        query = "SELECT * FROM users WHERE email like %(em)s;"
        data = { "em" : request.form["email"] }
        result = mysql.query_db(query, data)
        if len(result) > 0:
            if bcrypt.check_password_hash(result[0]['password'], request.form['pwd']):
                # if we get True after checking the password, we may put the user id in session
                session['id'] = result[0]['id']
                session['name'] = result[0]['first_name']
                # never render on a post, always redirect!
            else:
                flash("Unable to Login")
                print("Unable to login")
                failed=True
   

    if(failed==True):
        return redirect("/")
    else:
        return redirect("/show")

@app.route('/send', methods=['POST'])
def sendMessage():

    if len(request.form['message']) < 5:
        flash("message should be ateast 5 characters long!")
        return redirect("/show")

    elif not '_flashes' in session.keys():	# no flash messages means all validations passed
        query="insert into messages (text,users_id,recipient_id,created_at,updated_at)  values (%(message)s,%(id)s,%(r_id)s, NOW(),NOW());"

        data = {
            "message": request.form['message'],
            "r_id": request.form['recipient_id'],
            "id": session['id']
        }
        mysql = connectToMySQL(myDB)
        mysql.query_db(query,data)
    

    return redirect("/show")

@app.route("/delete/<int:id>")

def delete_message(id):
    id=id
    print(id)

    query="delete from messages where id=%(id)s"
    data = {
        "id": id,                
    }
    mysql = connectToMySQL('flask')
    mysql.query_db(query,data)

    
    return redirect("/show")  



@app.route('/logout')
def logout():

    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)  