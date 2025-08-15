import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import json
import pandas as pd
import re

# Set your OpenAI API key
openai_api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else ""
client = OpenAI(api_key=openai_api_key)

# ------------------ LLM URL Generator ------------------

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
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        content = response.choices[0].message.content
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return data.get("URLs", [])[:num_urls]
    except Exception as e:
        st.error(f"Error generating URLs: {e}")
    return []

# ------------------ Scraping Logic ------------------

def scrape_url_info(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.string.strip() if soup.title else "No title"
        heading = soup.find(['h1', 'h2', 'h3'])
        heading_text = heading.get_text(strip=True) if heading else "No heading"

        meta_desc = soup.find("meta", attrs={"name": "description"})
        description = meta_desc["content"].strip() if meta_desc and "content" in meta_desc.attrs else "No description"

        price = "Not found"
        for tag in soup.find_all(text=True):
            tag = tag.strip()
            if any(currency in tag for currency in ["$", "Rs", "₹"]) and any(char.isdigit() for char in tag):
                price = tag
                break

        return {
            "URL": url,
            "Title": title,
            "Heading": heading_text,
            "Description": description,
            "Price": price
        }
    except Exception as e:
        return {
            "URL": url,
            "Title": "Error",
            "Heading": "Error",
            "Description": str(e),
            "Price": "Error"
        }

# ------------------ Streamlit UI ------------------

st.set_page_config(page_title="🛒 Product URL Finder", layout="wide")
st.title("🛒 Real-Time Product URL Finder & Scraper")

product_name = st.text_input("Enter product name", "laptop")
num_urls = st.selectbox("Number of URLs to generate", [5, 10])

if st.button("Generate URLs"):
    with st.spinner("Generating URLs using GPT..."):
        urls = generate_real_urls(product_name, num_urls)
        if urls:
            st.session_state["urls"] = urls
        else:
            st.warning("No URLs generated.")

# ------------------ Display Checkboxes ------------------

selected_urls = []
if "urls" in st.session_state:
    st.subheader("✅ Select URLs to Scrape")
    for i, url in enumerate(st.session_state["urls"]):
        if st.checkbox(url, key=f"url_{i}"):
            selected_urls.append(url)

# ------------------ Scrape & Export ------------------

if selected_urls:
    if st.button("Scrape Selected URLs"):
        with st.spinner("Scraping selected URLs..."):
            results = [scrape_url_info(url) for url in selected_urls]
            df = pd.DataFrame(results)
            st.success("Scraping complete!")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV", csv, "scraped_results.csv", "text/csv")




