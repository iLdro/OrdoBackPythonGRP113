
import base64
import os
import bson
from flask import Flask, jsonify, make_response, render_template, request, Response, send_file
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
from bson.objectid import ObjectId

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

    return ordonnance 


# Initialize Firebase Admin SDK

def save_to_image_to_mongo(image_data):
    collection_doc = mongo_db["docs"]

    # Decode the Base64-encoded image data
    image_bytes = base64.b64decode(image_data)

    image_bson = bson.Binary(image_bytes)

    doc = {"image": image_bson}

    result = collection_doc.insert_one(doc)

    document_id = result.inserted_id

    return str(document_id)


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
    # Save the image temporarily
    temp_path = 'temp_ordonnance.png'
    cv2.imwrite(temp_path, image_data)

    # Serve the image using Flask's send_file function
    return send_file(temp_path, mimetype='image/png')



@app.route('/test', methods=['GET'])
def display_ordonnance():  
    request = {
  "medecin_id": "64999e9bfd677ad4f009b841",
  "client_id" : "64958e29428e5f9a03cba8ca",
  "medicaments": [
      {
          "nom_medicament": "Doliprane",
          "dosage": "500mg",
          "fréquence": "3 fois par jour",
          "duree": "5 jours"
      },
      {
          "nom_medicament": "Doliprane",
          "dosage": "500mg",
          "fréquence": "3 fois par jour",
          "duree": "5 jours"
      },
      {
          "nom_medicament": "Doliprane",
          "dosage": "500mg",
          "fréquence": "3 fois par jour",
          "duree": "5 jours"
      }]
}
    if request.method == 'GET': 
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
    
    # Generate the ordonnance image
    ordonnance_image = generate_ordonnance(medecin, client, medicaments)

    # Save the image temporarily
    temp_path = 'temp_ordonnance.png'
    cv2.imwrite(temp_path, ordonnance_image)

    # Serve the image using Flask's send_file function
    return send_file(temp_path, mimetype='image/png')


@app.route("/editOrdonnance", methods=["POST"])
def editOrdonnance():
    if request == 'POST':
        request_data = request.get_json()
        pharmacien_id = request_data['pharmacien_id']
        

        


if __name__ == '__main__':
    app.run(host='localhost', port=5173)