from bs4 import BeautifulSoup
from transformers import pipeline
import requests
from sentence_transformers import SentenceTransformer, util
import io
from gtts import gTTS
from googletrans import Translator
from fastapi.responses import StreamingResponse
from logging_config import logger
import base64

logger.info(f"loading all models")

text_model=pipeline("text-generation",model="gpt2")
sentiment_pipeline= pipeline("sentiment-analysis")
embedding_model= SentenceTransformer("all-MiniLM-L6-v2")
impact_model=pipeline("text-generation",model="EleutherAI/gpt-neo-1.3B")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


def extract_topics(description):
    logger.info("Topics extraction started")
    prompt = f"What are the main topics in this text? {description}\nTopics:"
    topics = text_model(prompt, max_new_tokens=20, num_return_sequences=1)[0]["generated_text"].split("Topics:")[1].strip()
    return topics.split(",")

def sentiment_analysis(news_data):
    logger.info("Sentiment analysis started")
    for article in news_data:
        result= sentiment_pipeline(article["description"])[0]
        article["sentiment"]= result["label"]
        article["score"]= result["score"]
    return news_data

def analyze_impact(desc1,desc2):
    logger.info("Impact analysis started")
    prompt=(
        f"""Analyze the following two news articles and predict their impact based on the given information.  
          Do not assume or add any extra details beyond what is provided.  

          Articles:  
          1. {desc1}  
          2. {desc2}  

          Based on these articles alone, provide a short and clear impact statement.  
          **Do not repeat the articles or prompt**  

          Impact:""")


    try:
        response = impact_model(prompt, max_new_tokens=100, truncation=True)[0]["generated_text"]
        
        impact_response = response.split("Impact:")[-1].strip()

        impact_response = re.sub(r"\*\*.*?\*\*", "", impact_response).strip()  
        impact_response = re.sub(r"\s+", " ", impact_response)  

        # Ensure structured response
        if len(impact_response.split(".")) > 1:  
            impact_response = impact_response.split(".")[0] + "."  

        return impact_response
    except Exception as e:
        return f"Impact is Unavailable{e}"
    


def extract_details_from_website(company_name):
    logger.info("Extracting details from website")

    classifier= pipeline("sentiment-analysis")

    url=f"https://economictimes.indiatimes.com/topic/{company_name}"
    response = requests.get(url)
    soup= BeautifulSoup(response.text, "html.parser")

    articles = soup.find_all("div",class_="clr flt topicstry story_list")
    news_data=[]

    for article in articles[:3]:
        title_element=article.find("h2").find("a")
        if title_element:
            title=title_element.get_text(strip=True)
        else:
            title="NO title found from the article"
        
        link_element= article.find("a",class_="wrapLines l2")
        if link_element:
            link= link_element.get("href")

            if not link.startswith("http"):
                link="https://economictimes.indiatimes.com"+link
        else:
            link= None
        
        description ="No Content available to extract"
        description_tag = article.find("p", class_="wrapLines l3")
        description = description_tag.text.strip() if description_tag else "No content available."
        topics = extract_topics(description)


        news_data.append({"title":title,"link":link,"description":description,"Topics":topics})

        sentiment_analysis(news_data)
        logger.info("All Articles extracted and stored")
    return news_data

def compare_articles(articles):
    logger.info("articles comparision started")
    sentiment_counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    for article in articles:
        sentiment_counts[article["sentiment"]] += 1
    
    coverage_differences=[]
    embeddings= embedding_model.encode([article["description"] for article in articles], convert_to_tensor=True)
    topics_overlap=[]
    for i in range(len(articles)):
        for j in range(i+1,len(articles)):
            desc1= articles[i]["description"]
            desc2= articles[j]["description"]

            common_topics = set(articles[i]["Topics"]) & set(articles[j]["Topics"])
            unique_topics_1 = set(articles[i]["Topics"]) - set(articles[j]["Topics"])
            unique_topics_2 = set(articles[j]["Topics"]) - set(articles[i]["Topics"])
            
            cos_similarity= util.pytorch_cos_sim(embeddings[i],embeddings[j]).item()

            impact= analyze_impact(desc1,desc2)

            coverage_differences.append({
                "Comparison": f"similarity score between articles:{cos_similarity}",
                "Impact": impact
            })

            topics_overlap.append({
                "Topic Overlap":{
                    "Common Topics": list(common_topics),
                    "Unique Topics in Article 1":list(unique_topics_1),
                    "Unique Topics in Artivle 2": list(unique_topics_2)
                }
            })
    if sentiment_counts["POSITIVE"]> sentiment_counts["NEGATIVE"]:
        final_sentiment=f"Overall the news is postive. Potential stock growth expected"
    elif sentiment_counts["NEGATIVE"]> sentiment_counts["POSITIVE"]:
        final_sentiment=f"Overall, the news coverage is negative, which may impact stock growth and performance"
    else:
        final_sentiment=f"Overall, the sentiment is mixed in the news coverage.Anything may stike up suddenly"
    logger.info("COmparision and Final sentiment Analysis started")
    return {
        "Comparative Sentiment Score": {
            "Sentiment Distribution": sentiment_counts,
            "Coverage Differences": coverage_differences,
            "Topic Overlap": topics_overlap
        },
        "Final Sentiment Analysis": final_sentiment
    }


# Convert the string to Hindi audio
def convert_to_hindi_audio(text):
    translator = Translator()
    translated_text = translator.translate(text, src='en', dest='hi').text
    tts = gTTS(text=translated_text, lang='hi')

    audio_stream = io.BytesIO()
    tts.write_to_fp(audio_stream)
    audio_stream.seek(0)

    # Convert to Base64
    audio_base64 = base64.b64encode(audio_stream.read()).decode("utf-8")
    return audio_base64

def merge_results(company):
    news_articles=extract_details_from_website(company)
    print(news_articles)
    comparison_articles=compare_articles(news_articles)
    print(comparison_articles)
    return {
        "Company": company,
        "Articles": news_articles,
        "Coverage Differences": comparison_articles
                }
    



def summarize_news(news_data):
    text = f"we are talking about news of {news_data['Company']} company "
    
    for article in news_data["Articles"]:
        text += f"{article['title']}: {article['description']} "
    
    text += f"Overall Sentiment: {news_data['Coverage Differences']['Final Sentiment Analysis']}."
    
    summary = summarizer(text,max_new_tokens=150, truncation=True, do_sample=False)[0]['summary_text']
    
    return summary
