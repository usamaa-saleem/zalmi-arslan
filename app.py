import streamlit as st
import io
import json
import os
import requests
import base64
from PIL import Image
import time

# Set page configuration (must be the first Streamlit command)
st.set_page_config(
    page_title="Zalmi Avatar",
    page_icon="📸",
    layout="centered",
    initial_sidebar_state="expanded"
)

# API Configuration - try to get from streamlit secrets first, then environment variables, then default
try:
    API_ENDPOINT = st.secrets["API_ENDPOINT"]
    # Log for debugging
    print(f"Using API_ENDPOINT from secrets: {API_ENDPOINT[:20]}...")
except:
    # Updated API endpoint based on error messages
    API_ENDPOINT = os.environ.get("API_ENDPOINT", "https://api.runpod.ai/v2/bogdfcwppmeh9x/runsync")
    print(f"Using fallback API_ENDPOINT: {API_ENDPOINT[:20]}...")

try:
    API_KEY = st.secrets["API_KEY"]
    # Log for debugging
    print(f"Using API_KEY from secrets: {API_KEY[:5]}...")
except:
    # Use more recent API key format if available
    API_KEY = os.environ.get("API_KEY", "rpa_AJZLDU6PQBNW7H6AWJ3EHRXL8RKNEVAT10FSTE8U7ts2rx")
    print(f"Using fallback API_KEY: {API_KEY[:5]}...")

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
    .branding-section {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 30px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .branding-title {
        text-align: center;
        font-size: 1.3rem;
        color: #333;
        margin-bottom: 15px;
        font-weight: 600;
    }
    .branding-image {
        margin: 0 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 80px;  /* Fixed height for all image containers */
    }
    .branding-image img {
        max-height: 80px !important;  /* Force same max height */
        width: auto !important;       /* Maintain aspect ratio */
        object-fit: contain;
    }
    /* Override Streamlit's default image sizing */
    [data-testid="stImage"] {
        width: auto !important;
        max-width: 200px !important;
    }
</style>
""", unsafe_allow_html=True)

# Add branding section at the top
# st.markdown('<div class="branding-section">', unsafe_allow_html=True)
# Create three columns for branding
col1, col2, col3 = st.columns(3)

# First logo
with col1:
    try:
        st.markdown('<div class="branding-image">', unsafe_allow_html=True)
        st.image("Main zalmi main cheezious.png", use_column_width=False)
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying main branding image")
        print(f"Error with main branding image: {e}")

# Second logo
with col2:
    try:
        st.markdown('<div class="branding-image">', unsafe_allow_html=True)
        st.image("zalmi-logo-black.png", use_column_width=False, width=150)
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying zalmi logo")
        print(f"Error with zalmi logo: {e}")

# Third logo
with col3:
    try:
        st.markdown('<div class="branding-image">', unsafe_allow_html=True)
        st.image("cheezious_logo[1].png", use_column_width=False)
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying cheezious logo")
        print(f"Error with cheezious logo: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# Title and description
st.title("Zalmi Avatar")
st.write("Take a photo, select gender and age, then submit.")

# Add tabs for webcam and upload options
webcam_tab, upload_tab = st.tabs(["Webcam Capture", "Upload Image"])

# Function to resize image if needed (to reduce base64 string size)
def resize_image_if_needed(img, max_size=(800, 800), quality=85):
    """
    Resize image if it exceeds max_size and convert to JPEG with given quality.
    This helps reduce the base64 string size which improves API request performance.
    
    Args:
        img: PIL Image object
        max_size: Tuple of (width, height) - image will not exceed these dimensions
        quality: JPEG quality (1-100)
        
    Returns:
        Image bytes in JPEG format
    """
    # Check if image needs resizing
    if img.width > max_size[0] or img.height > max_size[1]:
        # Calculate new size while maintaining aspect ratio
        ratio = min(max_size[0] / img.width, max_size[1] / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    
    # Convert to RGB if image is in RGBA mode (has transparency)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    # Save as JPEG with specified quality
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=quality)
    img_byte_arr.seek(0)
    
    return img_byte_arr.getvalue()

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
    
    try:
        # Optimize image size before encoding
        img = Image.open(io.BytesIO(image_data))
        optimized_image_data = resize_image_if_needed(img)
        
        # Convert image data to base64 string
        base64_image = base64.b64encode(optimized_image_data).decode('utf-8')
            
        # st.success("Image encoded successfully!")
        
        # Use base64 image
        image_value = base64_image
        
        # Create request body using standard format
        request_body = {
            "input": {
                "image": image_value,
                "gender": gender.lower(),
                "age": formatted_age
            }
        }
        
        # Set up authorization header - try with Bearer token first
        auth_header = f"Bearer {API_KEY}"
        
        # Check if we're in production (has secrets configured)
        try_without_bearer = False
        try:
            if 'API_KEY' in st.secrets:
                # We're likely in production, enable fallback option
                try_without_bearer = True
        except:
            pass
            
        # Send request to API
        with st.spinner("Processing your request... This may take a moment."):
            try:
                # First attempt with default auth header
                response = requests.post(
                    API_ENDPOINT,
                    json=request_body,
                    headers={
                        "Authorization": auth_header,
                        "Content-Type": "application/json"
                    },
                    timeout=60  # Add a 60-second timeout
                )
                
                # If unauthorized in production, try without 'Bearer' prefix
                if response.status_code == 401 and try_without_bearer and auth_header.startswith("Bearer "):
                    # Try again with API key only
                    direct_key = API_KEY
                    print(f"401 error with Bearer prefix, trying without Bearer prefix...")
                    print(f"Headers used: {{'Authorization': '[REDACTED]', 'Content-Type': 'application/json'}}")
                    print(f"Status code: {response.status_code}")
                    
                    response = requests.post(
                        API_ENDPOINT,
                        json=request_body,
                        headers={
                            "Authorization": direct_key,
                            "Content-Type": "application/json"
                        },
                        timeout=60
                    )
                    
                    # Log result of second attempt
                    print(f"Second attempt status code: {response.status_code}")
                
                # Check if request was successful
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # Check if response contains the expected result
                    if response_data.get("status") == "COMPLETED" and "output" in response_data and "result" in response_data["output"]:
                        result_image_url = response_data["output"]["result"][0]
                        
                        # Display the result image
                        st.subheader("Generated Result:")
                        # st.markdown(f'<div class="result-img">', unsafe_allow_html=True)
                        st.image(result_image_url, caption="Generated Image", use_column_width=True)
                        st.markdown(f'</div>', unsafe_allow_html=True)
                        
                        # Provide a link to download the image
                        st.markdown(
                            f"<div style='text-align: center;'><a href='{result_image_url}' style='font-size:16px; text-decoration:none;'>Download Generated Image</a></div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.error("The API response did not contain a valid result.")
                else:
                    st.error(f"API request failed with status code {response.status_code}")
                    # Log detailed error info
                    print(f"API request failed with status code {response.status_code}")
                    print(f"API endpoint: {API_ENDPOINT}")
                    print(f"Auth header type: {'Direct Key' if auth_header == API_KEY else 'Bearer Token'}")
                
            except requests.exceptions.RequestException as e:
                st.error(f"Request error: {str(e)}")
        
        return request_body
        
    except Exception as e:
        st.error(f"Error during processing: {str(e)}")
        return None

# Image storage variable
image_data = None
image_pil = None

# Webcam capture section
with webcam_tab:
    st.markdown('<p class="upload-header">Capture from Webcam</p>', unsafe_allow_html=True)

    # Use Streamlit's native camera input for smooth webcam functionality
    camera_image = st.camera_input("Take a picture", key="camera")

    if camera_image is not None:
        # Display success message
        st.markdown('<div class="success-message">Image captured successfully!</div>', unsafe_allow_html=True)
        
        # Process the captured image
        image_bytes = camera_image.getvalue()
        image_pil = Image.open(io.BytesIO(image_bytes))
        
        # Store image data for later use (original, will be optimized during processing)
        image_data = image_bytes

# Image upload section
with upload_tab:
    st.markdown('<p class="upload-header">Upload an Image</p>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Display success message
        st.markdown('<div class="success-message">Image uploaded successfully!</div>', unsafe_allow_html=True)
        
        # Process the uploaded image
        image_bytes = uploaded_file.getvalue()
        image_pil = Image.open(io.BytesIO(image_bytes))
        
        # Display the uploaded image
        st.image(image_pil, caption="Uploaded Image", use_column_width=True)
        
        # Store image data for later use (original, will be optimized during processing)
        image_data = image_bytes

# Sidebar form for user information
st.sidebar.title("Person Information")

# Gender selection outside the form so it can affect the form contents
gender = st.sidebar.selectbox("Gender", options=["Male", "Female"])

# Age range options depend on gender
if gender == "Female":
    age_options = ["Under 20", "20 to 35", "35 to 45"]
else:
    age_options = ["Under 20", "20 to 35", "35 to 45", "45+"]

# Create a form for the remaining inputs and submission
with st.sidebar.form(key="user_info_form"):
    # Age range selection using the options determined by gender
    age_range = st.selectbox("Age Range", options=age_options)
    
    # Submit button
    submit_button = st.form_submit_button(label="Submit")

# Process form submission
if submit_button:
    if image_data is None:
        st.error("Please capture an image first")
    else:
        # Process the submission
        result = process_submission(image_data, gender, age_range)
        
        if result:
            st.sidebar.success("Information submitted successfully!")

# Footer
st.markdown("---")
