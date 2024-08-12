from flask import Flask,jsonify,url_for, render_template, request, redirect, flash, session
import datetime
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)  

UPLOAD_FOLDER = 'static/img/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Define allowed file extensions for image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/gerant")
def gearnt():
    return render_template('gerant.html')

@app.route("/admin")
def adminlogin():
    return render_template('loginadmin.html')

@app.route('/cont')
def cont():
    return render_template('contact.html')
@app.route("/blog-single")
def blogsingle():
    return render_template('blog-single.html')
@app.route("/about")
def about():
    return render_template('portfolio-details.html')
@app.route("/forget")
def forget():
    return render_template('forgetpassword.html')

@app.route("/logingerant", methods=['POST'])
def logingearnt():
    username = request.form['username']
    password = request.form['password']
    
    # Connect to the database
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()

    # Fetch the password for the given username
    cursor.execute('SELECT id, password,idhospital FROM gerant WHERE username = ?', (username,))
    fetched_data = cursor.fetchone()

    if fetched_data and password == fetched_data[1]:
        idgerant = fetched_data[0]
        idhospital = fetched_data[2]
        
        conn.close()
        # Redirect to the dashboard with correct parameter name
        return redirect(url_for('dashboard', id=idgerant, idhospital =idhospital))
    else:
        conn.close()
        # Set error message
        error = "Invalid username or password."
        return render_template('gerant.html', error=error)

@app.route("/contactmsg", methods=['POST'])
def contactmsg():
    email = request.form['email']
    msg = request.form['message']
    id = request.form['id']
    idhospital = 0

    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO contact (email, message) VALUES (?, ?)', (email, msg))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        # Handle error (log it, return error response, etc.)
        return str(e), 500
    finally:
        conn.close()

    return redirect(url_for('dashboard', id=id, idhospital=idhospital))


@app.route("/dashboard/<int:id>/<int:idhospital>")
def dashboard(id,idhospital):
    idgerant = id
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    # Get sum of joiners from 'event joiners' table
    # Get count of rows from 'event joiners' table where idgerant matches
    cursor.execute("SELECT COUNT(*) FROM eventjoiners WHERE idgerant=?", (idgerant,))
    sum_joiners_result = cursor.fetchone()
    sum_joiners = sum_joiners_result[0] if sum_joiners_result else 0
    # Get sum of rows where action=1 from 'donne pub' table
    # Get count of rows from 'donne pub' table where action=1 and idgerant matches
    cursor.execute("SELECT COUNT(*) FROM donnepub WHERE idgerant=?", (idgerant,))
    sum_donnor_result = cursor.fetchone()
    sum_donnor = sum_donnor_result[0] if sum_donnor_result else 0
    cursor.execute("SELECT COUNT(*) FROM neederaction WHERE action=1 AND idgerant=?", (idgerant,))
    sum_needer_result = cursor.fetchone()
    sum_needer = sum_needer_result[0] if sum_needer_result else 0
    cursor.execute("SELECT SUM(Bpos + ABpos + ABneg + Aneg + Apos + Bneg + Opos + Oneg) FROM stock WHERE idhospital=?", (idhospital,))
    sum_donations_result = cursor.fetchone()
    sum_donations = sum_donations_result[0] if sum_donations_result else 0
    cursor.execute("SELECT Bpos, ABpos, ABneg, Aneg, Apos, Bneg, Opos, Oneg FROM stock WHERE idhospital=?", (idhospital,))
    bloodtype = cursor.fetchone()
    cursor.execute("SELECT u.nom, u.prenom, u.wilaya FROM users u JOIN donnepub d ON u.id = d.iddonnor WHERE d.idgerant = ? AND d.action = '1' ORDER BY d.id DESC LIMIT 5; ", (idgerant,))
    recently = cursor.fetchall()


    conn.close()
    return render_template('homedashboard.html',recently=recently,bloodtype = bloodtype,idhospital = idhospital,total=sum_donations, idgerant=idgerant, sum_donnor=sum_donnor, sum_needer=sum_needer)
    
@app.route("/besoinpost/<int:id>/<int:idhospital>")
def besoinpost(id, idhospital):
    email = session.get('email')
    idgerant = id

    # Establish connection to the SQLite database
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()

    # Define the SQL query
# Define the SQL query
    sql_query = """
SELECT id, nom, prenom, phone, wilaya, bloodtype, date
FROM needer
WHERE (id, ?) NOT IN (SELECT id, idgerant FROM neederaction)
"""

# Execute the query with parameter substitution
    cursor.execute(sql_query, (idgerant,))

    # Fetch the publications
    publications = cursor.fetchall()

    # Close cursor and connection
    cursor.close()
    conn.close()

    # Render the template and pass the publications data
    return render_template('besoinpost.html', idgerant=id, publications=publications, idhospital = idhospital)

    


@app.route("/")
def homepage():
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, event_name, event_description, event_date, event_image, wilaya FROM events  WHERE status = 1')
    rows = cursor.fetchall()  
    conn.close()  
    
    publications = []  
    
    for row in rows:
        id, nom, desc, date, image, wilaya = row
        publications.append({
            'id': id,
            'nom': nom,
            'desc': desc,
            'date': date,
            'image': image,
            'wilaya': wilaya,
        })
    return render_template('index.html', publications=publications)

@app.route("/logedin/<int:id>/<string:email>")
def logedin(id, email):
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, event_name, event_description, event_date, event_image, wilaya, idgerant FROM events  WHERE status = 1')
    iduser = id
    rows = cursor.fetchall() 
    conn.close() 
    publications = []  
    for row in rows:
        id, nom, desc, date, image, wilaya, idgerant = row
        publications.append({
            'id': id,
            'nom': nom,
            'desc': desc,
            'date': date,
            'image': image,
            'wilaya': wilaya,
            'idgerant': idgerant,

        })
    return render_template('index2.html', email=email,id= iduser ,publications = publications)
    
@app.route("/login")
def loginpage():
    return render_template('login.html')

@app.route("/loginadmin")
def admin():
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()

    # Fetch all contact data from the database
    cursor.execute("SELECT email, message FROM contact")
    contacts = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM events")
    events_total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM publication")
    publication_total = cursor.fetchone()[0]
    eventandpub =  publication_total + events_total

    cursor.execute("SELECT COUNT(*) FROM donnepub")
    donne_total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM eventjoiners")
    evenjoiners_total = cursor.fetchone()[0]
    donneandneed =  evenjoiners_total + donne_total    
    cursor.execute("SELECT COUNT(*) FROM gerant")
    gerant_total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")
    user_total = cursor.fetchone()[0]

    # Close database connection
    conn.close()

    return render_template('admin.html', contacts=contacts,donneandneed = donneandneed, gerant=gerant_total, users=user_total, eventandpub =eventandpub)


@app.route("/deletedatabase")
def deletedatabase():
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()

    tables = [
        'contact', 'donnepub', 'eventjoiners', 'events', 'gerant', 'Hospital',
        'joinevent', 'needer', 'neederaction', 'publication', 'stock', 'users'
    ]

    try:
        # Turn off foreign key constraints
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION;")
        
        # Generate and execute DELETE commands for all tables
        for table in tables:
            cursor.execute(f"DELETE FROM {table};")
        
        # Commit transaction
        cursor.execute("COMMIT;")
        
    except Exception as e:
        # Rollback in case of an error
        conn.rollback()
        print(f"An error occurred: {e}")
        
    finally:
        # Turn foreign key constraints back on
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Close database connection
        conn.close()
    
    return redirect('/loginadmin')


@app.route("/checkadminlogin", methods=['POST'])
def checkadminlogin():
        username = request.form['username']
        password = request.form['password']
        
        # Connect to the SQLite database
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        c = conn.cursor()
        
        # Check if the username and password exist in the admin table
        c.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password))
        admin_user = c.fetchone()
        
        conn.close()
        
        if admin_user:
            # If admin_user is not None, then username and password exist
            return redirect('loginadmin')
        else:
            # If admin_user is None, then username and/or password is incorrect
            return "Invalid username or password"

@app.route("/addgerant")
def addgerant():
    try:
        # Connect to the database
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()

        # Fetch all gerant data from the database
        cursor.execute("SELECT id, username, password, idhospital FROM gerant")
        gerants_data = cursor.fetchall()

        # Fetch all hospital data from the database
        cursor.execute("SELECT id, nom, adresse FROM hospital")
        hospitals_data = cursor.fetchall()
        
        cursor.execute("SELECT id, Apos,Bpos,Opos,ABpos, Aneg,Bneg,Oneg,ABneg,idhospital FROM stock")
        stock_data = cursor.fetchall()

        # Close database connection
        cursor.execute("SELECT email, message FROM contact")
        contacts = cursor.fetchall()
        # Close database connection
        conn.close()
        # Render the template with the fetched data
        return render_template('addgerant.html', gerants=gerants_data,stock=stock_data, hospitals=hospitals_data, contacts = contacts)

    except Exception as e:
        # Handle errors
        return str(e)

@app.route("/users")
def users():
    try:
        # Connect to the database
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()

        # Fetch all gerant data from the database
        cursor.execute("SELECT id, email, password, nom, prenom, bloodtype, wilaya, phone FROM users")
        users_data = cursor.fetchall()


        # Fetch all gerant data from the database
        cursor.execute("SELECT email, message FROM contact")
        contacts = cursor.fetchall()
        # Close database connection
        conn.close()
        # Render the template with the fetched data
        return render_template('users.html', users=users_data, contacts = contacts)

    except Exception as e:
        # Handle errors
        return str(e)
    
@app.route("/bloodrequest")
def bloodrequest():
    try:
        # Connect to the database
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()

        # Fetch all gerant data from the database
        cursor.execute("SELECT id, nom, prenom, bloodtype, wilaya, phone, iduser FROM needer")
        req_data = cursor.fetchall()
        cursor.execute("SELECT email, message FROM contact")
        contacts = cursor.fetchall()
        # Close database connection
        conn.close()
        # Render the template with the fetched data
        return render_template('bloodrequest.html', req=req_data, contacts = contacts)

    except Exception as e:
        # Handle errors
        return str(e)    

@app.route("/blooddonatio")
def blooddonatio():
    try:
        # Connect to the database
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()

        # Fetch all gerant data from the database
        cursor.execute("SELECT id, iddonnor, idpub, date, idgerant FROM donnepub")
        req_data = cursor.fetchall()

    

        cursor.execute("SELECT email, message FROM contact")
        contacts = cursor.fetchall()
        # Close database connection
        conn.close()
        # Render the template with the fetched data
        return render_template('blooddonatio.html', req=req_data, contacts = contacts)

    except Exception as e:
        # Handle errors
        return str(e)    

@app.route("/pub&event")
def pubEvent():
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        cursor2 = conn.cursor()
        # Fetch all gerant data from the database
        cursor.execute("SELECT id, idgerant, event_name, event_description, event_date,wilaya FROM events")
        req_data = cursor.fetchall()
        cursor2.execute("SELECT id, idgerant, bloodtype, wilaya, desc,phone FROM publication")
        req_data2 = cursor2.fetchall()
        cursor.execute("SELECT email, message FROM contact")
        contacts = cursor.fetchall()
        # Close database connection
        conn.close()
        # Render the template with the fetched data
        return render_template('pub&event.html',req=req_data, req2=req_data2, contacts = contacts)

@app.route("/donnors/<int:idgerant>/<int:idhospital>", methods=['GET', 'POST'])
def donnors(idgerant,idhospital):
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nomevent, description, nomjoiner, prenomjoiner, bloodtype, wilaya, phone, date FROM eventjoiners ")
    events = cursor.fetchall()
    conn.close()
    return render_template('donnors.html', events = events,idhospital=idhospital, idgerant=idgerant)


@app.route("/Signup")
def Signup():
    return render_template('Signup.html')

@app.route("/addnewgerant", methods=['POST'])
def add_newgerant():
    username = request.form['username']
    password = request.form['password']
    hospital = request.form['hospital']
    address = request.form['address']
    
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()

    cursor.execute('INSERT INTO hospital (nom, adresse) VALUES (?, ?)', 
                   (hospital, address))
    
    # Retrieve the generated hospital ID
    hospital_id = cursor.lastrowid
    
    cursor.execute('INSERT INTO gerant (username, password, idhospital) VALUES (?, ?, ?)', 
                   (username, password, hospital_id))  # Fixing the typo here
    cursor.execute('INSERT INTO stock (Apos, Bpos, Opos, ABpos, ABneg, Oneg, Bneg, Aneg, idhospital) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', 
               (0, 0, 0, 0, 0, 0, 0, 0, hospital_id))

    
    conn.commit()
    
    conn.close()
    return redirect(url_for('addgerant'))

@app.route("/editgerantdata", methods=['POST'])
def editgerant():
    username = request.form['username']
    password = request.form['password']
    id = request.form['id']
    
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()

    cursor.execute('UPDATE gerant SET username = ?, password = ? WHERE id = ?', (username, password, id))

    conn.commit()
    conn.close()
    
    return jsonify(status="success")


@app.route("/edithospitaldata", methods=['POST'])
def edithospital():
    name = request.form['name']
    address = request.form['address']
    id = request.form['id']

    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()

    cursor.execute('UPDATE Hospital SET nom = ?, adresse = ? WHERE id = ?', (name, address, id))

    conn.commit()
    conn.close()
    
    return jsonify(status="success")

@app.route("/editstockdata", methods=['POST'])
def editstock():
    Apos = request.form['Apos']
    Bpos = request.form['Bpos']
    Opos = request.form['Opos']
    ABpos = request.form['ABpos']
    Aneg = request.form['Aneg']
    Bneg = request.form['Bneg']
    Oneg = request.form['Oneg']
    ABneg = request.form['ABneg']
    id = request.form['id']

    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()

    cursor.execute('UPDATE stock SET Apos = ?, Bpos = ?, Opos = ?, ABpos = ?, Aneg = ?, Bneg = ?, Oneg = ?, ABneg = ? WHERE id = ?', 
                   (Apos, Bpos, Opos, ABpos, Aneg, Bneg, Oneg, ABneg, id))

    conn.commit()
    conn.close()
    
    return jsonify(status="success")


@app.route("/edituserdata", methods=['POST'])
def edituserdata():
    email = request.form['email']
    password = request.form['password']
    id = request.form['id']
    nom = request.form['nom']
    prenom = request.form['prenom']
    wilaya = request.form['wilaya']
    phone = request.form['phone']
    bloodtype = request.form['bloodtype']
    
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE users SET email = ?, password = ?, nom = ?, prenom = ?, bloodtype = ?, wilaya = ?, phone = ? WHERE id = ?', (email, password, nom, prenom, bloodtype, wilaya, phone, id))
    conn.commit()
    conn.close()
    
    return jsonify(status="success")

@app.route("/editblooddonation", methods=['POST'])
def editblooddonation():
    id = request.form['id']
    iddonnor = request.form['iddonnor']
    idpub = request.form['idpub']
    date = request.form['date']
    idgerant = request.form['idgerant']
    
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE donnepub SET iddonnor = ?, idpub = ?, date = ?, idgerant = ? WHERE id = ?', 
                   (iddonnor, idpub, date, idgerant, id))
    conn.commit()
    conn.close()
    
    return jsonify(status="success")

@app.route("/editbloodrequest", methods=['POST'])
def editbloodrequest():
    nom = request.form['nom']
    prenom = request.form['prenom']
    bloodtype = request.form['bloodtype']
    wilaya = request.form['wilaya']
    phone = request.form['phone']
    id = request.form['id']
    
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE needer SET nom = ?, prenom = ?, bloodtype = ?, wilaya = ?, phone = ? WHERE id = ?', 
                   (nom, prenom, bloodtype, wilaya, phone, id))
    conn.commit()
    conn.close()
    
    return jsonify(status="success")





@app.route("/addneeder", methods=['POST'])
def add_needer():
    email = request.form['email']
    userid = request.form['userid']
    prenom = request.form['prenom']
    nom = request.form['nom']
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    bloodtype = request.form['bloodtype']
    wilaya = request.form['wilaya']
    phone = request.form['phone']
    
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()

    # Using parameterized query to prevent SQL injection
    cursor.execute('INSERT INTO needer (nom, prenom, bloodtype, wilaya, phone, date,  iduser) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                   (nom, prenom, bloodtype, wilaya, phone, current_date, userid))
    conn.commit()
    conn.close()
    return redirect(url_for('besoin', id=userid, email=email))

@app.route("/besoin/<int:id>/<string:email>")
def besoin(id, email):
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    cursor.execute('SELECT nom, prenom, phone, bloodtype, wilaya FROM users WHERE id = ?', (id,))
    rows = cursor.fetchall()
    conn.close()
    
    publications = [] 
    
    for row in rows:
        nom, prenom, phone, bloodtype, wilaya = row
        publications.append({
            'nom': nom,
            'prenom': prenom,
            'wilaya': wilaya,
            'bloodtype': bloodtype,
            'phone': phone,
        })    
    return render_template('besoin.html', id=id ,email=email, publications=publications)


@app.route("/contacter/<int:idgerant>/<int:idhospital>")
def contact(idgerant,idhospital):
    return render_template('contactadmin.html', idgerant=idgerant)

  

@app.route("/bloodrequest/<int:idgerant>/<int:idhospital>", methods=['GET'])
def bloodrequist(idgerant,idhospital):
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, titre, phone, wilaya, desc, bloodtype, status FROM publication WHERE idgerant = ?', (idgerant,))
    rows = cursor.fetchall()  # Fetch all rows instead of just one
    conn.close()  # Close connection after fetching data
    
    publications = []  # Create an empty list to store publication data
    
    for row in rows:
        id, titre, phone, wilaya, desc, bloodtype, status = row
        publications.append({
            'id': id,
            'idgerant': idgerant,
            'titre': titre,
            'phone': phone,
            'wilaya': wilaya,
            'desc': desc,
            'bloodtype': bloodtype,
            'status': status
        })
    
    return render_template('bloodrequiest.html', publications=publications, idgerant=idgerant,idhospital=idhospital)


@app.route('/event/<int:idgerant>/<int:idhospital>', methods=['GET', 'POST'])
def event(idgerant,idhospital):
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, event_name, event_description, event_date, event_image, wilaya, status FROM events WHERE idgerant = ?', (idgerant,))
    rows = cursor.fetchall()  # Fetch all rows instead of just one
    conn.close()  # Close connection after fetching data
    
    publications = []  # Create an empty list to store publication data
    
    for row in rows:
        id , event_name, event_description, event_date, event_image, wilaya, status = row
        publications.append({
            'id' : id,
            'nom': event_name,
            'desc': event_description,
            'date': event_date,
            'image': event_image,
            'wilaya': wilaya,
            'status': status,
        })
    
    return render_template('event.html', publications=publications, idgerant=idgerant,idhospital=idhospital)


@app.route('/addevent', methods=['POST'])
def addevent():
    if request.method == 'POST':
        # Extract data from the form submission
        event_name = request.form['event_name']
        event_description = request.form['event_description']
        event_date = request.form['event_date']
        wilaya = request.form['wilaya']
        idgerant = request.form['idgerant']
        idhospital = request.form['idhospital']
        status = 1
        
        # Check if the post request has the file part
        if 'event_image' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['event_image']
        
        # If the user does not select a file, the browser submits an empty file without a filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        # Check if the file is allowed
        if file and allowed_file(file.filename):
            # Secure the filename to prevent any malicious file uploads
            filename = secure_filename(file.filename)
            
            # Save the file to the designated folder
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Save event data to the database
            conn = sqlite3.connect('base-donnée/blooddonation.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO events (event_name, event_description, event_date, event_image, wilaya, idgerant, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (event_name, event_description, event_date, filename, wilaya, idgerant, status))
            conn.commit()
            conn.close()

            # Redirect user to the events page or a confirmation page
            return redirect(url_for('event',idgerant = idgerant, idhospital=idhospital))


@app.route("/notification/<int:idgerant>/<int:idhospital>", methods=['GET'])
def notification(idgerant, idhospital):
    id = idgerant
    email = session.get('email')
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    conn2 = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    cursor2 = conn2.cursor()
    # Execute a SELECT query to fetch data from donnepub, publication, and users tables
    cursor.execute("""
    SELECT dp.iddonnor, dp.idpub, p.titre, p.wilaya, u.phone, u.bloodtype, u.nom, u.prenom, p.desc, dp.date, dp.id, u.wilaya
    FROM donnepub dp
    JOIN publication p ON dp.idpub = p.id
    JOIN users u ON dp.iddonnor = u.id
    WHERE dp.action != '1' AND dp.idgerant = ?;
""", (id,))

    cursor2.execute("""
        SELECT dp.iddonnor, dp.idevent, p.event_name, p.wilaya, u.phone, u.bloodtype, u.nom, u.prenom, p.event_description, dp.date, dp.id, u.wilaya
FROM joinevent dp
JOIN events p ON dp.idevent = p.id
JOIN users u ON dp.iddonnor = u.id
WHERE dp.action != '1' AND dp.idgerant= ?;
""", (id,))

    # Fetch all rows of the query result
    publications = cursor.fetchall()
    events = cursor2.fetchall()
    # Close the cursor and database connection
    cursor.close()
    cursor2.close()
    conn.close()
    conn2.close()
    
    return render_template('notification.html',idhospital =idhospital, email=email, publications=publications, events = events, idgerant = idgerant)

    
@app.route("/pub/<int:id>/<string:email>")
def pub(id, email):
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    

    # Execute a SELECT query to fetch data from the publication table
    cursor.execute("SELECT titre, wilaya, phone, bloodtype, desc, id, idgerant FROM publication WHERE status = 1")

    # Fetch all rows of the query result
    publications = cursor.fetchall()

    # Close the cursor and database connection
    cursor.close()
    conn.close()
    return render_template('pub.html',id=id,  email=email, publications=publications)

@app.route("/pub2/<int:id>/<string:email>")
def pub2(id, email):
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    

    # Execute a SELECT query to fetch data from the publication table
    cursor.execute("SELECT titre, wilaya, phone, bloodtype, desc, id, idgerant FROM publication WHERE status = 1")

    # Fetch all rows of the query result
    publications = cursor.fetchall()

    # Close the cursor and database connection
    cursor.close()
    conn.close()
    return render_template('pub2.html',id=id,  email=email, publications=publications)
@app.route("/update_status", methods=['POST'])
def update_status():
    if request.method == 'POST':
        # Extract id and status from the form submission
        publication_id = request.form['id']
        status = request.form['status']
        idgerant = request.form['idgerant']
        idhospital = request.form['idhospital']

        
        # Update status in the database
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE publication SET status = ? WHERE id = ? AND idgerant = ?', (status, publication_id, idgerant))
        conn.commit()
        conn.close()
        
        # Redirect to the bloodrequiest route
        return redirect(url_for('bloodrequist', idgerant=idgerant, idhospital =idhospital))

    # If not a POST request, return an error or redirect to an error page
    return 'Method Not Allowed', 405  # Method Not Allowed status code
 
@app.route("/update_status2", methods=['POST'])
def update_status2():
    if request.method == 'POST':
        # Extract id, status, and idgerant from the form submission
        publication_id = request.form['id']
        status = request.form['status']
        idgerant = (request.form['idgerant'])  # Convert idgerant to integer
        idhospital = (request.form['idhospital'])  # Convert idgerant to integer
        
        # Update status in the database
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE events SET status = ? WHERE id = ? AND idgerant = ?', (status, publication_id, idgerant))
        conn.commit()
        conn.close()
        
        # Redirect to the event route
        return redirect(url_for('event', idgerant=idgerant, idhospital=idhospital))


    # If not a POST request, return an error or redirect to an error page
    return 'Method Not Allowed', 405  # Method Not Allowed status code
 
 
@app.route("/suppub", methods=['POST'])
def suppub(): 
    if request.method == 'POST':
        # Extract id and status from the form submission
        id = request.form['id']
        idhospital = request.form['idhospital']  
        idgerant = request.form['idgerant']
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM publication WHERE id = ? AND idgerant = ?', (id, idgerant))
        conn.commit()
        conn.close()
        
        # Redirect to the bloodrequiest route
        return redirect(url_for('bloodrequist', idgerant=idgerant, idhospital = idhospital))
    
@app.route("/deletegerant", methods=['POST'])
def deletgerant(): 
    if request.method == 'POST':
        # Extract id and status from the form submission
        id = request.form['id']
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM gerant WHERE id = ? ', (id))
        conn.commit()
        conn.close()
        
        # Redirect to the bloodrequiest route
        return redirect(url_for('addgerant'))    

@app.route("/deletehospital", methods=['POST'])
def deletehospital(): 
    if request.method == 'POST':
        # Extract id and status from the form submission
        id = request.form['id']
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM hospital WHERE id = ? ', (id))
        conn.commit()
        conn.close()
        
        # Redirect to the bloodrequiest route
        return redirect(url_for('addgerant'))   

@app.route("/deletemanager", methods=['POST'])
def deletemanager(): 
    if request.method == 'POST':
        # Extract id and status from the form submission
        id = request.form['id']
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM gerant WHERE id = ? ', (id))
        conn.commit()
        conn.close()
        
        # Redirect to the bloodrequiest route
        return redirect(url_for('addgerant'))   
    
@app.route("/deleteuser", methods=['POST'])
def deleteuser(): 
    if request.method == 'POST':
        # Extract id from the form submission
        id = request.form['id']
        print(f"Received ID: {id}")  # Debugging line to print the ID

        # Ensure id is passed as a single-element tuple
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM users WHERE id = ?', (id,))
            conn.commit()
        except sqlite3.ProgrammingError as e:
            print(f"SQLite error: {e}")  # Debugging line to print the error
        finally:
            conn.close()
        
        # Redirect to the users route
        return redirect(url_for('users'))
 
@app.route("/deleteblooddonation", methods=['POST'])
def deleteblooddonation(): 
    if request.method == 'POST':
        # Extract id from the form submission
        id = request.form['id']
        print(f"Received ID: {id}")  # Debugging line to print the ID

        # Ensure id is passed as a single-element tuple
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM donnepub WHERE id = ?', (id,))
            conn.commit()
        except sqlite3.ProgrammingError as e:
            print(f"SQLite error: {e}")  # Debugging line to print the error
        finally:
            conn.close()
        
        # Redirect to the users route
        return redirect(url_for('blooddonatio'))
       
@app.route("/deletebloodrequest", methods=['POST'])
def deletebloodrequest(): 
    if request.method == 'POST':
        # Extract id from the form submission
        id = request.form['id']
        print(f"Received ID: {id}")  # Debugging line to print the ID

        # Ensure id is passed as a single-element tuple
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM needer WHERE id = ?', (id,))
            conn.commit()
        except sqlite3.ProgrammingError as e:
            print(f"SQLite error: {e}")  # Debugging line to print the error
        finally:
            conn.close()
        
        # Redirect to the users route
        return redirect(url_for('bloodrequest'))       

@app.route("/deletepub", methods=['POST'])
def deletepub():
    if request.method == 'POST':
        # Extract id from the form submission
        id = request.form['id']
        print(f"Received ID: {id}")  # Debugging line to print the ID

        # Ensure id is passed as a single-element tuple
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM publication WHERE id = ?', (id,))
            conn.commit()
        except sqlite3.ProgrammingError as e:
            print(f"SQLite error: {e}")  # Debugging line to print the error
        except sqlite3.Error as e:
            print(f"Database error: {e}")  # General database error handling
        finally:
            conn.close()
        
        # Redirect to the correct endpoint
        return redirect(url_for('users'))  # Use the function name as the endpoint

 

@app.route("/deleteevent", methods=['POST'])
def deleteevent(): 
    if request.method == 'POST':
        # Extract id from the form submission
        id = request.form['id']
        print(f"Received ID: {id}")  # Debugging line to print the ID

        # Ensure id is passed as a single-element tuple
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM events WHERE id = ?', (id,))
            conn.commit()
        except sqlite3.ProgrammingError as e:
            print(f"SQLite error: {e}")  # Debugging line to print the error
        finally:
            conn.close()
        
        # Redirect to the users route
        return redirect(url_for('users'))      

@app.route("/deletestock", methods=['POST'])
def deletestock(): 
    if request.method == 'POST':
        # Extract id and status from the form submission
        id = request.form['id']
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM stock WHERE id = ? ', (id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('addgerant'))       
    
@app.route("/supevent", methods=['POST'])
def supevent(): 
    if request.method == 'POST':
        # Extract id and status from the form submission
        id = request.form['id']
        idgerant = request.form['idgerant']
        idhospital = request.form['idhospital']
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM events WHERE id = ? and idgerant =?', (id, idgerant))
        conn.commit()
        conn.close()
        
        # Redirect to the bloodrequiest route
        return redirect(url_for('event',idgerant = idgerant, idhospital=idhospital))
    
@app.route("/suppdonate", methods=['POST'])
def supdonate(): 
    if request.method == 'POST':
        # Extract id and status from the form submission
        id = request.form['id']
        idgerant = request.form['idgerant']
        idhospital = request.form['idhospital']
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM donnepub WHERE id = ? AND idgerant = ?', (id, idgerant))
        conn.commit()
        conn.close()
        
        # Redirect to the bloodrequiest route
        return redirect(url_for('notification',idgerant = idgerant, idhospital = idhospital))  
    
@app.route("/suppjoiner", methods=['POST'])
def suppjoiner(): 
    if request.method == 'POST':
        # Extract id and status from the form submission
        id = request.form['id']
        idgerant = request.form['idgerant']
        idhospital = request.form['idhospital']

        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM joinevent WHERE id = ? AND idgerant = ?', (id, idgerant))
        conn.commit()
        conn.close()
        
        # Redirect to the bloodrequiest route
        return redirect(url_for('notification',idgerant = idgerant, idhospital=idhospital))  

@app.route('/login', methods=['POST'])
def logincheck():
    email = request.form['email']
    password = request.form['password']
    session['email'] = email
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    
    # Check if the user is a gerant
    cursor.execute('SELECT * FROM gerant WHERE username = ? AND password = ?', (email, password))
    gerant = cursor.fetchone()
    
    if gerant:
        cursor.execute('SELECT id, password,idhospital FROM gerant WHERE username = ?', (email,))
        fetched_data = cursor.fetchone()
        idgerant = fetched_data[0]
        idhospital = fetched_data[2]
        conn.close()
        return redirect(url_for('dashboard', id=idgerant, idhospital =idhospital))

    # Check if the user is a regular user
    cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
    user = cursor.fetchone()
    
    conn.close()
    
    if user:
        # If the user is a regular user, redirect to '/logedin'
        session['email'] = user[1]
        id = user[0]  
        return redirect(url_for('logedin', id=id, email=email))  
    
    else:
        return 'Invalid username or password'

    
    
@app.route('/donate', methods=['POST'])
def donate():
    if request.method == 'POST':
        id = request.form['userid']
        publication_id = request.form['id']
        user_email = request.form['email']
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        idgerant = request.form['idgerant']
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        action =0
        # Insert data into donnepub table
        cursor.execute("INSERT INTO donnepub (iddonnor, idpub, date, action, idgerant) VALUES ((SELECT id FROM users WHERE email = ?), ?, ?, ?, ?)", (user_email, publication_id, current_date, action, idgerant))
        
        conn.commit()
        conn.close()

    return redirect(url_for('pub',id =id,email =user_email))


@app.route('/joinevent2', methods=['POST'])
def joinevent2():
    if request.method == 'POST':
        publication_id = request.form['id']
        user_email = request.form['email']
        idgerant = request.form['idgerant']

        current_date = datetime.datetime.now().strftime('%Y-%m-%d')

        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        action =0
        # Insert data into donnepub table
        cursor.execute("INSERT INTO joinevent (iddonnor, idevent, date, action ,idgerant) VALUES ((SELECT id FROM users WHERE email = ?), ?, ?, ?, ?)", (user_email, publication_id, current_date, action, idgerant))
        
        conn.commit()
        conn.close()
    return redirect(url_for('logedin', id = idgerant, email = user_email ))  

@app.route('/confirmdonate', methods=['POST'])
def confirmdonate():
    if request.method == 'POST':
        id = request.form['id']
        idgerant = request.form['idgerant']
        idhospital = request.form['idhospital']
        bloodtype = request.form['bloodtype']
        
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        action = 1
        # Insert data into donnepub table
        cursor.execute('UPDATE donnepub SET action = ? WHERE id = ? AND idgerant = ?' , (action, id ,idgerant))
        cursor.execute('SELECT Bpos, ABpos, ABneg, Aneg, Apos, Bneg, Opos, Oneg FROM Stock WHERE idhospital = ?', (idhospital,))
        row = cursor.fetchone()
        if row:
                Bpos, ABpos, ABneg, Aneg, Apos, Bneg, Opos, Oneg = row
    # Update stock counts based on blood type
                if bloodtype == 'A+':
                     Apos += 1
                elif bloodtype == 'B+':
                     Bpos += 1
                elif bloodtype == 'AB+':
                     ABpos += 1
                elif bloodtype == 'AB-':
                     ABneg += 1
                elif bloodtype == 'B-':
                     Bneg += 1
                elif bloodtype == 'A-':
                     Aneg += 1
                elif bloodtype == 'O+':
                     Opos += 1
                elif bloodtype == 'O-':
                     Oneg += 1

    # Update stock table
        cursor.execute('UPDATE Stock SET Bpos=?, ABpos=?, ABneg=?, Aneg=?, Apos=?, Bneg=?, Opos=?, Oneg=? WHERE idhospital=?',
                   (Bpos, ABpos, ABneg, Aneg, Apos, Bneg, Opos, Oneg, idhospital))

        conn.commit()
        conn.close()

    return redirect(url_for('notification',idhospital=idhospital,idgerant = idgerant)) 

import sqlite3
from flask import request, redirect, url_for

@app.route('/suppneeder', methods=['POST'])
def suppneeder():
    if request.method == 'POST':
        idneeder = request.form['idneeder']
        idgerant = request.form['idgerant']
        idhospital = request.form['idhospital']
        action = 0  

        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()

        # Check if a record with given idneeder and idgerant exists
        cursor.execute('SELECT * FROM neederaction WHERE idneeder = ? AND idgerant = ?', (idneeder, idgerant))
        existing_record = cursor.fetchone()

        if existing_record:
            # Update the action
            cursor.execute('UPDATE neederaction SET action = ? WHERE idneeder = ? AND idgerant = ?', (action, idneeder, idgerant))
        else:
            # Insert data into neederaction table
            cursor.execute('INSERT INTO neederaction (idneeder, idgerant, action) VALUES (?, ?, ?)', (idneeder, idgerant, action))

        # Commit the transaction 
        conn.commit()
        # Close the connection
        conn.close()
        
        return redirect(url_for('besoinpost', id=idgerant ,idhospital=idhospital))



@app.route('/acceptneeder', methods=['POST'])
def acceptneeder():
    if request.method == 'POST':
        idneeder = request.form['idneeder']
        idgerant = request.form['idgerant']
        idhospital = request.form['idhospital']
        
        action = 1  
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        # Check if a record with given idneeder and idgerant exists
        cursor.execute('SELECT * FROM neederaction WHERE idneeder = ? AND idgerant = ?', (idneeder, idgerant))
        existing_record = cursor.fetchone()

        if existing_record:
            # Update the action
            cursor.execute('UPDATE neederaction SET action = ? WHERE idneeder = ? AND idgerant = ?', (action, idneeder, idgerant))
        else:
            cursor.execute('INSERT INTO neederaction (idneeder, idgerant, action) VALUES (?, ?, ?)', (idneeder, idgerant, action))
        # Commit the transaction 
        conn.commit()
        # Close the connection
        conn.close()
        
        return redirect(url_for('besoinpost', id=idgerant, idhospital=idhospital))


@app.route('/confirmjoiner', methods=['POST'])
def confirmjoiner():
    if request.method == 'POST':
        id = request.form['id']
        nom = request.form['nom']
        prenom = request.form['prenom']
        bloodtype = request.form['bloodtype']
        phone = request.form['phone']
        wilaya = request.form['wilaya']
        event = request.form['event']
        desc = request.form['desc']
        date = request.form['date']        
        idgerant = request.form['idgerant']
        idhospital = request.form['idhospital']
        conn = sqlite3.connect('base-donnée/blooddonation.db')
        cursor = conn.cursor()
        action = 1
        # Insert data into donnepub table
        cursor.execute('UPDATE joinevent SET action = ? WHERE id = ? AND idgerant = ?' , (action, id ,idgerant))
        cursor2 = conn.cursor()
        cursor2.execute('INSERT INTO eventjoiners (nomevent, description, nomjoiner, prenomjoiner, bloodtype, wilaya, phone, date, idgerant) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (event, desc, nom, prenom , bloodtype, wilaya, phone, date, idgerant))
        cursor.execute('UPDATE donnepub SET action = ? WHERE id = ? AND idgerant = ?' , (action, id ,idgerant))
        cursor.execute('SELECT Bpos, ABpos, ABneg, Aneg, Apos, Bneg, Opos, Oneg FROM Stock WHERE idhospital = ?', (idhospital,))
        row = cursor.fetchone()
        if row:
                Bpos, ABpos, ABneg, Aneg, Apos, Bneg, Opos, Oneg = row
    # Update stock counts based on blood type
                if bloodtype == 'A+':
                     Apos += 1
                elif bloodtype == 'B+':
                     Bpos += 1
                elif bloodtype == 'AB+':
                     ABpos += 1
                elif bloodtype == 'AB-':
                     ABneg += 1
                elif bloodtype == 'B-':
                     Bneg += 1
                elif bloodtype == 'A-':
                     Aneg += 1
                elif bloodtype == 'O+':
                     Opos += 1
                elif bloodtype == 'O-':
                     Oneg += 1

    # Update stock table
        cursor.execute('UPDATE Stock SET Bpos=?, ABpos=?, ABneg=?, Aneg=?, Apos=?, Bneg=?, Opos=?, Oneg=? WHERE idhospital=?',
                   (Bpos, ABpos, ABneg, Aneg, Apos, Bneg, Opos, Oneg, idhospital))

        conn.commit()
        conn.close()

    return redirect(url_for('notification',idgerant = idgerant, idhospital=idhospital)) 


    
@app.route('/Signup', methods=['POST'])
def signup():
    email = request.form['email']  
    password = request.form['password']
    nom = request.form['nom']
    prenom = request.form['prenom']
    bloodtype = request.form['bloodtype']
    wilaya = request.form['wilaya']
    phone = request.form['phone']

    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    
    cursor.execute('INSERT INTO users (email, password , nom, prenom , bloodtype, wilaya, phone) VALUES (?, ?, ?, ?, ?, ?, ?)', (email, password , nom, prenom , bloodtype, wilaya, phone))
    conn.commit()
    conn.close()

    return redirect('/login') 

@app.route('/addpub', methods=['POST'])
def addpub():
    titre = request.form['titre']  
    phone = request.form['phone']
    wilaya = request.form['wilaya']
    desc = request.form['desc']
    bloodtype = request.form['bloodtype']
    status = 1
    idgerant= request.form['idgerant']
    idhospital= request.form['idhospital']
    

    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    
    cursor.execute('INSERT INTO publication (titre, phone , wilaya, desc , bloodtype, status, idgerant) VALUES (?, ?, ?, ?, ?, ?, ?)', (titre, phone , wilaya, desc , bloodtype, status, idgerant))
    conn.commit()
    conn.close()

    return redirect(url_for('bloodrequist', idgerant=idgerant, idhospital=idhospital))

@app.route('/editpub', methods=['POST'])
def editpub():
    id = request.form['id']  
    idgerant = request.form['idgerant']  
    idhospital = request.form['idhospital']  

    titre = request.form['titre']  
    phone = request.form['phone']
    wilaya = request.form['wilaya']
    desc = request.form['desc']
    bloodtype = request.form['bloodtype']

    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE publication 
    SET titre = ?, phone = ?, wilaya = ?, bloodtype = ?, desc = ? 
    WHERE id = ? AND idgerant = ?''', (titre, phone, wilaya, bloodtype, desc, id, idgerant))
    conn.commit()
    conn.close()

    return redirect(url_for('bloodrequist', idgerant=idgerant, idhospital = idhospital))

@app.route("/editpubb", methods=['POST'])
def editpubb():
    id = request.form['id']
    titre = request.form['titre']
    phone = request.form['phone']
    wilaya = request.form['wilaya']
    desc = request.form['desc']
    bloodtype = request.form['bloodtype']
    
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE publication 
        SET titre = ?, phone = ?, wilaya = ?, bloodtype = ?, desc = ? 
        WHERE id = ?
    ''', (titre, phone, wilaya, bloodtype, desc, id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('pubEvent'))

@app.route("/editeventt", methods=['POST'])
def editeventt():
    id = request.form['id']
    nom = request.form['event_nom']
    date = request.form['event_date']
    wilaya = request.form['event_wilaya']
    desc = request.form['event_desc']
    
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE events 
        SET event_name = ?, event_description = ?, event_date = ?, wilaya = ? 
        WHERE id = ?
    ''', (nom, desc, date, wilaya, id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('pubEvent'))

@app.route('/editevent', methods=['POST'])
def editevent():
    id = request.form['id']  
    nom = request.form['nom']  
    wilaya = request.form['wilaya']
    desc = request.form['desc']
    date = request.form['event_date']
    idgerant = request.form['idgerant']
    idhospital = request.form['idhospital']
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE events 
    SET event_name = ?, event_description = ?, event_date = ?,  wilaya = ? 
    WHERE id = ? AND idgerant = ?''', (nom, desc, date, wilaya, id, idgerant))

    conn.commit()
    conn.close()
    return redirect(url_for('event', idgerant=idgerant, idhospital=idhospital))

@app.route("/changepass", methods=['POST'])
def changepass():
    password = request.form.get('password')
    email = request.form.get('email')
    id = request.form.get('id')
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE users SET password = ? WHERE email = ?', (password, email))
    conn.commit()
    conn.close()
    return redirect(url_for('logedin',id = id, email = email))


@app.route("/myaccount/<int:id>/<string:email>")
def myaccount(id, email):
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    cursor.execute('SELECT nom, prenom, bloodtype, wilaya, phone, situation FROM users WHERE email = ?', (email,))
    row = cursor.fetchone()
    if row:
        nom, prenom, bloodtype, wilaya, phone, situation = row
        return render_template('myaccount.html', id=id, email=email, nom=nom, prenom=prenom, bloodtype=bloodtype, wilaya=wilaya, phone=phone, situation=situation)

@app.route('/changeinfo', methods=['POST'])
def changeinfo():
    id = request.form['id']
    email = request.form['email']
    nom = request.form['nom']
    prenom = request.form['prenom']
    bloodtype = request.form['bloodtype']
    wilaya = request.form['wilaya']
    phone = request.form['numero']  # Corrected to match HTML input name
    conn = sqlite3.connect('base-donnée/blooddonation.db')
    cursor = conn.cursor()
    currentemail = request.form['em']  # Corrected to match HTML input name
    session['email'] = email
    cursor.execute('UPDATE users SET email = ?, nom = ?, prenom = ?, bloodtype = ?, wilaya = ?, phone = ? WHERE email = ?', 
                   (email, nom, prenom, bloodtype, wilaya, phone, currentemail))
    conn.commit()
    conn.close()
    return redirect(url_for('myaccount', id=id, email=email))
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050, debug=True)