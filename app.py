import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="E-commerce URL Generator", layout="wide")

st.title("🛍️ E-commerce URL Generator")
st.markdown("Generate search URLs for multiple e-commerce platforms based on your keywords.")

# Sidebar input
st.sidebar.header("🔍 Search Settings")
keywords = st.sidebar.text_area("Enter keywords (one per line)", height=150)
platforms = st.sidebar.multiselect(
    "Select platforms",
    ["Amazon", "Daraz", "eBay", "AliExpress"],
    default=["Amazon", "Daraz"]
)

# URL templates
url_templates = {
    "Amazon": "https://www.amazon.com/s?k={query}",
    "Daraz": "https://www.daraz.pk/catalog/?q={query}",
    "eBay": "https://www.ebay.com/sch/i.html?_nkw={query}",
    "AliExpress": "https://www.aliexpress.com/wholesale?SearchText={query}"
}

# Generate URLs
def generate_urls(keywords, platforms):
    urls = []
    for keyword in keywords:
        encoded = urllib.parse.quote_plus(keyword.strip())
        for platform in platforms:
            url = url_templates[platform].format(query=encoded)
            urls.append(url)
    return urls

# Main logic
if st.sidebar.button("Generate URLs"):
    if not keywords.strip():
        st.warning("Please enter at least one keyword.")
    elif not platforms:
        st.warning("Please select at least one platform.")
    else:
        keyword_list = keywords.strip().split("\n")
        generated_urls = generate_urls(keyword_list, platforms)
        st.session_state.generated_urls = generated_urls

# Display results
if "generated_urls" in st.session_state:
    st.subheader("🔗 Generated URLs")
    for i, url in enumerate(st.session_state.generated_urls):
        col1, col2 = st.columns([0.05, 0.95])
        
        # Use a safe key instead of the full URL
        safe_key = f"url_{i}"
        
        # Create checkbox and let Streamlit handle session state
        selected = col1.checkbox(f"{i+1}", key=safe_key, value=st.session_state.get(safe_key, False))
        
        # Display the URL as a clickable link
        col2.markdown(f"[{url}]({url})")

    # Collect selected URLs
    selected_urls = [
        st.session_state.generated_urls[i]
        for i in range(len(st.session_state.generated_urls))
        if st.session_state.get(f"url_{i}", False)
    ]

    if selected_urls:
        st.markdown("### ✅ Selected URLs")
        for url in selected_urls:
            st.markdown(f"- [{url}]({url})")
            import requests
from bs4 import BeautifulSoup

# Common headers
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

# Amazon scraper
def scrape_amazon(url):
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.content, "html.parser")

    products = []
    for item in soup.select("[data-component-type='s-search-result']"):
        title = item.select_one("h2 span")
        price_whole = item.select_one(".a-price-whole")
        price_fraction = item.select_one(".a-price-fraction")

        if title:
            product = {
                "Platform": "Amazon",
                "Title": title.get_text(strip=True),
                "Price": None,
                "URL": url
            }
            if price_whole and price_fraction:
                product["Price"] = f"{price_whole.get_text(strip=True)}.{price_fraction.get_text(strip=True)}"
            products.append(product)
    return products

# Daraz scraper
def scrape_daraz(url):
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.content, "html.parser")

    products = []
    for item in soup.select(".gridItem--Yd0sa"):
        title = item.select_one(".title--WbWjP")
        price = item.select_one(".price--NVB62")

        if title and price:
            products.append({
                "Platform": "Daraz",
                "Title": title.get_text(strip=True),
                "Price": price.get_text(strip=True),
                "URL": url
            })
    return products

# Dispatcher
def scrape_url(url):
    if "amazon.com" in url:
        return scrape_amazon(url)
    elif "daraz.pk" in url:
        return scrape_daraz(url)
    else:
        st.warning(f"Scraping not yet supported for: {url}")
        return []

# Scrape button
if selected_urls:
    if st.button("Scrape Selected URLs"):
        all_data = []

        for url in selected_urls:
            scraped = scrape_url(url)
            all_data.extend(scraped)

        if all_data:
            df = pd.DataFrame(all_data)
            st.subheader("🧹 Scraped & Cleaned Data")
            st.dataframe(df)

            # CSV download
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="scraped_products.csv",
                mime="text/csv"
            )
        else:
            st.info("No data scraped. Try different URLs or check your internet connection.")

