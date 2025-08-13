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
