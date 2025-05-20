import json
import time
from playwright.sync_api import sync_playwright

def scrape_google_data(keyword, page):
    results = {
        "keyword": keyword,
        "auto_suggest": [],
        "people_also_ask": [],
        "people_also_search_for": []
    }

    # Get auto-suggest using Google's API
    page.goto(f"https://suggestqueries.google.com/complete/search?client=firefox&q={keyword}")
    json_data = page.content()
    if '["' in json_data:
        try:
            suggestions = eval(json_data.split('>', 1)[-1].split('<')[0])
            results["auto_suggest"] = suggestions[1]
        except Exception:
            pass

    # Search Google and get People Also Ask / Search For
    page.goto("https://www.google.com/")
    page.fill("input[name='q']", keyword)
    page.keyboard.press("Enter")
    page.wait_for_selector("#search", timeout=10000)

    # People Also Ask
    paa_elements = page.query_selector_all("div[jsname='Cpkphb']")
    results["people_also_ask"] = [el.inner_text() for el in paa_elements if el.inner_text()]

    # Scroll and collect People Also Search For
    page.evaluate("window.scrollBy(0, 2000)")
    page.wait_for_timeout(3000)
    pasf_elements = page.query_selector_all("a[href^='/search']")
    unique_texts = set()
    for el in pasf_elements:
        text = el.inner_text().strip()
        if text and text.lower() != keyword.lower() and len(text.split()) >= 2:
            unique_texts.add(text)
    results["people_also_search_for"] = list(unique_texts)

    return results

def main():
    with open("keywords.txt", "r") as f:
        keywords = [line.strip() for line in f if line.strip()]

    output = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for keyword in keywords:
            print(f"Scraping: {keyword}")
            try:
                data = scrape_google_data(keyword, page)
                output.append(data)
                time.sleep(2)  # polite delay
            except Exception as e:
                print(f"Error scraping '{keyword}': {e}")

        browser.close()

    with open("output.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()
