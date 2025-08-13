import streamlit as st
import json
import asyncio
import nest_asyncio
import os
from openai import OpenAI
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

# Enable nested async loops for Streamlit
nest_asyncio.apply()

# Initialize OpenAI client securely
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # 🔐 Add this in Streamlit Secrets

# ⚠️ Usage warning
st.set_page_config(page_title="🛒 Ecommerce URL Generator", layout="wide")
st.title("🛒 Ecommerce URL Generator & Scraper")
st.warning("⚠️ This app uses the developer's OpenAI credits to generate URLs. Please use responsibly. Excessive use may disable the app.")
st.write("Enter a product name and number of URLs to generate real shopping links. Optionally scrape selected URLs for product info.")

# Generate URLs using GPT-3.5
def generate_real_urls(product_name, num_urls):
    prompt = f"""
You are a product researcher. Generate {num_urls} real URLs for buying "{product_name}" from Amazon, Flipkart, Daraz, etc.

Return only JSON format like this:
{{
  "URLs": [
    "https://example.com/product1",
    "https://example.com/product2"
  ]
}}
Only return JSON. No explanation.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # ✅ Cheaper model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return data.get("URLs", [])[:num_urls]
    except Exception as e:
        return [f"Error generating URLs: {e}"]

# Async scraping
async def async_scrape_url(url):
    crawler = AsyncWebCrawler()
    config = CrawlerRunConfig(
        urls=[url],
        extract_text=True,
        extract_metadata=True,
        extract_links=False,
        browser=BrowserConfig(headless=True)
    )
    result = await crawler.run(config)
    if result and result[0].success:
        return result[0].data
    return {"error": "Failed to extract data"}

def scrape_url_info(url):
    try:
        return asyncio.run(async_scrape_url(url))
    except Exception as e:
        return {"error": str(e)}

# Sidebar inputs
st.sidebar.header("🔧 Input Settings")
product_name = st.sidebar.text_input("Product Name", value="wireless headphones")
num_urls = st.sidebar.slider("Number of URLs", min_value=1, max_value=10, value=5)

# Generate URLs
if st.sidebar.button("Generate URLs"):
    urls = generate_real_urls(product_name, num_urls)

    if urls and not urls[0].startswith("Error"):
        st.session_state.generated_urls = urls
        # Reset checkbox states
        for url in urls:
            st.session_state[url] = False
    else:
        st.error("❌ Failed to generate URLs. This may be due to API limits, missing credits, or invalid key.")

# Display generated URLs and checkboxes
if "generated_urls" in st.session_state:
    st.subheader("🔗 Generated URLs")
    for url in st.session_state.generated_urls:
        col1, col2 = st.columns([0.05, 0.95])
        selected = col1.checkbox("", key=url, value=st.session_state.get(url, False))
        col2.markdown(f"[{url}]({url})")
        st.session_state[url] = selected

    # Collect selected URLs
    selected_urls = [url for url in st.session_state.generated_urls if st.session_state.get(url)]

    # Scrape selected URLs
    if selected_urls:
        st.subheader("🧠 Scraped Info")
        for url in selected_urls:
            result = scrape_url_info(url)
            if "error" in result:
                st.error(f"URL: {url}\nError: {result['error']}")
            else:
                st.markdown(f"**URL:** {url}")
                st.write(f"**Title:** {result.get('title', 'N/A')}")
                st.write(f"**Heading:** {result.get('heading', 'N/A')}")
                st.write(f"**Price:** {result.get('price', 'N/A')}")
                st.markdown("---")
