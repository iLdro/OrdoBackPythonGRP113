from flask import Flask, render_template
import cv2
import numpy as np
import firebase_admin
from firebase_admin import credentials, storage
from firebase_admin import firestore
import time 
from random import randint
from pymongo import MongoClient
from confing import MONGO_URI

app = Flask(__name__)

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["test"]
print(mongo_db.list_collection_names()) 



medecin = {
    "id": "6489d4dce1e3c3b567b62240",
    "nom_medecin": "Dr Philippe Langloys",
    "intitulé": "Medecin generaliste",
    "numero_rue": "10",
    "nom_rue": "Pl. Robert Belvaux",
    "code_postal": "94170",
    "ville": "Le Perreux-sur-Marne",
    "telephone": "+33 143244199",
    "RPPS": "78563249587"
}

client = {
    "id": "6489ed374c9d35917a0760f5",
    "nom_client": "Gaillard",
    "prenom_client": "Etienne",
    "date": "13/07/2001"
}

medicaments = [
    {
        "nom_medoc": "Doliprane",
        "dosage": "1000 mg",
        "fréquence": "3/jour",
        "durée": "1 semaine"
    },
    {
        "nom_medoc": "Ibuprofene",
        "dosage": "100 mg",
        "fréquence": "1/jour",
        "durée": "5 jours"
    },
    {
        "nom_medoc": "Smecta",
        "dosage": "500 mg",
        "fréquence": "2/jour",
        "durée": "4 ans"
    },
    {
        "nom_medoc": "Spasfon",
        "dosage": "100 mg",
        "fréquence": "4/jour",
        "durée": "pour toujours"
    },
    {
        "nom_medoc": "Ketoprofene",
        "dosage": "200 mg",
        "fréquence": "1/8h",
        "durée": "6 ms"
    }
]

def generate_ordonnance():
    file_name = str(int(time.time()) % randint(1, 200))
    for _ in range(5):  # Generate 5 frames
        ordonnance = np.zeros((1000, 708, 3), np.uint8)
        ordonnance.fill(255)

        cv2.putText(ordonnance, medecin["nom_medecin"], (10, 50), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, medecin["intitulé"], (10, 70), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, medecin["numero_rue"], (10, 90), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, medecin["nom_rue"], (25, 90), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, medecin["code_postal"], (10, 110), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, medecin["ville"], (60, 110), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, medecin["telephone"], (10, 130), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, medecin["RPPS"], (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)

        NomPrenom = (client["nom_client"], client["prenom_client"])
        Id_client = " ".join(NomPrenom)
        cv2.putText(ordonnance, Id_client, (355, 225), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        cv2.putText(ordonnance, client["date"], (355, 245), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)

        coord = (75, 340)
        for medicament in medicaments:
            nom = medicament["nom_medoc"]
            dose = medicament["dosage"]
            freq = medicament["fréquence"]
            temps = medicament["durée"]

            cv2.putText(ordonnance, nom, coord, cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
            infos_medocs = (dose, freq, temps)
            final_medoc = " ".join(infos_medocs)
            coord = (coord[0], coord[1] + 30)
            cv2.putText(ordonnance, final_medoc, (coord[0] + 10, coord[1]), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
            coord = (coord[0], coord[1] + 10)
            cv2.line(ordonnance, coord, (coord[0] + 400, coord[1]), (0, 0, 0), 1)
            coord = (coord[0], coord[1] + 30)

        cv2.putText(ordonnance, medecin["nom_medecin"], (350, 900), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)

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
    filename = "ordonnance.jpg"

    # Create a new blob in the bucket and upload the image data
    blob = bucket.blob(filename)
    blob.upload_from_string(image_data, content_type='image/jpeg')

    # Generate a public URL for the uploaded image
    url = blob.public_url

    return url


@app.route('/ordonnance')
def ordonnance():
    mongo_collection = mongo_db["ordonnances"]
    image_data = generate_ordonnance()
    image_bytes = next(image_data)  # Get the first generated frame as bytes
    image_data.close()  # Close the generator to release resources

    image_url = save_image_to_firebase(image_bytes)

    ordonnance_data = {
        'image_url': image_url,
        'medecin_id': medecin["id"],
        'user_id': client["id"],
        'medicaments': medicaments
    }

    result = mongo_collection.insert_one(ordonnance_data)

    print('Created ordonnance {0}'.format(result.inserted_id))

if __name__ == '__main__':
    app.run(host='localhost', port=5173)