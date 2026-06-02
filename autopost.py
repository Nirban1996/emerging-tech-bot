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
