from flask import Flask, request, render_template
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from markupsafe import Markup
import concurrent.futures

app = Flask(__name__)

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

MAX_RESULTS = 15  # Increase the number of results to fetch
MIN_SUMMARIES = 5  # Minimum number of summaries needed for combined summary

def google_search(query):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def parse_search_results(html):
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    for g in soup.find_all('div', class_='tF2Cxc')[:MAX_RESULTS]:
        title = g.find('h3')
        title = title.text if title else 'No title found'
        link = g.find('a')['href']
        snippet = g.find('div', class_='VwiC3b')
        snippet = snippet.text if snippet else 'No snippet found'
        results.append({'title': title, 'link': link, 'snippet': snippet})
    return results

def fetch_and_summarize(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()
        return article.summary
    except Exception as e:
        print(f"Error fetching summary for {url}: {e}")
        return None

def highlight_important_sentences(text, query, num_sentences=3):
    sentences = sent_tokenize(text)
    words = nltk.word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.isalnum() and word not in stop_words]
    
    freq_dist = FreqDist(words)
    query_words = set(query.lower().split())
    
    def sentence_importance(sentence):
        sentence_words = set(word.lower() for word in nltk.word_tokenize(sentence) if word.isalnum())
        return sum(freq_dist[word] for word in sentence_words) + sum(5 for word in sentence_words if word in query_words)
    
    ranked_sentences = sorted([(sentence, sentence_importance(sentence)) for sentence in sentences], 
                              key=lambda x: x[1], reverse=True)
    
    highlighted_sentences = set(sentence for sentence, _ in ranked_sentences[:num_sentences])
    
    highlighted_text = []
    for sentence in sentences:
        if sentence in highlighted_sentences:
            highlighted_text.append(f'<mark class="highlight">{sentence}</mark>')
        else:
            highlighted_text.append(sentence)
    
    return ' '.join(highlighted_text)

def combine_summaries(summaries, query):
    combined_text = " ".join(summaries)
    if combined_text:
        parser = PlaintextParser.from_string(combined_text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary_sentences = summarizer(parser.document, 6)  # Summarize to 3 sentences
        summary = ' '.join([str(sentence) for sentence in summary_sentences])
        return highlight_important_sentences(summary, query)
    return "No useful summary available."

def filter_results(results):
    filtered_results = []
    for result in results:
        if "india" in result['snippet'].lower() or "buy & sell" in result['snippet'].lower() or "classified" in result['snippet'].lower():
            continue
        filtered_results.append(result)
    return filtered_results

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form["query"]
        html = google_search(query)
        results = parse_search_results(html)
        results = filter_results(results)
        summarized_results = []
        all_summaries = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_url = {executor.submit(fetch_and_summarize, result['link']): result for result in results}
            for future in concurrent.futures.as_completed(future_to_url):
                result = future_to_url[future]
                try:
                    summary = future.result()
                    if summary:
                        highlighted_summary = highlight_important_sentences(summary, query)
                        summarized_results.append({
                            'title': result['title'],
                            'link': result['link'],
                            'snippet': result['snippet'],
                            'summary': Markup(highlighted_summary)
                        })
                        all_summaries.append(summary)
                except Exception as e:
                    print(f"Error fetching summary for {result['link']}: {e}")

        if len(all_summaries) >= MIN_SUMMARIES:
            combined_summary = combine_summaries(all_summaries, query)
        else:
            combined_summary = "No useful summary available."
        print(f"Combined Summary: {combined_summary}")  # Debugging statement

        return render_template("index.html", 
                               results=summarized_results, 
                               query=query, 
                               combined_summary=Markup(combined_summary))
    
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
