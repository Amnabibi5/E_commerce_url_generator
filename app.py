import streamlit as st
import pandas as pd
import urllib.parse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# 📌 Page Config
st.set_page_config(page_title="E-commerce URL Generator", layout="wide")
st.title("🛍️ E-commerce URL Generator")
st.markdown("Generate and scrape search URLs for multiple e-commerce platforms.")

# 📌 Sidebar Inputs
st.sidebar.header("🔍 Search Settings")
keywords = st.sidebar.text_area("Enter keywords (one per line)", height=150)
platforms = st.sidebar.multiselect(
    "Select platforms",
    ["Amazon", "Daraz"],
    default=["Amazon", "Daraz"]
)

# 📌 URL Templates
url_templates = {
    "Amazon": "https://www.amazon.com/s?k={query}",
    "Daraz": "https://www.daraz.pk/catalog/?q={query}"
}

# 📌 Generate URLs
def generate_urls(keywords, platforms):
    urls = []
    for keyword in keywords:
        encoded = urllib.parse.quote_plus(keyword.strip())
        for platform in platforms:
            url = url_templates[platform].format(query=encoded)
            urls.append(url)
    return urls

if st.sidebar.button("Generate URLs"):
    if not keywords.strip():
        st.warning("Please enter at least one keyword.")
    elif not platforms:
        st.warning("Please select at least one platform.")
    else:
        keyword_list = keywords.strip().split("\n")
        generated_urls = generate_urls(keyword_list, platforms)
        st.session_state["generated_urls"] = generated_urls
        st.success("URLs generated successfully!")

# 📌 Display URLs with Checkboxes
selected_urls = []
if "generated_urls" in st.session_state:
    st.subheader("🔗 Generated URLs")
    for i, url in enumerate(st.session_state["generated_urls"]):
        col1, col2 = st.columns([0.05, 0.95])
        safe_key = f"url_{i}"
        selected = col1.checkbox(f"{i+1}", key=safe_key, value=st.session_state.get(safe_key, False))
        col2.markdown(f"[{url}]({url})")
        if selected:
            selected_urls.append(url)

# 📌 Scraping Functions
def scrape_amazon(url, page):
    page.goto(url)
    page.wait_for_selector("[data-component-type='s-search-result']")
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

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

def scrape_daraz(url, page):
    page.goto(url)
    page.wait_for_selector("div[data-qa-locator='product-item']")
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    products = []
    for item in soup.select("div[data-qa-locator='product-item']"):
        title = item.select_one("div[data-qa-locator='product-title']")
        price = item.select_one("div[data-qa-locator='product-price']")

        if title and price:
            products.append({
                "Platform": "Daraz",
                "Title": title.get_text(strip=True),
                "Price": price.get_text(strip=True),
                "URL": url
            })
    return products

def scrape_url(url, page):
    if "amazon.com" in url:
        return scrape_amazon(url, page)
    elif "daraz.pk" in url:
        return scrape_daraz(url, page)
    else:
        st.warning(f"Scraping not supported for: {url}")
        return []

# 📌 Scrape Selected URLs
def handle_scraping(urls):
    all_data = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for url in urls:
            st.write(f"Scraping: {url}")
            scraped = scrape_url(url, page)
            all_data.extend(scraped)

        browser.close()
    return all_data

# 📌 Trigger Scraping
if selected_urls:
    if st.button("Scrape Selected URLs"):
        scraped_data = handle_scraping(selected_urls)

        if scraped_data:
            df = pd.DataFrame(scraped_data)
            st.subheader("🧹 Scraped & Cleaned Data")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="scraped_products.csv",
                mime="text/csv"
            )
        else:
            st.info("No data scraped. Try different URLs or check your internet connection.")


