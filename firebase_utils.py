import os
import time
import uuid
import json
import firebase_admin
from firebase_admin import credentials, storage

# Path to your Firebase credentials file
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "firebase_credentials.json")

def initialize_firebase():
    """Initialize Firebase app if not already initialized"""
    if not firebase_admin._apps:
        try:
            # First, try to get credentials from environment variable (for production/deployment)
            firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS')
            if firebase_creds_json:
                cred_dict = json.loads(firebase_creds_json)
                cred = credentials.Certificate(cred_dict)
                project_id = cred_dict.get('project_id')
            # Otherwise, try to load from local file (for development)
            elif os.path.exists(CREDENTIALS_PATH):
                cred = credentials.Certificate(CREDENTIALS_PATH)
                with open(CREDENTIALS_PATH, 'r') as f:
                    project_id = json.load(f).get('project_id')
            else:
                raise FileNotFoundError("Firebase credentials not found. Please make sure firebase_credentials.json exists or set FIREBASE_CREDENTIALS environment variable.")
            
            # Initialize the app with the credentials
            firebase_admin.initialize_app(cred, {
                'storageBucket': f"{project_id}.appspot.com"
            })
        except Exception as e:
            raise Exception(f"Error initializing Firebase: {str(e)}")

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