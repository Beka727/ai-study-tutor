import firebase_admin
from firebase_admin import credentials, firestore, storage

# Initialize Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'YOUR_PROJECT_ID.appspot.com'  # የ Firebase Storage Bucket ስምህን እዚህ ተካ
})

# Firestore DB instance
db = firestore.client()
