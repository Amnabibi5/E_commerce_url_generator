# app.py

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import openai
import json
import asyncio
import nest_asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

# Enable asyncio compatibility for nested loops
nest_asyncio.apply()

# Set your OpenAI API key here or use environment variable in production
openai.api_key = "place your openai key here"  # ⚠️ Replace with your secure key

checkbox_vars = []  # Hold checkbox URL selection states

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
        messagebox.showerror("OpenAI Error", f"Error generating URLs:\n{e}")
        return []

# ✅ Async scraping using Crawl4AI
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

# ✅ GUI Functions
def on_generate_urls():
    product = product_entry.get().strip()
    try:
        num = int(num_entry.get())
    except ValueError:
        messagebox.showerror("Invalid input", "Please enter a valid number.")
        return

    if not product:
        messagebox.showerror("Input Error", "Please enter a product name.")
        return

    for widget in checkbox_frame.winfo_children():
        widget.destroy()
    checkbox_vars.clear()
    output_text.delete(1.0, tk.END)

    urls = generate_real_urls(product, num)
    if not urls:
        output_text.insert(tk.END, "No relevant URLs found.\n")
        return

    for url in urls:
        var = tk.BooleanVar()
        row_frame = ttk.Frame(checkbox_frame)
        row_frame.pack(anchor='w', fill='x', padx=5, pady=2)

        chk = ttk.Checkbutton(row_frame, variable=var)
        chk.pack(side='left')

        link = tk.Label(row_frame, text=url, fg="blue", cursor="hand2", wraplength=700, justify="left", font=("Arial", 9, "underline"))
        link.pack(side='left', padx=5)
        link.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))

        checkbox_vars.append((url, var))

def on_scrape_selected():
    output_text.delete(1.0, tk.END)
    selected_urls = [url for url, var in checkbox_vars if var.get()]
    if not selected_urls:
        output_text.insert(tk.END, "No URLs selected.\n")
        return

    for url in selected_urls:
        result = scrape_url_info(url)
        if "error" in result:
            output_text.insert(tk.END, f"URL: {url}\nError: {result['error']}\n\n{'-'*80}\n")
        else:
            title = result.get('title', 'N/A')
            heading = result.get('heading', 'N/A')
            price = result.get('price', 'N/A')
            output_text.insert(tk.END, f"URL: {url}\nTitle: {title}\nHeading: {heading}\nPrice: {price}\n\n{'-'*80}\n")

# ✅ GUI Setup
root = tk.Tk()
root.title("🛒 Real-Time Product URL Finder & Scraper")
root.geometry("980x720")
root.configure(bg="#f7f5fc")

style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", font=("Arial", 11), background="#f7f5fc")
style.configure("TButton", font=("Arial", 10, "bold"))

main_frame = ttk.Frame(root, padding=15)
main_frame.pack(fill=tk.BOTH, expand=True)

ttk.Label(main_frame, text=" Enter Product Name:").grid(row=0, column=0, sticky="w")
product_entry = ttk.Entry(main_frame, width=50)
product_entry.grid(row=0, column=1, padx=10, pady=5)

ttk.Label(main_frame, text=" Number of URLs:").grid(row=1, column=0, sticky="w")
num_entry = ttk.Entry(main_frame, width=10)
num_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

ttk.Button(main_frame, text=" Generate URLs", command=on_generate_urls).grid(row=2, column=0, pady=10)
ttk.Button(main_frame, text=" Scrape Selected URLs", command=on_scrape_selected).grid(row=2, column=1, pady=10, sticky="w")

# Checkbox scroll area
checkbox_canvas = tk.Canvas(main_frame, height=180, bg="#ffffff", bd=1, relief="sunken")
checkbox_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=checkbox_canvas.yview)
checkbox_scrollable_frame = ttk.Frame(checkbox_canvas)

checkbox_scrollable_frame.bind("<Configure>", lambda e: checkbox_canvas.configure(scrollregion=checkbox_canvas.bbox("all")))
checkbox_canvas.create_window((0, 0), window=checkbox_scrollable_frame, anchor="nw")
checkbox_canvas.configure(yscrollcommand=checkbox_scrollbar.set)

checkbox_canvas.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=10)
checkbox_scrollbar.grid(row=3, column=2, sticky="ns", padx=(5, 0))
checkbox_frame = checkbox_scrollable_frame

output_text = tk.Text(main_frame, wrap=tk.WORD, height=20, bg="#fdfdfd", font=("Consolas", 10), relief="solid", bd=1)
output_text.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

main_frame.grid_rowconfigure(4, weight=1)
main_frame.grid_columnconfigure(1, weight=1)

root.mainloop()
