import streamlit as st
import openai
import json
import asyncio
import nest_asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

# Enable nested async loops
nest_asyncio.apply()

# Set your OpenAI API key
openai.api_key = "your-openai-key-here"  # 🔒 Replace securely

# Generate URLs using GPT
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
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        content = response.choices[0].message["content"]
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

# Streamlit UI
st.set_page_config(page_title="🛒 Ecommerce URL Generator", layout="wide")
st.title("🛒 Ecommerce URL Generator & Scraper")
st.write("Enter a product name and number of URLs to generate real shopping links. Optionally scrape selected URLs for product info.")

# Sidebar inputs
st.sidebar.header("🔧 Input Settings")
product_name = st.sidebar.text_input("Product Name", value="wireless headphones")
num_urls = st.sidebar.slider("Number of URLs", min_value=1, max_value=10, value=5)

# Generate URLs
if st.sidebar.button("Generate URLs"):
    urls = generate_real_urls(product_name, num_urls)
    if urls and not urls[0].startswith("Error"):
        st.subheader("🔗 Generated URLs")
        selected_urls = []
        for url in urls:
            col1, col2 = st.columns([0.05, 0.95])
            selected = col1.checkbox("", key=url)
            col2.markdown(f"[{url}]({url})")
            if selected:
                selected_urls.append(url)

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
    else:
        st.error(urls[0])
