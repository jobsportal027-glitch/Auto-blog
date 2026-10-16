import os
import json
import requests
import google.generativeai as genai
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# 1. Environment Variables Check
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BLOG_ID = os.environ.get("BLOG_ID")
GCP_SERVICE_ACCOUNT_KEY = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# 2. Generate Content with H1, H2, H3 Headings, Links, and Categories
def generate_job_post():
    prompt = """
    Write a 100% unique, plagiarism-free, detailed blog post in HTML format about latest Global Career & Visa Sponsorship Jobs opportunities.
    Ensure proper HTML heading hierarchy:
    - Main Title inside <h1>
    - Major sections inside <h2>
    - Sub-sections inside <h3>
    Include:
    - Job Overview & Requirements with bullet points
    - Visa Sponsorship Details
    - An External Link pointing to an official immigration or career portal (e.g., <a href="https://www.ec.europa.eu" target="_blank">Eures Job Portal</a>)
    - An Internal Link pointing back to the main job portal category page
    - How to Apply Section
    Use clean HTML formatting (paragraphs, bold text, lists, h1, h2, h3). Do not include <html> or <body> tags, just the content.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    
    title = "Latest Global Career & Visa Sponsorship Opportunities"
    content = response.text
    return title, content

# 3. Get Pixabay Image
def get_image():
    if not PIXABAY_API_KEY:
        return "https://via.placeholder.com/800x400.png?text=Jobs+Portal"
    try:
        url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q=job+career&image_type=photo"
        res = requests.get(url).json()
        if res.get("hits"):
            return res["hits"][0]["webformatURL"]
    except Exception as e:
        print("Image fetch error:", e)
    return "https://via.placeholder.com/800x400.png?text=Jobs+Portal"

# 4. Get Google OAuth Access Token from Service Account Key
def get_access_token():
    creds_json = json.loads(GCP_SERVICE_ACCOUNT_KEY)
    scopes = [
        'https://www.googleapis.com/auth/blogger',
        'https://www.googleapis.com/auth/indexing'
    ]
    credentials = service_account.Credentials.from_service_account_info(creds_json, scopes=scopes)
    credentials.refresh(Request())
    return credentials.token

# 5. Post to Blogger API v3 with Category Labels
def post_to_blogger(title, content, image_url, token):
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    full_content = f'<p><img src="{image_url}" alt="Job Image" style="width:100%; max-width:800px;"/></p>' + content
    
    # Category wise labels/tags
    labels = ["Global Career", "Visa Sponsorship", "Jobs"]
    
    payload = {
        "kind": "blogger#post",
        "title": title,
        "content": full_content,
        "labels": labels
    }
    
    res = requests.post(url, headers=headers, json=payload)
    print("Blogger Post Status:", res.status_code)
    if res.status_code == 200:
        post_data = res.json()
        print("Published URL:", post_data.get("url"))
        return post_data.get("url")
    else:
        print("Blogger Error Response:", res.text)
        return None

# 6. Index URL via Google Indexing API
def index_url(post_url, token):
    if not post_url:
        return
    url = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": post_url,
        "type": "URL_UPDATED"
    }
    res = requests.post(url, headers=headers, json=payload)
    print("Indexing API Status:", res.status_code, res.text)

if __name__ == "__main__":
    print("Starting Auto Blogging Process...")
    token = get_access_token()
    title, content = generate_job_post()
    image_url = get_image()
    post_url = post_to_blogger(title, content, image_url, token)
    if post_url:
        index_url(post_url, token)
    print("Process Completed!")
