import streamlit as st
import time
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import torchvision.transforms as T
import numpy as np
import google.generativeai as genai

st.set_page_config(layout="wide")
@st.cache_resource
def init_gem():
  GeminiKey = 'AIzaSyCJhAtyZXOnedFy331IsoWtJaWURpYRnXg'
  genai.configure(api_key=GeminiKey)
  return genai.GenerativeModel('gemini-1.5-flash')

gemini = init_gem()

page_bg_gradient = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(-45deg, #a1c4fd, #c2e9fb, #e0f7fa, #b2ebf2, #80deea, #4dd0e1, #d4f1f4, #75e6da);
    background-size: 400% 400%;
    animation: gradient 15s ease infinite;
}

@keyframes gradient {
    0% {
        background-position: 0% 50%;
    }
    25% {
        background-position: 50% 100%;
    }
    50% {
        background-position: 100% 50%;
    }
    75% {
        background-position: 50% 0%;
    }
    100% {
        background-position: 0% 50%;
    }
}

</style>
"""
def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

st.markdown(page_bg_gradient, unsafe_allow_html=True)
st.title('*Aion.ai*')
st.subheader('Visual Search Solution', divider='gray')
if "uploader_visible" not in st.session_state:
    st.session_state["uploader_visible"] = False
if 'hidden_chat' not in st.session_state:
    st.session_state['hidden_chat'] = True
if 'disable_upload' not in st.session_state:
    st.session_state['disable_upload'] = False
if "messages" not in st.session_state:
    st.session_state['messages'] = []
if 'first_file' not in st.session_state:
    st.session_state['first_file'] = True
if 'cropped_img' not in st.session_state:
    st.session_state['cropped_img'] = None
if 'arm_chatbox' not in st.session_state:
    st.session_state['arm_chatbox'] = False
chat_box = st.chat_input("What do you want to ask?", disabled=st.session_state['hidden_chat'])
#print(st.session_state['disable_upload'])
def show_upload(state:bool):
    st.session_state["uploader_visible"] = state
    st.session_state['disable_upload'] = not st.session_state['disable_upload'] #remove this line in future?
    
def show_upload_reset(state:bool):
    st.session_state["uploader_visible"] = state
    st.session_state['disable_upload'] = not st.session_state['disable_upload'] #remove this line in future?
    st.session_state['arm_chatbox'] = False
    st.session_state['messages'] = []
    st.session_state['hidden_chat'] = True
    
with st.chat_message("AION"):
    cols= st.columns((3,1,1))
    cols[0].write("Do you want to upload a file?")
    cols[1].button("Yes", use_container_width=True, on_click=show_upload, disabled=st.session_state['disable_upload'], args=[True])
    cols[2].button("Reset", use_container_width=True, on_click=show_upload_reset, args=[False])

if st.session_state["uploader_visible"]:
    with st.chat_message("AION"):
        file = st.file_uploader("Upload your data")
        if file:
            img = Image.open(file)
            canvas_width = img.size[0]
            canvas_height = img.size[1]
            gpa = (canvas_width // 100) - 1
            clms = st.columns((gpa, 2))
            if st.session_state['first_file']:
                st.session_state['first_file'] = False
                with st.spinner("Processing your file"):
                    time.sleep(1.5)
            with clms[0]:
                canvas_result = st_canvas(
                    fill_color='#EA101077',
                    stroke_width=3,
                    background_image=img,
                    background_color="rgba(255, 255, 255, 0)",
                    height=canvas_height,
                    width=canvas_width,
                    drawing_mode='rect',
                    key="color_annotation_app",
                )
                if canvas_result.json_data is not None:
                    st.session_state['hidden_chat'] = False
                    objects = canvas_result.json_data['objects']
                    if len(objects) > 0:
                        for obj in objects:
                            if obj["type"] == "rect":
                                img_width, img_height = img.size
                                x_scale = img_width / canvas_width
                                y_scale = img_height / canvas_height
                                x = int(obj["left"] * x_scale)
                                y = int(obj["top"] * y_scale)
                                w = int(obj["width"] * x_scale)
                                h = int(obj["height"] * y_scale)
                                transform = T.ToPILImage()
                                st.session_state['cropped_img'] = transform(np.array(img)[y:y+h, x:x+w])
                                st.session_state['arm_chatbox'] = True
            with clms[1]:
                with st.expander('Click here for intructions'):
                    st.markdown('Draw a box covering the desired object (left click on the top left corner then drag to the bottom right until desired box is created)')
if st.session_state['arm_chatbox']:
    for message in st.session_state['messages']:
            with st.chat_message(message["role"]):
                st.write(message["content"])

if st.session_state['arm_chatbox']:
    if chat_box:
        with st.chat_message("user"):
            st.markdown(chat_box)
        st.session_state['messages'].append({"role": "user", "content": chat_box})
        
        content = [st.session_state['cropped_img'], f'{chat_box} Please give a descriptive, accurate, and detailed response.']
        response = gemini.generate_content(content).text
        
        with st.chat_message('AION'):
            st.write_stream(response_generator(response)) 
        st.session_state['messages'].append({"role": "AION", "content": response})                                                                                          