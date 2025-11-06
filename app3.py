import streamlit as st
import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.crawl4ai import Crawl4aiTools
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from urllib.parse import urlparse, urlunparse
import re

# ====== Environment ======
load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY")
YOUTUBE_KEY = os.getenv("YOUTUBE_API_KEY")
INSTAGRAM_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY") or os.getenv("SERPAPI_KEY")

# ====== Streamlit Config ======
st.set_page_config(
    page_title="Think Node - Cross-Platform Intelligence", 
    page_icon="🔍", 
    layout="wide"
)

# ====== CSS ======
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 0 0 20px 20px;
        color: white; text-align: center;
        margin-bottom: 2rem;
    }
    .brand-title { font-size: 3.5em; font-weight: 800; margin-bottom: 0.2em; }
    .brand-subtitle { font-size: 1.3em; opacity: 0.9; margin-bottom: 1em; }
    .insight-box {
        background: #fff; color: #111;
        border-radius: 12px; padding: 2rem; margin: 1rem 0;
        border: 1px solid #e0e0e0; line-height: 1.6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .video-card, .instagram-card {
        background: white; border-radius: 12px;
        padding: 1.5rem; margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #FF0000;
    }
    .instagram-card { border-left: 4px solid #E4405F; }
    .stButton button {
        border-radius: 8px; padding: 0.8rem;
        font-weight: 600; transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# ====== Header ======
st.markdown("""
<div class="header-container">
    <div class="brand-title">Think Node</div>
    <div class="brand-subtitle">Cross-Platform Intelligence & Trend Analysis</div>
    <div style="font-size: 1.1em; opacity: 0.85;">
        Professional Insights from YouTube, Google, and Instagram
    </div>
</div>
""", unsafe_allow_html=True)

# ====== Sidebar ======
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    yt_count = st.slider("YouTube Results", 1, 20, 8)
    insta_count = st.slider("Instagram Posts", 1, 12, 6)
    search_depth = st.selectbox(
        "Analysis Depth", 
        ["Quick Overview", "Standard Analysis", "Deep Research"], 
        index=1
    )
    
    # Model Selection
    model_mapping = {
        "Quick Overview": "qwen/qwen3-32b",
        "Standard Analysis": "llama-3.3-70b-versatile", 
        "Deep Research": "openai/gpt-oss-20b"
    }
    selected_model = model_mapping[search_depth]
    
    st.markdown(f"**Selected Model:** `{selected_model}`")
    st.markdown("---")
    st.markdown("### 🔑 API Status")
    st.write(f"YouTube API: {'✅' if YOUTUBE_KEY else '❌'}")
    st.write(f"Groq API: {'✅' if GROQ_KEY else '❌'}")
    st.write(f"SerpAPI: {'✅' if SERPAPI_KEY else '❌'}")

# ====== Input ======
col1, col2 = st.columns([3, 1])
with col1:
    topic = st.text_input(
        "🔍 Research Topic or Hashtag", 
        placeholder="e.g., artificial intelligence, Deloitte, dance studios, digital marketing"
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_all = st.button("🚀 Analyze All Platforms", type="primary")

# ====== Platform Buttons ======
st.markdown("### 📊 Select Analysis Platform")
col1, col2, col3 = st.columns(3)
with col1:
    yt_clicked = st.button("🎬 YouTube Analysis", use_container_width=True)
with col2:
    gg_clicked = st.button("🌐 Google + AI Research", use_container_width=True)
with col3:
    insta_clicked = st.button("📸 Instagram Insights", use_container_width=True)

# ====== YouTube Function ======
def fetch_youtube_videos(query, max_results=8):
    """Fetch YouTube videos with engagement metrics"""
    try:
        if not YOUTUBE_KEY:
            st.error("🔑 YouTube API key not configured.")
            return []
            
        youtube = build("youtube", "v3", developerKey=YOUTUBE_KEY)
        
        # Search for videos
        search_response = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results,
            relevanceLanguage="en",
            order="relevance",
            safeSearch="moderate"
        ).execute()

        videos = []
        video_ids = [item["id"]["videoId"] for item in search_response.get("items", []) 
                    if item["id"]["kind"] == "youtube#video"]
        
        if not video_ids:
            st.info("No YouTube videos found for this topic.")
            return []

        # Get detailed statistics
        stats_response = youtube.videos().list(
            part="statistics,contentDetails,snippet",
            id=",".join(video_ids)
        ).execute()

        stats_dict = {item["id"]: item for item in stats_response.get("items", [])}
        
        for item in search_response.get("items", []):
            if item["id"]["kind"] == "youtube#video":
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                stats = stats_dict.get(video_id, {})
                statistics = stats.get("statistics", {})
                
                # Calculate engagement
                views = int(statistics.get("viewCount", 0))
                likes = int(statistics.get("likeCount", 0))
                comments = int(statistics.get("commentCount", 0))
                engagement_rate = ((likes + comments) / views * 100) if views > 0 else 0
                
                videos.append({
                    "title": snippet.get("title", "Untitled"),
                    "link": f"https://www.youtube.com/watch?v={video_id}",
                    "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                    "channel": snippet.get("channelTitle", "Unknown Channel"),
                    "published_at": snippet.get("publishedAt", ""),
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "engagement_rate": round(engagement_rate, 2),
                    "description": snippet.get("description", "")[:200] + "..." if len(snippet.get("description", "")) > 200 else snippet.get("description", "")
                })
        
        return sorted(videos, key=lambda x: x["views"], reverse=True)
        
    except HttpError as e:
        error_msg = str(e)
        if "quotaExceeded" in error_msg:
            st.error("📹 YouTube API quota exceeded. Please try again tomorrow.")
        elif "keyInvalid" in error_msg:
            st.error("📹 YouTube API key is invalid.")
        else:
            st.error(f"📹 YouTube API Error: {error_msg}")
        return []
    except Exception as e:
        st.error(f"📹 Unexpected error: {str(e)}")
        return []

# ====== INSTAGRAM WITH SERPAPI ======
def fetch_instagram_with_serpapi(query, limit=6):
    """
    Fetch Instagram profiles and posts using SerpAPI
    """
    try:
        if not SERPAPI_KEY:
            st.error("🔑 SerpAPI key not configured.")
            return []

        st.info("🔍 Searching Instagram with SerpAPI...")
        
        # Search for Instagram content
        params = {
            "engine": "google",
            "q": f"site:instagram.com {query}",
            "api_key": SERPAPI_KEY,
            "num": 20,
            "google_domain": "google.com"
        }
        
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
        
        if response.status_code != 200:
            st.error(f"❌ SerpAPI request failed: {response.status_code}")
            return []
        
        data = response.json()
        posts = []
        
        # Extract Instagram links from organic results
        for result in data.get("organic_results", []):
            if len(posts) >= limit:
                break
                
            url = result.get("link", "")
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            
            # Validate Instagram URL
            if not is_valid_instagram_url(url):
                continue
            
            # Create post object
            post_type = "Profile" if "/p/" not in url and "/reel/" not in url else "Post"
            
            posts.append({
                "url": url,
                "title": title,
                "snippet": snippet,
                "type": post_type,
                "source": "SerpAPI"
            })
        
        if posts:
            st.success(f"✅ Found {len(posts)} Instagram results")
            return posts
        else:
            st.info("No Instagram results found via SerpAPI.")
            return []
            
    except Exception as e:
        st.error(f"📸 SerpAPI Error: {str(e)}")
        return []

def is_valid_instagram_url(url):
    """Validate Instagram URL format"""
    if not url or "instagram.com" not in url:
        return False
    
    parsed = urlparse(url)
    path = parsed.path
    
    # Allow profiles, posts, reels
    valid_patterns = [
        r"^/[^/]+/?$",           # Profile: /username
        r"^/p/[^/]+/?$",         # Post: /p/xyz
        r"^/reel/[^/]+/?$",      # Reel: /reel/xyz
        r"^/stories/[^/]+/?$",   # Stories: /stories/username
    ]
    
    return any(re.match(pattern, path) for pattern in valid_patterns)

# ====== Enhanced AI Research Function ======
def perform_ai_research(topic, depth="Standard Analysis"):
    """Enhanced research with configurable depth"""
    
    model_mapping = {
        "Quick Overview": "qwen/qwen3-32b",
        "Standard Analysis": "llama-3.3-70b-versatile", 
        "Deep Research": "openai/gpt-oss-20b"
    }
    
    depth_instructions = {
        "Quick Overview": [
            "Provide a concise overview (max 500 words)",
            "Include 3-5 key points with bullet points",
            "List 5 relevant sources with titles and URLs",
            "Focus on current trends and main concepts",
            "Keep it brief and actionable"
        ],
        "Standard Analysis": [
            "Do a comprehensive Google search for the topic",
            "Produce a 'Sources' section with 8-10 relevant results",
            "Provide analysis with: key findings, recent trends, opportunities",
            "Include both consensus views and notable disagreements",
            "Add actionable insights and recommendations",
            "Format with clear headings and bullet points"
        ],
        "Deep Research": [
            "Conduct exhaustive research on the topic",
            "Provide 12-15 high-quality sources with detailed descriptions",
            "Include: historical context, current state, future projections",
            "Analyze market trends, competitive landscape, risks and opportunities",
            "Provide strategic recommendations and emerging patterns",
            "Include data points, statistics, and expert opinions",
            "Create comprehensive sections with executive summary"
        ]
    }
    
    try:
        if not GROQ_KEY:
            st.error("🔑 Groq API key not configured.")
            return "## Configuration Error\n\nGroq API key is required."
            
        selected_model = model_mapping[depth]
        
        agent = Agent(
            model=Groq(id=selected_model),
            tools=[GoogleSearchTools(), Crawl4aiTools(max_length=4000 if depth == "Deep Research" else 2000)],
            description=f"Senior Research Analyst specializing in {depth.lower()}",
            instructions=[
                f"Research Topic: {topic}",
                f"Analysis Depth: {depth}",
                *depth_instructions[depth],
                "Always cite sources and provide direct URLs",
                "Use professional business language",
                "Include actionable insights and strategic implications",
                "Structure with clear sections and headings",
                "Use markdown formatting for better readability"
            ],
            markdown=True
        )
        
        with st.spinner(f"🔍 Performing {depth} using {selected_model}..."):
            result = agent.run(topic)
            return result.content if result else f"## Research Completed\n\n{depth} completed for '{topic}'."
            
    except Exception as e:
        st.error(f"🤖 Research Error: {str(e)}")
        return f"## Research Error\n\nUnable to complete research: {str(e)}"

# ====== Results Display Functions ======
def display_youtube_results(videos, topic):
    """Display YouTube results with enhanced metrics"""
    if not videos:
        st.info("No YouTube videos found for this topic.")
        return
    
    total_views = sum(v["views"] for v in videos)
    avg_views = total_views // len(videos) if videos else 0
    total_engagement = sum(v["likes"] + v["comments"] for v in videos)
    avg_engagement_rate = sum(v["engagement_rate"] for v in videos) / len(videos) if videos else 0
    
    st.markdown("### 📊 YouTube Analytics Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Videos Analyzed", len(videos))
    with col2:
        st.metric("Total Views", f"{total_views:,}")
    with col3:
        st.metric("Avg Views/Video", f"{avg_views:,}")
    with col4:
        st.metric("Avg Engagement Rate", f"{avg_engagement_rate:.2f}%")
    
    st.markdown(f"### 🎬 Top YouTube Videos for '{topic}'")
    
    for i, video in enumerate(videos, 1):
        with st.container():
            st.markdown(f'<div class="video-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(video["thumbnail"], use_column_width=True)
            with col2:
                st.markdown(f"**#{i}:** [{video['title']}]({video['link']})")
                st.markdown(f"**Channel:** {video['channel']}")
                st.markdown(f"**Published:** {video['published_at'][:10]}")
                if video['description']:
                    with st.expander("Description"):
                        st.write(video['description'])
                
                col_metrics = st.columns(4)
                with col_metrics[0]:
                    st.metric("Views", f"{video['views']:,}")
                with col_metrics[1]:
                    st.metric("Likes", f"{video['likes']:,}")
                with col_metrics[2]:
                    st.metric("Comments", f"{video['comments']:,}")
                with col_metrics[3]:
                    st.metric("Engagement", f"{video['engagement_rate']}%")
            
            st.markdown('</div>', unsafe_allow_html=True)

def display_instagram_results(posts, topic):
    """Display Instagram results"""
    if not posts:
        st.info("No Instagram content found for this topic.")
        return
    
    st.markdown("### 📊 Instagram Results Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Results", len(posts))
    with col2:
        profile_count = sum(1 for p in posts if p.get("type") == "Profile")
        st.metric("Profiles Found", profile_count)
    
    st.markdown(f"### 📸 Instagram Content for '{topic}'")
    
    for i, post in enumerate(posts, 1):
        with st.container():
            st.markdown(f'<div class="instagram-card">', unsafe_allow_html=True)
            
            # Determine icon based on post type
            icon = "👤" if post.get("type") == "Profile" else "📸"
            
            st.markdown(f"**{icon} {post.get('type', 'Post')} #{i}**")
            st.markdown(f"**Title:** {post.get('title', 'Instagram Content')}")
            st.markdown(f"**URL:** [{post['url']}]({post['url']})")
            
            if post.get('snippet'):
                st.markdown(f"**Description:** {post['snippet']}")
            
            st.markdown(f"*Source: {post.get('source', 'SerpAPI')}*")
            
            st.markdown('</div>', unsafe_allow_html=True)

def display_research_insights(insights, topic):
    """Display research insights"""
    st.markdown(f"### 🌐 Comprehensive Research: {topic}")
    st.markdown(f'<div class="insight-box">{insights}</div>', unsafe_allow_html=True)
    
    # Add download button
    st.download_button(
        label="📥 Download Research Report",
        data=insights,
        file_name=f"research_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown",
        use_container_width=True
    )

# ====== Main Execution Logic ======
if analyze_all and topic:
    st.markdown(f"## 🚀 Comprehensive Analysis: {topic}")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # YouTube Analysis
    status_text.text("📹 Fetching YouTube videos...")
    youtube_videos = fetch_youtube_videos(topic, yt_count)
    progress_bar.progress(33)
    
    # Instagram Analysis
    status_text.text("📸 Searching Instagram content...")
    instagram_posts = fetch_instagram_with_serpapi(topic, insta_count)
    progress_bar.progress(66)
    
    # AI Research
    status_text.text("🤖 Performing AI research...")
    research_insights = perform_ai_research(topic, search_depth)
    progress_bar.progress(100)
    
    status_text.text("✅ Analysis Complete!")
    
    # Display results in tabs
    tab1, tab2, tab3 = st.tabs(["🎬 YouTube Analysis", "📸 Instagram Insights", "🌐 Research Report"])
    
    with tab1:
        display_youtube_results(youtube_videos, topic)
    
    with tab2:
        display_instagram_results(instagram_posts, topic)
    
    with tab3:
        display_research_insights(research_insights, topic)

elif yt_clicked and topic:
    st.markdown(f"## 🎬 YouTube Analysis: {topic}")
    with st.spinner("Fetching YouTube videos..."):
        videos = fetch_youtube_videos(topic, yt_count)
    display_youtube_results(videos, topic)

elif gg_clicked and topic:
    st.markdown(f"## 🌐 AI Research: {topic}")
    insights = perform_ai_research(topic, search_depth)
    display_research_insights(insights, topic)

elif insta_clicked and topic:
    st.markdown(f"## 📸 Instagram Analysis: {topic}")
    with st.spinner("Searching Instagram content with SerpAPI..."):
        posts = fetch_instagram_with_serpapi(topic, insta_count)
    display_instagram_results(posts, topic)

# ====== Empty State ======
elif not topic:
    st.markdown("""
        <div style='text-align: center; padding: 4rem 2rem;'>
            <h2>🔍 Ready to Analyze</h2>
            <p style='font-size: 1.2em; color: #666;'>
                Enter a topic above to start your cross-platform analysis.<br>
                Get insights from YouTube, Google, and Instagram in one place.
            </p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Think Node • Cross-Platform Intelligence</div>",
    unsafe_allow_html=True
)