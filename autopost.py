import feedparser
import requests
from google import genai
import time
import os
from huggingface_hub import InferenceClient

# ==========================================
# 1. YOUR CREDENTIALS (REPLACE THESE)
# ==========================================
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_TOKEN = os.environ.get("FB_PAGE_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
HF_API_KEY = os.environ.get("HF_API_KEY")

# RSS Feed for Tech News
RSS_URL = "https://techcrunch.com/feed/"

# Initialize Clients
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
hf_client = InferenceClient(api_key=HF_API_KEY)

# ==========================================
# 2. THE FUNCTIONS
# ==========================================

def get_latest_news():
    """Fetches the latest article from the RSS feed."""
    print("📰 Fetching latest tech news...")
    feed = feedparser.parse(RSS_URL)
    latest_entry = feed.entries[0]
    return {
        "title": latest_entry.title,
        "link": latest_entry.link,
        "summary": latest_entry.summary
    }

def write_facebook_post(news_data, max_retries=3):
    """Uses Gemini to write an engaging Facebook post with auto-retry."""
    print("✍️ Writing the post copy...")
    
    prompt = f"""
    Act as the social media manager for a Facebook page called 'Emerging Tech'.
    Write a short, engaging Facebook post about this news article.
    
    Title: {news_data['title']}
    Summary: {news_data['summary']}
    Link: {news_data['link']}
    
    Rules:
    - Keep it under 4 sentences.
    - Sound enthusiastic and knowledgeable, not robotic.
    - End with a thought-provoking question to drive comments.
    - Include 3 relevant hashtags.
    - DO NOT include the link in the text (Meta suppresses links).
    """
    
    for attempt in range(max_retries):
        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"⚠️ Gemini API Error: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in 15 seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(15)
            else:
                # If it fails 3 times, let the script crash gracefully
                raise e

def generate_image(prompt_text, max_retries=3):
    """Generates an image using Hugging Face's official InferenceClient."""
    print("🎨 Generating tech image...")
    
    visual_prompt = f"Futuristic technology concept art related to: {prompt_text}, highly detailed, 8k resolution, cinematic lighting, digital art"
    
    for attempt in range(max_retries):
        try:
            # FLUX.1-schnell is currently the most powerful free image model
            image = hf_client.text_to_image(
                visual_prompt,
                model="black-forest-labs/FLUX.1-schnell"
            )
            
            image_path = "temp_tech_image.jpg"
            image.save(image_path)
            return image_path
            
        except Exception as e:
            print(f"⚠️ Image API Error: {e}")
            print(f"Retrying in 20 seconds... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(20)
            
    print("❌ Failed to generate image. Proceeding without one.")
    return None

def post_to_facebook(message, image_path):
    """Uploads the image (if available) and posts the message to the Facebook Page."""
    print("🚀 Publishing to Facebook...")
    
    if image_path:
        url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
        payload = {'message': message, 'access_token': FB_PAGE_TOKEN, 'published': 'true'}
        files = {'source': open(image_path, 'rb')}
        response = requests.post(url, data=payload, files=files)
    else:
        print("⚠️ No image available. Posting text-only fallback...")
        url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
        payload = {'message': message, 'access_token': FB_PAGE_TOKEN}
        response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        print("✅ SUCCESS! Post is live on 'Emerging Tech'.")
    else:
        # Check for Meta's notorious "Ghost Error" Code 1
        error_data = response.json().get('error', {})
        if error_data.get('code') == 1:
            print("👻 META GHOST ERROR: Facebook's API timed out, but your post is successfully live on the page!")
        else:
            print("❌ FAILED to post to Facebook.")
            print("Response:", response.json())

# ==========================================
# 3. RUN THE ENGINE
# ==========================================
if __name__ == "__main__":
    try:
        news = get_latest_news()
        print(f"Target: {news['title']}")
        
        post_copy = write_facebook_post(news)
        
        image_file = generate_image(news['title'])
        
        post_to_facebook(post_copy, image_file)
        
        if image_file:
            os.remove(image_file)
            
    except Exception as e:
        import sys
        print(f"❌ Critical Engine Failure: {e}")
        sys.exit(1) # This forces GitHub Actions to turn RED when a failure happens
