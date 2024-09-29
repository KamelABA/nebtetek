from flask import Flask, render_template, request, redirect, send_from_directory, session, url_for
import cv2
import tensorflow as tf
import numpy as np
import datetime
from keras.models import load_model
import sqlite3
import os
import torch


def calculate_mean(arr: np.ndarray) -> float:
    return np.mean(arr)


app = Flask(__name__, template_folder='HtmlPage')
app.secret_key = 'your_secret_key'

COUNT = 0

model_potato = load_model("Potato.h5")
model_tomato = load_model("Tomato.h5")
model_grape = load_model("Grape.h5")
model_cotton = load_model("Cotton.h5")
model_corn = load_model("Corn.h5")
# model_Apple = load_model("apple.h5")



HtmlTemplate = ['potato', 'cotton', 'corn', 'tomato', 'grape','Apple']


@app.route('/')
def home():
    return render_template('home.html')





@app.route('/login')
def Login():
     error = request.args.get('error')
     return render_template('login.html', error=error)

@app.route('/detect_plant')
def detect_plant():

    if 'email' in session and 'id' in session:
        email = session['email']
        password = session['password']
        user_id = session['id']
        
    conn = sqlite3.connect('PlantDisease.db')
    c = conn.cursor()

    try:
        # Check if the email and hashed password exist in the users table
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
    except Exception as e:
        conn.close()
        return redirect(url_for('Login', error=str(e)))
    
    conn.close()
    
    if user:
        session['email'] = email
        session['password'] = password
        session['id'] = user[0]
        return redirect(url_for('leaf'))
    else:
        return redirect(url_for('Login', error='User not found or incorrect password.', email=email, password=password, id=user_id))



visitor_count = 0

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    global visitor_count
    visitor_count += 1  # Increment the visitor count on each visit

    # Handle POST request for language selection
    if request.method == 'POST':
        lang = request.form.get('lang')  # Get selected language from the form
        session['lang'] = lang  # Store the selected language in the session
        return redirect(url_for('settings'))  # Redirect to reflect the changes

    # Default language is English if not set in the session
    lang = session.get('lang', 'en')

    return render_template('settings.html', lang=lang, visitor_count=visitor_count)

@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/users')
def users():
    try:
        # Connect to the database
        conn = sqlite3.connect('PlantDisease.db')
        cursor = conn.cursor()

        # Fetch all gerant data from the database
        cursor.execute("SELECT id, email, password FROM users")
        users_data = cursor.fetchall()

        conn.close()
        # Render the template with the fetched data
        return render_template('users.html', users=users_data)
    except Exception as e:
        # Handle errors
        return str(e)


@app.route('/supplement')
def supplement():
    try:
        # Use a context manager for the database connection
        with sqlite3.connect('PlantDisease.db') as conn:
            cursor = conn.cursor()
            # Fetch all supplement data from the database
            cursor.execute(
                'SELECT id, disease_name, supplementName FROM Supplement')
            req_data = cursor.fetchall()
        # Render the template with the fetched data
        return render_template('supplement.html', req=req_data)

    except Exception as e:
        # Handle errors (e.g., render an error template)
        return str(e)


@app.route('/diseaseinfo')
def diseaseinfo():
    try:
        # Connect to the database
        conn = sqlite3.connect('PlantDisease.db')
        cursor = conn.cursor()

        # Fetch all relevant data from the database
        cursor.execute(
            "SELECT id, disease_name, description, PossibleSteps FROM DiseaseInfromation")
        req_data = cursor.fetchall()

        # Close the database connection
        conn.close()

        # Handle encoding issues for the 'PossibleSteps' column
        cleaned_data = []
        for row in req_data:
            id, disease_name, description, possible_steps = row
            if isinstance(possible_steps, bytes):
                possible_steps = possible_steps.decode('utf-8', 'replace')
            else:
                possible_steps = str(possible_steps)  # Ensure it's a string
            cleaned_data.append(
                (id, disease_name, description, possible_steps))

        # Render the template with the fetched and cleaned data
        return render_template('diseasesInfo.html', req=cleaned_data)

    except Exception as e:
        # Handle errors
        return str(e)


@app.route('/<temp>')
def predict_crop(temp):
    if temp in HtmlTemplate:
        return render_template(f'{temp}.html')
    else:
        return render_template('404.html'), 404


def get_disease_info(disease_name):
    conn = sqlite3.connect('PlantDisease.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT description, PossibleSteps FROM DiseaseInfromation WHERE disease_name = ?", (disease_name,))
    result = cursor.fetchone()
    conn.close()
    if result:
        Description, possiblesteps = result
    else:
        Description, possiblesteps = "No information available", "No recommendations"
    return Description, possiblesteps


def get_Supplement_info(disease_name):
    conn = sqlite3.connect('PlantDisease.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT SupplementName, SupplementImage FROM Supplement WHERE disease_name = ?", (disease_name,))
    result = cursor.fetchone()
    conn.close()
    if result:
        SupplementName, SupplementImage = result
    else:
        SupplementName, SupplementImage = "No information available", "No recommendations"
    return SupplementName, SupplementImage


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/adduser', methods=['POST'])
def adduser():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        try:
            # Connect to SQLite database
            conn = sqlite3.connect('PlantDisease.db')
            cursor = conn.cursor()

            # Insert data into User table
            cursor.execute("INSERT INTO users (password, email, name) VALUES (?, ?, ?)",
                       (password, email, name))

            # Commit changes
            conn.commit()

            return redirect(url_for('Login'))
        except Exception as e:
            conn.rollback()
            error_message = f"Error occurred while inserting data: {e}. Details: {str(e)}"
            return error_message
        finally:
            # Close connection
            if conn:
                conn.close()

    return redirect(url_for('signup'))


@app.route('/leaf-detection')
def leaf():
    if 'email' in session and 'id' in session:
        email = session['email']
        user_id = session['id']
        conn = sqlite3.connect('PlantDisease.db')
        cursor = conn.cursor()
        
        # Fetch the name from the users table
        cursor.execute('SELECT name FROM users WHERE id = ?', (user_id,))
        data = cursor.fetchone()  # Fetch a single row
        
        conn.close()

        if data:
            name = data[0]  # 'name' is the first and only column selected
        else:
            name = None  # Handle case when no data is returned

        return render_template('leaf-detection.html', name=name, email=email, id=user_id)
    else:
        return "Session data missing."





@app.route("/checklogin", methods=['POST'])
def checklogin():
    email = request.form['email']
    password = request.form['password']
    
    # Connect to the SQLite database
    conn = sqlite3.connect('PlantDisease.db')
    c = conn.cursor()
    
    try:
        # Check if the email and hashed password exist in the users table
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
    except Exception as e:
        conn.close()
        return redirect(url_for('Login', error=str(e)))
    
    conn.close()
    
    if user:
        session['email'] = email
        session['password'] = password
        session['id'] = user[0]
        return redirect(url_for('leaf'))
    else:
        return redirect(url_for('Login', error='User not found or incorrect password.'))


def save_image(img, count):
    img_path = f'static/img/{count}.jpg'
    img.save(img_path)
    if not os.path.exists(img_path):
        raise ValueError("Image not saved correctly")
    return img_path

def preprocess_image(img_path):
    img_arr = cv2.imread(img_path)
    if img_arr is None:
        raise ValueError("Image not read correctly")
    img_arr = cv2.resize(img_arr, (224, 224))
    img_arr = img_arr / 255.0
    img_arr = img_arr.reshape(1, 224, 224, 3)
    return img_arr

def store_prediction(cursor, user_id, disease_name, description, possiblesteps, supplement_name, current_date):
    cursor.execute(
        'INSERT INTO Historique (iduser, DiseaseName, Explanation, Recommendations, Supplement, date) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, disease_name, description, possiblesteps, supplement_name, current_date)
    )

def save_image(img, count):
    img_path = f'static/img/{count}.jpg'
    img.save(img_path)
    if not os.path.exists(img_path):
        raise ValueError("Image not saved correctly")
    return img_path

def preprocess_image(img_path):
    img_arr = cv2.imread(img_path)
    if img_arr is None:
        raise ValueError("Image not read correctly")
    img_arr = cv2.resize(img_arr, (224, 224))
    img_arr = img_arr / 255.0
    img_arr = img_arr.reshape(1, 224, 224, 3)
    return img_arr

def store_prediction(cursor, user_id, disease_name, description, possiblesteps, supplement_name, current_date):
    cursor.execute(
        'INSERT INTO Historique (iduser, DiseaseName, Explanation, Recommendations, Supplement, date) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, disease_name, description, possiblesteps, supplement_name, current_date)
    )

def predict_disease(model, get_disease_func, endpoint):
    global COUNT
    img = request.files['image']
    if img.mimetype not in ['image/jpeg', 'image/png']:
        return render_template('Error.html', message="Unsupported image format. Please upload a JPEG or PNG image.")

    current_date = datetime.datetime.now().strftime('%Y-%m-%d')

    conn = None
    try:
        img_path = save_image(img, COUNT)
        img_arr = preprocess_image(img_path)
        predictions = model.predict(img_arr)
        
        # استخدام .any() للتأكد من أن المصفوفة غير فارغة
        if predictions.size == 0:
            raise ValueError("No prediction could be made")

        # استخدام np.argmax بشكل صحيح للحصول على التنبؤ
        prediction = np.argmax(predictions, axis=1)[0]
        COUNT += 1

        disease_info = get_disease_func(prediction)
        disease_name, color, Description, possiblesteps, SupplementName, SupplementImage = disease_info

        conn = sqlite3.connect('PlantDisease.db', timeout=10)
        cursor = conn.cursor()
        store_prediction(cursor, session['id'], disease_name, Description, possiblesteps, SupplementName, current_date)
        conn.commit()
    except Exception as e:
        return render_template('Error.html', message=str(e))
    finally:
        if conn:
            conn.close()

    return render_template('Output.html', data=(disease_name, color), img_path=img_path, Description=Description, possiblesteps=possiblesteps, SupplementName=SupplementName, SupplementImage=SupplementImage)

@app.route('/predictionpotato', methods=['POST'])
def prediction_potato():
    return predict_disease(model_potato, get_potato_disease, 'potato')

@app.route('/predictiontomato', methods=['POST'])
def prediction_tomato():
    return predict_disease(model_tomato, get_tomato_disease, 'tomato')

@app.route('/predictiongrape', methods=['POST'])
def prediction_grape():
    return predict_disease(model_grape, get_grape_disease, 'Grape')

@app.route('/predictioncotton', methods=['POST'])
def prediction_cotton():
    return predict_disease(model_cotton, get_cotton_disease, 'cotton')

@app.route('/predictioncorn', methods=['POST'])
def prediction_corn():
    return predict_disease(model_corn, get_corn_disease, 'corn')
@app.route('/predictionapple', methods=['POST'])
def prediction_apple():
    return predict_disease(model_Apple, get_apple_disease, 'Apple')

def get_potato_disease(prediction):
    if prediction == 0:
        return [
            "Potato Early Blight", 'red',
            *get_disease_info("Potato : Early Blight"),
            *get_Supplement_info("Potato___Early_blight")
        ]
    elif prediction == 1:
        return [
            "Potato Late Blight", 'red',
            *get_disease_info("Potato : Late Blight"),
            *get_Supplement_info("Potato___Late_blight")
        ]
    elif prediction == 2:
        return [
            "Potato Healthy", 'green',
            *get_disease_info("Potato : Healthy"),
            *get_Supplement_info("Potato___healthy")
        ]

def get_tomato_disease(prediction):
    if prediction == 0:
        return [
            "Bacterial Spot", 'red',
            *get_disease_info("Tomato : Bacterial Spot"),
            *get_Supplement_info("Tomato : Bacterial Spot")
        ]
    elif prediction == 1:
        return [
            "Early Blight", 'red',
            *get_disease_info("Tomato : Early Blight"),
            *get_Supplement_info("Tomato : Early Blight")
        ]
    elif prediction == 2:
        return [
            "Late Blight", 'red',
            *get_disease_info("Tomato : Late Blight"),
            *get_Supplement_info("Tomato : Late Blight")
        ]
    elif prediction == 3:
        return [
            "Leaf Mold", 'red',
            *get_disease_info("Tomato : Leaf Mold"),
            *get_Supplement_info("Tomato : Leaf Mold")

        ]
    elif prediction == 4:
        return [
        "Septoria Leaf Spot", 'red',
            *get_disease_info("Tomato : Septoria Leaf Spot"),
            *get_Supplement_info("Tomato : Septoria Leaf Spot")

        ]
    elif prediction == 5:
        return [
        "Spider Mites", 'red',
            *get_disease_info("Tomato : Spider Mites | Two-Spotted Spider Mite"),
            *get_Supplement_info("Tomato : Spider Mites | Two-Spotted Spider Mite")

        ]
    elif prediction == 6:
        return [
        "Target Spot", 'red',
            *get_disease_info("Tomato : Target Spot"),
            *get_Supplement_info("Tomato : Target Spot")

        ]
    elif prediction == 7:
         return [
        "Yellow Leaf Curl Virus", 'red',
            *get_disease_info("Tomato : Yellow Leaf Curl Virus"),
            *get_Supplement_info("Tomato : Yellow Leaf Curl Virus")

        ]
    elif prediction == 8:
         return [
        "Tomato Mosaic Virus", 'red',
            *get_disease_info("Tomato : Mosaic Virus"),
            *get_Supplement_info("Tomato : Mosaic Virus")

        ]
    else:
        return [
            "Tomato Healthy", 'green',
            *get_disease_info("Tomato : Healthy"),
            *get_Supplement_info("Tomato : Healthy")
        ]
def get_grape_disease(prediction):
    if prediction == 0:
        return[
            "Grape Black rot","red",
            *get_disease_info("Grape : Black Rot"),
            *get_Supplement_info("Grape : Black Rot")

        ]
    elif prediction ==1:
        return[
            "Grape Esca(Black_Measles)","red",
            *get_disease_info("Grape : Esca | Black Measles"),
            *get_Supplement_info("Grape : Esca | Black Measles")


        ]
    elif prediction ==2:
        return[
        "Grape Leaf blight (Isariopsis Leaf Spot)","red",
            *get_disease_info("Grape : Leaf Blight | Isariopsis Leaf Spot"),
            *get_Supplement_info("Grape : Leaf Blight | Isariopsis Leaf Spot")

        ]
    else:
        return[
            "Grape Healthy", 'green',
            *get_disease_info("Grape : Healthy"),
            *get_Supplement_info("Grape : Healthy")
        ]
def get_corn_disease(prediction):
    if prediction == 0:
        return[
            "Blight", 'red',
            *get_disease_info("Corn : Northern Leaf Blight"),
            *get_Supplement_info("Corn : Northern Leaf Blight")
        ]
    elif prediction == 1:
        return[
            "Common Rust", 'red',
            *get_disease_info("Corn : Common Rust"),
            *get_Supplement_info("Corn : Common Rust")

        ]
    elif prediction ==2:
        return[
            "Corn : Cercospora Leaf Spot | Gray Leaf Spot","red"
            *get_disease_info("Corn___Cercospora_leaf_spot Gray_leaf_spot"),
            *get_Supplement_info("Corn___Cercospora_leaf_spot Gray_leaf_spot")

        ]
    else:
        return [
            "Corn Healthy", 'green',
            *get_disease_info("Corn : Healthy"),
            *get_Supplement_info("Corn : Healthy")
        ]

def get_cotton_disease(prediction):
    if prediction ==0:
        return[
            "diseased cotton leaf","red",

        ]
    elif prediction ==1:
        return[
            "diseased cotton plant", "red",

        ]
    elif prediction ==2:
        return[
            "fresh cotton leaf","green",

        ]
    else : 
         return[
            "fresh cotton plant","green",
        ]
    
def get_apple_disease(prediction):
    if prediction == 0:
        return[
            "Apple Scab","red",
            *get_disease_info("Apple : Scab"),
            *get_Supplement_info("Apple : Scab")

        ]
    elif prediction ==1:
        return[
            "Apple Black rot","red",
            *get_disease_info("Apple : Black rot"),
            *get_Supplement_info("Apple : Black rot")


        ]
    elif prediction == 2:
        return[
        "Apple Cedar rust","red",
            *get_disease_info("Apple : Cedar rust"),
            *get_Supplement_info("Apple : Cedar rust")

        ]
    else:
        return[
            "Apple Healthy", 'green',
            *get_disease_info("Apple : Healthy"),
            *get_Supplement_info("Apple : Healthy")
        ]
    
def get_visitor_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']

@app.route('/')
def index():
    visitor_ip = get_visitor_ip()
    user_agent = request.headers.get('User-Agent')
    
    # Log visitor info (in this example, print to console or save to a file)
    log_visitor_info(visitor_ip, user_agent)
    
    return f"Welcome! Your IP: {visitor_ip}, Your User-Agent: {user_agent}"

# Log visitor info to console (can be modified to log to a file or database)
def log_visitor_info(ip, user_agent):
    print(f"Visitor IP: {ip}, User-Agent: {user_agent}")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

