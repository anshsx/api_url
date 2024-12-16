from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def scrape_google(query):
    """Scrape Google search results."""
    query = query.replace(" ", "+")
    url = f"https://www.google.com/search?q={query}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for g in soup.find_all('div', class_='tF2Cxc'):
            title = g.find('h3').text if g.find('h3') else None
            link = g.find('a')['href'] if g.find('a') else None
            if link:
                results.append({'title': title, 'link': link})
        return results
    except Exception as e:
        print(f"Error scraping Google: {e}")
        return []

def scrape_bing(query):
    """Scrape Bing search results."""
    query = query.replace(" ", "+")
    url = f"https://www.bing.com/search?q={query}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for li in soup.find_all('li', class_='b_algo'):
            title = li.find('h2').text if li.find('h2') else None
            link = li.find('a')['href'] if li.find('a') else None
            if link:
                results.append({'title': title, 'link': link})
        return results
    except Exception as e:
        print(f"Error scraping Bing: {e}")
        return []

def deduplicate_results(results):
    """Remove duplicate URLs based on the base domain."""
    seen_domains = set()
    unique_results = []

    for result in results:
        url = result['link']
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"  # Extract base domain
        if domain not in seen_domains:
            seen_domains.add(domain)
            unique_results.append(result)

    return unique_results

@app.route('/search', methods=['GET'])
def search_combined():
    """API endpoint for combined search."""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    google_results = scrape_google(query)
    if google_results:
        results = google_results
    else:
        print("Google scraping failed, trying Bing...")
        results = scrape_bing(query)

    if results:
        unique_results = deduplicate_results(results)
        return jsonify({"results": unique_results})
    else:
        print("Both Google and Bing failed to provide results.")
        return jsonify({"results": []}), 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
