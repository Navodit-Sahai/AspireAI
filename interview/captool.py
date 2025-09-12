import cv2
from dotenv import load_dotenv
import base64

load_dotenv()

def capture_image()->str:
    """captures frame from the webcam ,resizes it and then encodes it as Base64 JPEG (raw string) and returns it"""

    for idx in range(4):
        cap=cv2.VideoCapture(idx, cv2.CAP_AVFOUNDATION)
        if cap.isOpened():
            for _  in range(10):
                cap.read()
            ret,frame=cap.read()
            cap.release()
            if not ret:
                continue
            # cv2.imwrite('sample.jpg',frame)
            ret,buf=cv2.imencode('.jpg',frame)
            if ret:
                return base64.b64encode(buf).decode('utf-8')
        raise RuntimeError("Could not open any webcam")
    
    
from groq import Groq
    
def analyze_image_with_query(query: str)-> str:
    """expects a string with query . captures image and sends the image and query to groq vision model."""
    imgb64=capture_image()
    model="meta-llama/llama-4-maverick-17b-128e-instruct"
    if query and imgb64:
        client=Groq()
        messages=[
                        {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": query
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{imgb64}",
                        },
                    },
                ],
            }]
        chat_completion=client.chat.completions.create(
        messages=messages,
        model=model
        )
        return chat_completion.choices[0].message.content
    else:
        return "Error: both 'query' and 'image' fields required."
            