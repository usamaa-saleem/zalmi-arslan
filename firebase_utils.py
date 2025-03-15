import os
import time
import uuid
import firebase_admin
from firebase_admin import credentials, storage
import json

# Path to your Firebase credentials file
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "firebase_credentials.json")

def initialize_firebase():
    """Initialize Firebase app if not already initialized"""
    if not firebase_admin._apps:
        if os.path.exists(CREDENTIALS_PATH):
            cred = credentials.Certificate(CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {
                'storageBucket': "arslan-zalmi.firebasestorage.app"
            })
        else:
            raise FileNotFoundError("Firebase credentials file not found. Please make sure firebase_credentials.json exists.")

def upload_image(image_data, image_format='jpeg'):
    """
    Upload image to Firebase Storage and return public URL
    
    Args:
        image_data: The image data as bytes
        image_format: The format of the image (jpeg, png, etc.)
        
    Returns:
        The public URL of the uploaded image
    """
    # Initialize Firebase if not already initialized
    initialize_firebase()
    
    # Create a unique filename
    filename = f"{uuid.uuid4()}.{image_format}"
    
    # Get bucket reference
    bucket = storage.bucket()
    
    # Create a blob and upload the image
    blob = bucket.blob(f"streamlit_uploads/{filename}")
    blob.upload_from_string(image_data, content_type=f"image/{image_format}")
    
    # Make the blob publicly accessible
    blob.make_public()
    
    # Return the public URL
    return blob.public_url 