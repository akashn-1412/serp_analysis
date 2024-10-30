from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Fetch location data on startup
COUNTRIES_API_URL = 'https://restcountries.com/v3.1/all'
SERP_API_KEY = '59f0a74669d9773027ad5727559d34cf50167ae99f0b2b69a8db8c56819023e4'  # Replace with your actual API key
SERP_API_URL = 'https://serpapi.com/search.json'

def fetch_countries():
    try:
        response = requests.get(COUNTRIES_API_URL)
        response.raise_for_status()
        countries_data = response.json()
        return [{'code': country['cca2'].lower(), 'name': country['name']['common']} for country in countries_data]
    except Exception as e:
        print("Error fetching countries:", e)
        return []

# Load countries on server start
countries = fetch_countries()

@app.route('/')
def index():
    return render_template('index.html', countries=countries)

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query')
    website = data.get('website')
    selected_country_code = data.get('country_code')
    website_position = None
    
    if not query or not selected_country_code:
        return jsonify({"error": "Please select a location and enter a search query."}), 400

    # Prepare and send the SERP API request
    params = {
        'api_key': SERP_API_KEY,
        'q': query,
        'gl': selected_country_code,
        'hl': 'en'
    }
    try:
        serp_response = requests.get(SERP_API_URL, params=params)
        serp_response.raise_for_status()
        results = serp_response.json()
        
        normalized_website = normalize_website_url(website)
        normalized_result_website = normalized_website.replace('www.', '')

        # Find website position in SERP results
        for index, result in enumerate(results.get('organic_results', [])):
            result_link = result['link'].replace('www.', '')
            if normalized_result_website in result_link:
                website_position = index + 1
                break

        return jsonify({
            "results": results.get('organic_results', []),
            "website_position": website_position
        })
    except Exception as e:
        print("Error fetching SERP data:", e)
        return jsonify({"error": "Failed to fetch results. Please try again."}), 500

def normalize_website_url(url):
    url = url.strip().lower()
    if not url.startswith('http'):
        url = 'https://' + url
    return url

if __name__ == '__main__':
    app.run(debug=True)
