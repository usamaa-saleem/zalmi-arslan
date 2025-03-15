import streamlit as st
import io
import json
import requests
from PIL import Image
import time
from firebase_utils import upload_image

# API Configuration
API_ENDPOINT = "https://api.runpod.ai/v2/f4hs5vki2ff7jm/runsync"
API_KEY = "rpa_AJZLDU6PQBNW7H6AWJ3EHRXL8RKNEVAT10FSTE8U7ts2rx"

# Set page configuration
st.set_page_config(
    page_title="Zalmi Face Swap",
    page_icon="📸",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for better appearance
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: bold;
    }
    .upload-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .result-img {
        border: 2px solid #f0f0f0;
        border-radius: 10px;
        padding: 10px;
        margin-top: 20px;
    }
    .success-message {
        padding: 10px;
        background-color: #d4edda;
        color: #155724;
        border-radius: 5px;
        margin: 10px 0;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("Zalmi Face Swap")
st.write("Upload an image or take a photo, select gender and age, then submit.")

# Function to process and format the submission
def process_submission(image_data, gender, age_range):
    # Convert age range to format expected by API
    age_mapping = {
        "Under 20": "under-20",
        "20 to 35": "20-to-35",
        "35 to 45": "35-to-45",
        "45+": "45-plus"
    }
    
    formatted_age = age_mapping.get(age_range, age_range)
    
    # Upload image to Firebase and get URL
    try:
        image_url = upload_image(image_data)
        st.success("Image uploaded successfully!")
        
        # Create API request body
        request_body = {
            "input": {
                "image": image_url,
                "gender": gender.lower(),
                "age": formatted_age
            }
        }
        
        # Send request to API
        with st.spinner("Processing your request... This may take a moment."):
            response = requests.post(
                API_ENDPOINT,
                json=request_body,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            
            # Check if request was successful
            if response.status_code == 200:
                response_data = response.json()
                
                # Check if response contains the expected result
                if response_data.get("status") == "COMPLETED" and "output" in response_data and "result" in response_data["output"]:
                    result_image_url = response_data["output"]["result"][0]
                    
                    # Display the result image
                    st.subheader("Generated Result:")
                    st.markdown(f'<div class="result-img">', unsafe_allow_html=True)
                    st.image(result_image_url, caption="Generated Image", use_column_width=True)
                    st.markdown(f'</div>', unsafe_allow_html=True)
                    
                    # Provide a link to download the image
                    st.markdown(f"[Download Generated Image]({result_image_url})", unsafe_allow_html=False)
                else:
                    st.error("The API response did not contain a valid result.")
            else:
                st.error(f"API request failed with status code {response.status_code}")
                st.error(f"Error message: {response.text}")
        
        return request_body
        
    except Exception as e:
        st.error(f"Error during processing: {str(e)}")
        return None

# Create tabs for different input methods
tab1, tab2 = st.tabs(["Upload Image", "Capture from Webcam"])

# Image storage variable
image_data = None
image_pil = None

# Tab 1: Upload Image
with tab1:
    st.markdown('<p class="upload-header">Upload an Image</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Read the file and convert to bytes
        image_bytes = uploaded_file.getvalue()
        image_pil = Image.open(io.BytesIO(image_bytes))
        
        # Display the uploaded image
        st.image(image_pil, caption="Uploaded Image", use_column_width=True)
        
        # Store image data for later use
        img_byte_arr = io.BytesIO()
        image_pil.save(img_byte_arr, format=image_pil.format if image_pil.format else 'JPEG')
        image_data = img_byte_arr.getvalue()

# Tab 2: Capture from Webcam
with tab2:
    st.markdown('<p class="upload-header">Capture from Webcam</p>', unsafe_allow_html=True)
    
    # Use Streamlit's native camera input for smooth webcam functionality
    camera_image = st.camera_input("Take a picture", key="camera")
    
    if camera_image is not None:
        # Display success message
        st.markdown('<div class="success-message">Image captured successfully!</div>', unsafe_allow_html=True)
        
        # Process the captured image
        image_bytes = camera_image.getvalue()
        image_pil = Image.open(io.BytesIO(image_bytes))
        
        # Store image data for later use
        img_byte_arr = io.BytesIO()
        image_pil.save(img_byte_arr, format='JPEG')
        image_data = img_byte_arr.getvalue()

# Sidebar form for user information
st.sidebar.title("Person Information")

# Create a form
with st.sidebar.form(key="user_info_form"):
    # Gender selection
    gender = st.selectbox("Gender", options=["Male", "Female"])
    
    # Age range selection
    age_range = st.selectbox("Age Range", options=["Under 20", "20 to 35", "35 to 45", "45+"])
    
    # Submit button
    submit_button = st.form_submit_button(label="Submit")

# Process form submission
if submit_button:
    if image_data is None:
        st.error("Please upload or capture an image first")
    else:
        # Process the submission
        result = process_submission(image_data, gender, age_range)
        
        if result:
            st.sidebar.success("Information submitted successfully!")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit and Firebase") 