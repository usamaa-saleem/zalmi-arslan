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
    layout="wide",
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
        padding: 1rem;
        max-width: 1200px !important;
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
        margin-top: 10px;
        margin-bottom: 10px;
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
        padding: 20px;
        margin-top: 20px;
        margin-bottom: 30px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        display: flex;
        flex-direction: column;
        width: 100%;
    }
    .sponsor-title {
        text-align: center;
        font-size: 1.5rem;
        color: #333;
        margin-bottom: 15px;
        font-weight: 600;
    }
    /* Style for branding columns */
    .branding-col img {
        margin-bottom: 15px;
        margin-top: 15px;
        display: block;
        min-height: 150px;
        object-fit: contain;
    }
    /* Make the center column stand out */
    .center-result h3 {
        text-align: center;
        margin-bottom: 0.8rem;
        font-size: 1.3rem;
    }
    /* Adjust column gap and width */
    .row-widget.stHorizontal {
        gap: 15px !important;
        width: 100% !important;
        max-width: 100% !important;
    }
    /* Ensure the container uses full width */
    .block-container {
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    /* Make all columns stretch to use available space */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 !important;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("Zalmi Avatar")
st.write("Take a photo, select gender and age, then submit.")

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

# Function to safely load image from file
def load_image_safely(image_path):
    """
    Load an image file safely, with error handling.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        PIL.Image object or None if the image could not be loaded
    """
    try:
        return Image.open(image_path)
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

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
                        
                        # Add branding images side-by-side with the result
                        st.markdown('<div class="branding-section">', unsafe_allow_html=True)
                        st.markdown('<p class="sponsor-title">Zalmi Avatar - Sponsored by</p>', unsafe_allow_html=True)
                        
                        # Create a three-column layout
                        left_brand_col, center_result_col, right_brand_col = st.columns([1.5, 2, 1.5])
                        
                        # Left column - Main branding image
                        with left_brand_col:
                            try:
                                st.markdown('<div class="branding-col">', unsafe_allow_html=True)
                                st.image("Main zalmi main cheezious.png", use_column_width=True)
                                st.markdown('</div>', unsafe_allow_html=True)
                            except Exception as e:
                                st.error(f"Error displaying main branding image")
                                print(f"Error with main branding image: {e}")
                        
                        # Center column - Generated result
                        with center_result_col:
                            st.markdown('<div class="center-result">', unsafe_allow_html=True)
                            st.subheader("Generated Result:")
                            st.markdown(f'<div class="result-img">', unsafe_allow_html=True)
                            st.image(result_image_url, caption="Generated Image", use_column_width=True)
                            st.markdown(f'</div>', unsafe_allow_html=True)
                            
                            # Provide a link to download the image
                            st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
                            st.markdown(f"[Download Generated Image]({result_image_url})", unsafe_allow_html=False)
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Right column - Two stacked logos
                        with right_brand_col:
                            st.markdown('<div class="branding-col">', unsafe_allow_html=True)
                            try:
                                st.image("zalmi-logo-black.png", use_column_width=True)
                            except Exception as e:
                                st.error(f"Error displaying zalmi logo")
                                print(f"Error with zalmi logo: {e}")
                                
                            try:
                                st.image("cheezious_logo[1].png", use_column_width=True)
                            except Exception as e:
                                st.error(f"Error displaying cheezious logo")
                                print(f"Error with cheezious logo: {e}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
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
st.markdown('<p class="upload-header">Capture from Webcam</p>', unsafe_allow_html=True)

# Use Streamlit's native camera input for smooth webcam functionality
camera_image = st.camera_input("Take a picture", key="camera")

if camera_image is not None:
    # Display success message
    st.markdown('<div class="success-message">Image captured successfully!</div>', unsafe_allow_html=True)
    
    # Process the captured image
    image_bytes = camera_image.getvalue()
    image_pil = Image.open(io.BytesIO(image_bytes))
    
    # Display the captured image
    st.image(image_pil, caption="Captured Image", use_column_width=True)
    
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
        st.error("Please capture an image first")
    else:
        # Process the submission
        result = process_submission(image_data, gender, age_range)
        
        if result:
            st.sidebar.success("Information submitted successfully!")

# Footer
st.markdown("---")
