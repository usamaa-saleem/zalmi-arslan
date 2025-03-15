# Zalmi Face Swap

A Streamlit application that allows users to upload an image or take a webcam photo and apply face-swapping AI technology to generate a new image based on the selected gender and age range.

## Features

- Image upload functionality
- Webcam capture integration
- Direct base64 image encoding
- API integration with RunPod AI service
- Image optimization for efficient processing
- Gender and age range selection
- Face-swapping image generation

## Project Structure

- `app.py`: Main application code
- `requirements.txt`: Dependencies

## Local Setup

1. Clone the repository:
```bash
git clone https://github.com/usamaa-saleem/zalmi-arslan.git
cd zalmi-arslan
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run app.py
```

## Deployment

### Deploy to Streamlit Cloud

1. Create a Streamlit account at https://streamlit.io/cloud
2. Connect your GitHub repository
3. Create a new app by selecting the repository and branch
4. Add your API credentials as secrets in the Streamlit Cloud dashboard
5. Deploy and access your application

### Environment Variables

For production deployment, you should set the following environment variables:
- `API_ENDPOINT`: Your RunPod AI API endpoint
- `API_KEY`: Your RunPod AI API key

## Security Notes

- The API key should not be hardcoded in the source code for production use
- The application includes image optimization to handle large images efficiently

## License

This project is licensed under the MIT License - see the LICENSE file for details. 