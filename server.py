from flask import Flask, jsonify, render_template, request, Response
import requests
import cv2
import numpy as np
import firebase_admin
from firebase_admin import credentials, storage
from firebase_admin import firestore
import time 
from random import randint
from pymongo import MongoClient
from confing import MONGO_URI
import time
from random import randint
import json
import datetime

app = Flask(__name__)

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["test"]
print(mongo_db.list_collection_names()) 


def generate_ordonnance(medecin, client, medicaments):
    file_name = str(int(time.time()) % randint(1, 200))
    for _ in range(5):  # Generate 5 frames
        ordonnance = np.zeros((1000, 708, 3), np.uint8)
        ordonnance.fill(255)

        cv2.putText(ordonnance, medecin["name"], (10, 50), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, medecin["intitule"], (10, 70), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, medecin["numberStreet"], (10, 90), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, medecin["street"], (25, 90), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, medecin["postalCode"], (10, 110), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, medecin["city"], (60, 110), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, medecin["phoneNumber"], (10, 130), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, medecin["RPPS"], (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)

        NomPrenom = (client["name"], client["firstname"])
        Id_client = " ".join(NomPrenom)
        cv2.putText(ordonnance, Id_client, (355, 225), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, client["dateNaissance"], (355, 245), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)

        coord = (75, 340)
        for medicament in medicaments:
            nom = medicament["nom_medicament"]  # Updated parameter name
            dose = medicament["dosage"]
            freq = medicament["fréquence"]
            temps = medicament["duree"]  # Updated parameter name

            cv2.putText(ordonnance, nom, coord, cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
            infos_medocs = (dose, freq, temps)
            final_medoc = " ".join(infos_medocs)
            coord = (coord[0], coord[1] + 30)
            cv2.putText(ordonnance, final_medoc, (coord[0] + 10, coord[1]), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
            coord = (coord[0], coord[1] + 10)
            cv2.line(ordonnance, coord, (coord[0] + 400, coord[1]), (0, 0, 0), 1)
            coord = (coord[0], coord[1] + 30)

        cv2.putText(ordonnance, medecin["name"], (350, 900), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)

        ret, buffer = cv2.imencode('.jpg', ordonnance)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return file_name


# Initialize Firebase Admin SDK
cred = credentials.Certificate("odomastercamp-firebase-adminsdk-jdqqe-2be3aebde8.json")
firebase_admin.initialize_app(cred, {'storageBucket': 'odomastercamp.appspot.com'})

db = firestore.client()



# Create a Firebase Storage client
bucket = storage.bucket()


def save_image_to_firebase(image_data):
    # Specify the filename for the image
    filename = str(int(time.time())) + '.jpg'
    # Create a new blob in the bucket and upload the image data
    blob = bucket.blob(filename)
    blob.upload_from_string(image_data, content_type='image/jpeg')

    # Generate a public URL for the uploaded image
    url = blob.public_url

    return url


@app.route('/ordonnance', methods=['POST'])
def ordonnance():
    print(request)
    if request.method == 'POST': 
        request_data = request.get_json()
        medecin_id = request_data['medecin_id']
        user_id = request_data['client_id']
        medicaments = request_data['medicaments']
        
    express_url = "http://localhost:5000"
    
    try:
        response = requests.post(express_url + "/medById", json={"id": medecin_id})
        print("medecin", response.text)  # Affiche la réponse JSON reçue
        medecin = response.json()  # Convertit la réponse JSON en objet Python
        client = requests.post("http://localhost:5000/med/getUserById", json={"id": user_id}).json()
        print(medecin)
        print(client)
    except requests.exceptions.RequestException as e:
        print(str(e))
        return "erreur"

    print(request_data)
    
    
    
        
    mongo_collection = mongo_db["ordonnances"]
    image_data = generate_ordonnance(medecin, client, medicaments)
    image_bytes = next(image_data)  # Get the first generated frame as bytes
    image_data.close()  # Close the generator to release resources

    image_url = save_image_to_firebase(image_bytes)

    ordonnance_data = {
        'image_url': image_url,
        'medecin_id': medecin_id,
        'user_id': user_id,
        'medicaments': medicaments,
        'pharmacien': " ",
        'dateDeCréation': datetime.datetime.now(),
        'expired': False,
    }

    result = mongo_collection.insert_one(ordonnance_data)

    print('Created ordonnance {0}'.format(result.inserted_id))
    return jsonify(request_data)

if __name__ == '__main__':
    app.run(host='localhost', port=5173)