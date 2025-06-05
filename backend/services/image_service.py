import os
import base64
import logging
from prompt_engineering.image_gen import get_image_prompt
import http.client
import requests
import json
import time
import random

logger = logging.getLogger(__name__)
"""
import http.client

conn = http.client.HTTPSConnection("api.us1.bfl.ai")

conn.request("GET", "/v1/get_result")

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))

"""
class ImageService:
    # Available BFL FLUX models
    FLUX_MODELS = {
        "ultra": "https://api.us1.bfl.ai/v1/flux-pro-1.1-ultra",
        "standard": "https://api.us1.bfl.ai/v1/flux-pro-1.1",
        "fast": "https://api.us1.bfl.ai/v1/flux-pro-1.1-fast",
        "anime": "https://api.us1.bfl.ai/v1/flux-anime-1.1"
    }

    def __init__(self, api_key):
        self.api_key = api_key
        self.api_headers = {
            'Content-Type': 'application/json',
            'x-key': api_key
        }

    # Given the character ID, passes in the base64 image
    def get_reference_image(self, character_id):
        """Get base64 encoded reference image for character"""
        print("We got to reference image")
        # Load directly from file
        try:
            #get the image path for nina or harlold
            image_path = os.path.join(os.path.dirname(__file__), "..", "assets", f"{character_id}.png")
            print(f"Looking for image at: {image_path}")
            # Check if the file exists
            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                    logger.info("Passed in base64 image from get_reference_image")
                    return base64.b64encode(image_bytes).decode('utf-8')
            else:
                logger.error(f"Image not found: {image_path}")
                return None
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return None

    def generate_image(self, body_language_desc, character_id='Nina', FLUX_model='anime'):
        """Return actual image data"""
        logger.info(f"Image generation requested for {character_id} using FLUX: {FLUX_model}")
        
        # Get the base64 encoded image directly
        image_data = self.get_reference_image(character_id)
        if not image_data:
            logger.error(f"Failed to get reference image for {character_id}")
            return "https://example.com/default_nina.jpg"
        
        model_url = self.FLUX_MODELS.get(FLUX_model, self.FLUX_MODELS["anime"])
        
        # Use the provided body language description in the prompt
        prompt = f"Young female animetherapist with {body_language_desc}"
        payload = {
            "prompt": body_language_desc,
            "prompt_upsampling": True,
            "seed": random.randint(1, 10000),
            "aspect_ratio": "9:16",
            "safety_tolerance": 4,
            "output_format": "png",
            "raw": False,
            "image_prompt": image_data,
            "image_prompt_strength": 0.4
        }
        
        try:
            response = requests.post(model_url, json=payload, headers=self.api_headers)
            
            if response.status_code == 200:
                poll_url = response.json()["polling_url"]
                logger.info(f"Got polling URL: {poll_url}")
                
                
                # Keep checking the polling URL until image is ready or retries run out
                max_retries = 10
                wait_time = 6  # seconds
                
                for attempt in range(max_retries):
                     time.sleep(wait_time)
                     poll_data = requests.get(poll_url, headers=self.api_headers).json()
                     status = poll_data.get("status")
                     
                if status == "Ready" and poll_data.get("result", {}).get("sample"):
                     img_url = poll_data["result"]["sample"]
                     img_content = requests.get(img_url).content
                     logger.info("Successfully downloaded generated image")
                    
                     self.archive_image(img_content, body_language_desc, character_id)
                     return f"data:image/png;base64,{base64.b64encode(img_content).decode('utf-8')}"
                logger.info(f"Attempt {attempt+1}/{max_retries}: Status is '{status}', waiting...")
                
                # If still not ready after all retries
                logger.warning("Image was never ready. Using reference image as fallback.")
        except Exception as e:
            logger.error(f"Error in image generation: {str(e)}")
        
        # Fallback to reference image
        logger.info("Using reference image as fallback")
        return f"data:image/png;base64,{image_data}"

    #This saves the image to the local
    def archive_image(self, img_content, body_language_desc, character_id):
        """Save generated image to disk with appropriate naming"""
        try:
            # Create directory path for character
            base_dir = os.path.join(os.path.dirname(__file__), "..", "logs", "generated_images", character_id)
            save_dir = os.path.abspath(base_dir)
            os.makedirs(save_dir, exist_ok=True)
            
            # Create filename with timestamp and emotion hint
            timestamp = int(time.time())
            emotion_hint = body_language_desc.split()[0] if body_language_desc else "unknown"
            filename = f"{save_dir}/{character_id}_{emotion_hint}_{timestamp}.png"
            
            # Save the image
            with open(filename, "wb") as f:
                f.write(img_content)
            
            logger.info(f"Archived image to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to archive image: {str(e)}")
            return False
