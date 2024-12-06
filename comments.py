import os
import json
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs
from collections import defaultdict
from datetime import datetime

api_key = 'AIzaSyALU9ZCw48L-JAW8DdcDs4JZjZi3_mHaPQ'  # Replace with your API key
os.makedirs('data', exist_ok=True)
youtube = build('youtube', 'v3', developerKey=api_key)

def extract_video_id(url):
    """Extract the video ID from a YouTube URL."""
    try:
        parsed_url = urlparse(url)
        if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
            return parse_qs(parsed_url.query).get('v', [None])[0]
        elif parsed_url.hostname == 'youtu.be':
            return parsed_url.path.lstrip('/')
    except Exception as e:
        return None
    return None

def get_comments(url, max_results=30):
    """
    Retrieve the first `max_results` comments for the given video ID.
    """
    video_id = extract_video_id(url)
    comments_data = []
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_results,  # Limit to max_results
            order="relevance"  # Retrieve relevant/top comments
        )
        response = request.execute()
        for item in response['items']:
            snippet = item['snippet']['topLevelComment']['snippet']
            comment_data = {
                'author': snippet['authorDisplayName'],
                'text': snippet['textDisplay'],
                'likes': snippet['likeCount'],
                'publish_time': snippet['publishedAt'],
                'reply_count': item['snippet']['totalReplyCount']
            }
            comments_data.append(comment_data)

        # Stop after fetching the required number of comments
        if len(comments_data) >= max_results:
            return comments_data[:max_results]

    except Exception as e:
        print(f"Error retrieving comments: {e}")

    return comments_data[:max_results]

def extract_content(comments_data): 
    """Extract all comments into a single string."""
    all_text = " ".join(entry['text'] for entry in comments_data)
    return all_text

def get_video_metadata(video_id):
    """Retrieve metadata for the given video ID."""
    try:
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        )
        response = request.execute()
        if response["items"]:
            video_info = response["items"][0]
            return {
                "title": video_info["snippet"]["title"],
                "description": video_info["snippet"]["description"],
                "channel_title": video_info["snippet"]["channelTitle"],
                "publish_date": video_info["snippet"]["publishedAt"],
                "view_count": video_info["statistics"].get("viewCount", 0),
                "like_count": video_info["statistics"].get("likeCount", 0),
                "comment_count": video_info["statistics"].get("commentCount", 0),
                "duration": video_info["contentDetails"]["duration"],
                "category_id": video_info["snippet"]["categoryId"]
            }
    except Exception as e:
        print(f"Error retrieving video metadata: {e}")
    return {"error": "Video metadata not found."}

def get_video_category(category_id):
    """Retrieve the name of the video category from its ID."""
    if not category_id:
        return "Unknown Category"

    try:
        request = youtube.videoCategories().list(
            part="snippet",
            id=category_id  # Only use the 'id' parameter
        )
        response = request.execute()
        if response["items"]:
            return response["items"][0]["snippet"]["title"]
    except Exception as e:
        print(f"Error retrieving category: {e}")

    return "Unknown Category"

def get_top_comments(comments_data, count=10):
    """Get the top 'count' liked and replied comments."""
    top_liked = sorted(comments_data, key=lambda x: x["likes"], reverse=True)[:count]
    top_replied = sorted(comments_data, key=lambda x: x["reply_count"], reverse=True)[:count]
    return top_liked, top_replied

def get_comment_trends_monthly(comments_data):
    """Prepare data for comment trends over months."""
    monthly_trends = defaultdict(int)
    for comment in comments_data:
        date = comment["publish_time"].split("T")[0]
        month = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
        monthly_trends[month] += 1
    return dict(monthly_trends)
