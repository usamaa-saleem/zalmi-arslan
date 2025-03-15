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
    page_title="Zalmi Face Swap",
    page_icon="📸",
    layout="centered",
    initial_sidebar_state="expanded"
)

# API Configuration - try to get from streamlit secrets first, then environment variables, then default
try:
    API_ENDPOINT = st.secrets["API_ENDPOINT"]
except:
    # Updated API endpoint based on error messages
    API_ENDPOINT = os.environ.get("API_ENDPOINT", "https://api.runpod.ai/v2/bogdfcwppmeh9x/runsync")

try:
    API_KEY = st.secrets["API_KEY"]
except:
    # Use more recent API key format if available
    API_KEY = os.environ.get("API_KEY", "rpa_AJZLDU6PQBNW7H6AWJ3EHRXL8RKNEVAT10FSTE8U7ts2rx")

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
    .help-box {
        padding: 10px 15px;
        background-color: #e9ecef;
        border-left: 4px solid #5c636a;
        border-radius: 4px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("Zalmi Face Swap")
st.write("Upload an image or take a photo, select gender and age, then submit.")

# Help box for API configuration
with st.expander("⚙️ API Configuration Help", expanded=False):
    st.markdown("""
    <div class="help-box">
    <strong>How to resolve API issues:</strong><br>
    If you're receiving 401 Unauthorized errors, check your API configuration:
    <ol>
        <li>Make sure your API key is correct and active</li>
        <li>Try both authorization formats in the Debug panel (Bearer Token vs API Key Only)</li>
        <li>Verify the API endpoint URL</li>
        <li>Some APIs don't accept base64-encoded images directly - try the URL option</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <strong>Current API Endpoint:</strong> 
    <pre style="padding:5px; background-color:#f8f9fa; border-radius:3px; font-size:0.8em;">"""
    + API_ENDPOINT + """</pre>
    """, unsafe_allow_html=True)

# Debug section for administrators
if st.sidebar.checkbox("Show Debug Info", False):
    st.sidebar.subheader("API Configuration Debug")
    
    # Check API keys
    try:
        api_endpoint = st.secrets["API_ENDPOINT"]
        st.sidebar.success(f"API_ENDPOINT found in secrets")
        st.sidebar.text(f"Endpoint: {api_endpoint[:20]}...")
    except:
        default_endpoint = os.environ.get("API_ENDPOINT", "https://api.runpod.ai/v2/f4hs5vki2ff7jm/runsync")
        st.sidebar.warning("API_ENDPOINT not found in secrets, using fallback")
        st.sidebar.text(f"Fallback endpoint: {default_endpoint[:20]}...")
        
    try:
        api_key = st.secrets["API_KEY"]
        st.sidebar.success(f"API_KEY found in secrets")
        st.sidebar.text(f"Key starts with: {api_key[:5]}...")
    except:
        default_key = os.environ.get("API_KEY", "rpa_AJZLDU6PQBNW7H6AWJ3EHRXL8RKNEVAT10FSTE8U7ts2rx")
        st.sidebar.warning("API_KEY not found in secrets, using fallback")
        st.sidebar.text(f"Fallback key starts with: {default_key[:5]}...")
        
    # Show API test section
    st.sidebar.subheader("API Test Options")
    auth_format = st.sidebar.radio("Authorization Format", ["Bearer Token", "API Key Only"])
    image_format = st.sidebar.radio("Image Format", ["Base64 Encoded", "URL (Placeholder)"])
    body_format = st.sidebar.radio("Request Body Format", [
        "Standard: {input:{image, gender, age}}", 
        "Flat: {image, gender, age}",
        "Custom: {data:{image}, parameters:{gender, age}}"
    ])
    
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
        
        # Get the image value (either base64 or URL)
        if st.sidebar.checkbox("Show Debug Info", False) and st.sidebar.radio("Image Format", ["Base64 Encoded", "URL (Placeholder)"]) == "URL (Placeholder)":
            # Use a placeholder URL instead of base64
            image_value = "https://example.com/placeholder.jpg"
            st.info("Using URL placeholder instead of base64 image")
        else:
            # Use base64 image
            image_value = base64_image
        
        # Create request body based on selected format
        if st.sidebar.checkbox("Show Debug Info", False):
            body_format = st.sidebar.radio("Request Body Format", [
                "Standard: {input:{image, gender, age}}", 
                "Flat: {image, gender, age}",
                "Custom: {data:{image}, parameters:{gender, age}}"
            ])
            
            if body_format == "Flat: {image, gender, age}":
                request_body = {
                    "image": image_value,
                    "gender": gender.lower(),
                    "age": formatted_age
                }
            elif body_format == "Custom: {data:{image}, parameters:{gender, age}}":
                request_body = {
                    "data": {
                        "image": image_value
                    },
                    "parameters": {
                        "gender": gender.lower(),
                        "age": formatted_age
                    }
                }
            else:  # Standard
                request_body = {
                    "input": {
                        "image": image_value,
                        "gender": gender.lower(),
                        "age": formatted_age
                    }
                }
        else:
            # Use standard format
            request_body = {
                "input": {
                    "image": image_value,
                    "gender": gender.lower(),
                    "age": formatted_age
                }
            }
        
        # Set up authorization header based on settings
        if st.sidebar.checkbox("Show Debug Info", False) and st.sidebar.radio("Authorization Format", ["Bearer Token", "API Key Only"]) == "API Key Only":
            auth_header = API_KEY
            st.sidebar.info("Using API Key directly without Bearer prefix")
        else:
            auth_header = f"Bearer {API_KEY}"
        
        # Debug info about the request
        with st.expander("Request Details", expanded=False):
            st.write("**API Endpoint:**")
            st.code(API_ENDPOINT)
            st.write("**Authorization Header Format:**")
            st.code(f"Authorization: {auth_header[:10]}...")
            st.write("**Request Body Structure:**")
            truncated_payload = {
                "input": {
                    "image": f"{image_value[:20]}... (truncated)",
                    "gender": gender.lower(),
                    "age": formatted_age
                }
            }
            st.json(truncated_payload)
            
        # Send request to API
        with st.spinner("Processing your request... This may take a moment."):
            try:
                response = requests.post(
                    API_ENDPOINT,
                    json=request_body,
                    headers={
                        "Authorization": auth_header,
                        "Content-Type": "application/json"
                    },
                    timeout=60  # Add a 60-second timeout
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
                    
                    # Show detailed error information
                    with st.expander("Error Details", expanded=True):
                        st.write("**Response Headers:**")
                        st.json(dict(response.headers))
                        
                        st.write("**Error Message:**")
                        try:
                            error_json = response.json()
                            st.json(error_json)
                        except:
                            st.code(response.text)
                        
                        # Provide common error explanations
                        if response.status_code == 401:
                            st.warning("**401 Unauthorized**: This usually means your API key is invalid or incorrectly formatted.")
                            st.info("Things to check: \n1. Make sure your API key is correct\n2. Check if the authorization format should be 'Bearer TOKEN' or just 'TOKEN'\n3. Verify you're using the correct API endpoint")
                        elif response.status_code == 400:
                            st.warning("**400 Bad Request**: The API didn't understand your request format.")
                            st.info("The API might not accept base64 encoded images directly. You may need to revert to URL-based images.")
                        elif response.status_code == 413:
                            st.warning("**413 Payload Too Large**: Your base64 image is too large.")
                            st.info("Try reducing the image size or quality further.")
                            
            except requests.exceptions.RequestException as e:
                st.error(f"Request error: {str(e)}")
        
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
