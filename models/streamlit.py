import streamlit as st
import tempfile
from PIL import Image

# Import our modules (ensure these files are in the same directory)
import multimodal
import alternatives
import diy

st.set_page_config(page_title="Sustaino", layout="centered")

# Custom CSS for a modern, clean look
st.markdown(
    """
    <style>
    body { background-color: #f4f4f9; }
    .title { font-size: 3rem; font-weight: bold; text-align: center; color: #2c3e50; margin-bottom: 0; }
    .subtitle { font-size: 1.5rem; text-align: center; color: #34495e; margin-top: 0; }
    .result { background-color: #ffffff; padding: 20px; border-radius: 10px; 
              box-shadow: 0px 2px 10px rgba(0,0,0,0.1); margin-top: 20px; }
    .btn { background-color: #3498db; color: white; border: none; padding: 10px 20px; 
           font-size: 1rem; margin: 10px; border-radius: 5px; cursor: pointer; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">Sustaino</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your Sustainability & Health Analyzer</div>', unsafe_allow_html=True)
st.write("Upload a product photo below to analyze its sustainability and health attributes.")

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_container_width=True)
    
    # Save the uploaded file temporarily for our modules
    def save_uploaded_file(uploaded_file):
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tfile.write(uploaded_file.getbuffer())
        return tfile.name

    file_path = save_uploaded_file(uploaded_file)
    
    # Analyze Product button
    if st.button("Analyze Product", key="analyze"):
        with st.spinner("Analyzing the product..."):
            analysis_text = multimodal.generate_product_analysis(file_path)
            st.session_state.analysis = analysis_text  # store analysis for later use
            # Replace newline characters with HTML line breaks for display
            st.markdown("<div class='result'>" + analysis_text.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)
    
    # Alternatives and DIY options (appear only if analysis is available)
    if "analysis" in st.session_state:
        if st.button("Get Alternatives", key="alt"):
            with st.spinner("Generating alternative suggestions..."):
                alt_text = alternatives.generate_alternative_suggestion(st.session_state.analysis)
                st.markdown("<div class='result'>" + alt_text.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)
                
        if st.button("DIY Options", key="diy"):
            with st.spinner("Fetching DIY ideas..."):
                diy_text = diy.generate_diy_suggestions(file_path)
                st.markdown("<div class='result'>" + diy_text.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)