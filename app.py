import streamlit as st
import io
import json
import os
import requests
import base64
from PIL import Image
import time

# API Configuration - try to get from streamlit secrets first, then environment variables, then default
try:
    API_ENDPOINT = st.secrets["API_ENDPOINT"]
except:
    API_ENDPOINT = os.environ.get("API_ENDPOINT", "https://api.runpod.ai/v2/f4hs5vki2ff7jm/runsync")

try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = os.environ.get("API_KEY", "rpa_AJZLDU6PQBNW7H6AWJ3EHRXL8RKNEVAT10FSTE8U7ts2rx")

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

# Debug section for administrators
if st.sidebar.checkbox("Show Debug Info", False):
    st.sidebar.subheader("API Configuration Debug")
    
    # Check API keys
    try:
        api_endpoint = st.secrets["API_ENDPOINT"]
        st.sidebar.success(f"API_ENDPOINT found in secrets")
    except:
        st.sidebar.warning("API_ENDPOINT not found in secrets, using fallback")
        
    try:
        api_key = st.secrets["API_KEY"]
        st.sidebar.success(f"API_KEY found in secrets")
    except:
        st.sidebar.warning("API_KEY not found in secrets, using fallback")
    
    # Add information about base64 encoding
    st.sidebar.subheader("Image Processing")
    st.sidebar.info("Using base64 encoding for images")
    
    # Add max request size information
    st.sidebar.info("Note: Large images will result in large request payloads")
    st.sidebar.warning("API may have limits on request size")
    
    # Add sample code for debugging
    if st.sidebar.checkbox("Show sample code", False):
        st.sidebar.code("""
# Python code to convert an image to base64
import base64
with open('image.jpg', 'rb') as img_file:
    base64_string = base64.b64encode(img_file.read()).decode('utf-8')
        """)

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
        
        # Display base64 string size info
        size_kb = len(base64_image) / 1024
        if size_kb > 1000:
            st.info(f"Base64 image size: {size_kb/1024:.2f} MB")
        else:
            st.info(f"Base64 image size: {size_kb:.2f} KB")
            
        st.success("Image encoded successfully!")
        
        # Create API request body with base64 image
        request_body = {
            "input": {
                "image": base64_image,
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
        
        # Store image data for later use (original, will be optimized during processing)
        image_data = image_bytes

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
        
        # Store image data for later use (original, will be optimized during processing)
        image_data = image_bytes

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
st.markdown("Built with Streamlit • Direct API Integration with Base64 Image Encoding") 