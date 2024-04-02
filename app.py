import os
import cv2
import numpy as np
import face_recognition
import json
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# Load registered data from file
def load_registered_data():
    try:
        with open('registered_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save registered data to file
def save_registered_data(data):
    with open('registered_data.json', 'w') as f:
        json.dump(data, f)

registered_data = load_registered_data()

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/newuser")
def newuser():
    return render_template("newuser.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    photo = request.files['photo']
    photo_image = face_recognition.load_image_file(photo)
    photo_image = cv2.cvtColor(photo_image, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(photo_image)
    if len(face_locations) == 0:
        response = {"success": False, "message": "No face detected in the provided photo"}
        return jsonify(response), 400
    face_encodings = face_recognition.face_encodings(photo_image, face_locations)
    uploads_folder = os.path.join(os.getcwd(), "static", "uploads")
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)
    photo_filename = os.path.join(uploads_folder, f'{name}.jpg')
    cv2.imwrite(photo_filename, cv2.cvtColor(photo_image, cv2.COLOR_RGB2BGR))
    registered_data[name] = {
        "photo": f"{name}.jpg",
        "face_encodings": [encoding.tolist() for encoding in face_encodings]
    }
    save_registered_data(registered_data)
    response = {"success": True, "name": name}
    return jsonify(response)

@app.route("/login", methods=["POST"])
def login():
    try:
        if 'photo' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        photo = request.files['photo']
        uploads_folder = os.path.join(os.getcwd(), "static", "uploads")
        if not os.path.exists(uploads_folder):
            os.makedirs(uploads_folder)
        login_filename = os.path.join(uploads_folder, "login_face.jpg")
        photo.save(login_filename)
        login_image = face_recognition.load_image_file(login_filename)
        login_image = cv2.cvtColor(login_image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(login_image)
        if len(face_locations) == 0:
            response = {"success": False, "message": "No face detected in the provided photo"}
            return jsonify(response), 400
        login_face_encodings = face_recognition.face_encodings(login_image, face_locations)
        registered_data = load_registered_data()
        for name, data in registered_data.items():
            registered_photo = os.path.join(uploads_folder, data["photo"])
            registered_face_encodings = [np.array(encoding) for encoding in data["face_encodings"]]
            matches = face_recognition.compare_faces(registered_face_encodings, login_face_encodings[0])
            if any(matches):
                response = {"success": True, "name": name}
                return jsonify(response)
        return jsonify({"success": False, "message": "Face not recognized as a registered user"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/success")
def success():
    user_name = request.args.get("user_name")
    return render_template("success.html", user_name=user_name)

if __name__ == "__main__":
    app.run(debug=True)
