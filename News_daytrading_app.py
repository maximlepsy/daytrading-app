import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob
from langdetect import detect
import requests

# -----------------------
# Sentiment-Funktion
# -----------------------
def analyze_sentiment(text):
    try:
        if detect(text) != "en":
            return 0.0  # Nicht-englische News ignorieren
        return TextBlob(text).sentiment.polarity
    except:
        return 0.0

# -----------------------
# Aktienliste (~100, US & EU Liquiditätsaktien)
# -----------------------
all_stocks = [
    "AAPL","MSFT","AMZN","GOOGL","META","TSLA","NVDA","NFLX","PYPL","ADBE",
    "INTC","AMD","CSCO","ORCL","CRM","IBM","UBER","LYFT","SHOP","SQ",
    "BA","NKE","DIS","V","MA","JPM","BAC","GS","C","WFC",
    "KO","PEP","MCD","SBUX","PG","JNJ","PFE","MRK","ABBV","GILD",
    "T","VZ","XOM","CVX","BP","TOT","RDS.A","DOW","BHP","RIO",
    "SAP","SIE","BMW","ALV","DAI","VOW3","BAYN","NESN","ROG","ULVR",
    "ZM","TWTR","SNAP","DOCU","SHOP","SQ","UBS","BN","DTE","CVS",
    "COST","F","GM","HD","LOW","AMGN","CSX","FDX","CAT","MMM",
    "ADP","ACN","NOW","LIN","LMT","BA","HON","RTX","GE","SPGI",
    "BLK","AXP","GS","ORCL","INTU","ISRG","AMAT","MU","QCOM","TSM",
    "SHOP","ZM","PYPL","DOCU","CRM","TEAM","TWLO","OKTA","SNOW","ROKU"
]

st.title("News + Daytrading Übersicht mit Super-Score (~100 Aktien)")

results = []

# -----------------------
# Hauptschleife: jede Aktie analysieren
# -----------------------
for stock in all_stocks:
    st.header(stock)

    # 📈 Kursdaten
    data = yf.download(stock, period="5d", interval="1h")

    if data.empty or "Close" not in data.columns:
        st.write("Keine Daten verfügbar")
        continue

    close_prices = data["Close"].dropna()

    if len(close_prices) < 6:
        st.write("Zu wenig Kursdaten")
        continue

    # -----------------------
    # Technischer Score
    # -----------------------
    volatility = close_prices.pct_change().std()
    momentum = float(close_prices.iloc[-1]) / float(close_prices.iloc[-5])
    tech_score = float(volatility) * float(momentum)

    # -----------------------
    # News abrufen (englisch)
    # -----------------------
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": stock,
        "apiKey": "AIzaSyCUQE6exeixg7RchDNvr9q-cnE4eqg1mZI",  # <-- hier deinen NewsAPI Key einfügen
        "pageSize": 5,
        "language": "en",
        "sortBy": "publishedAt"
    }
    response = requests.get(url, params=params)
    data_news = response.json()
    articles = data_news.get("articles", [])

    sentiment_total = 0
    news_list = []

    for article in articles:
        title = article.get("title", "")
        sentiment = analyze_sentiment(title)
        sentiment_total += sentiment
        news_list.append({"Titel": title, "Sentiment": round(sentiment,3)})

    # Durchschnittliches Sentiment
    avg_sentiment = sentiment_total / max(len(articles),1)

    # -----------------------
    # Super-Score berechnen
    # -----------------------
    super_score = tech_score * (1 + avg_sentiment)

    # -----------------------
    # Empfehlung ableiten
    # -----------------------
    if super_score > 0.01:
        recommendation = "Kaufen möglich"
    elif super_score > 0.005:
        recommendation = "Neutral / Vorsicht"
    else:
        recommendation = "Nicht handeln"

    # -----------------------
    # Ergebnisse speichern
    # -----------------------
    results.append({
        "Aktie": stock,
        "Super-Score": round(super_score,5),
        "Technischer Score": round(tech_score,5),
        "News-Sentiment": round(avg_sentiment,3),
        "Empfehlung": recommendation
    })

# -----------------------
# Ergebnisse sortieren nach Super-Score
# -----------------------
results_sorted = sorted(results, key=lambda x: x["Super-Score"], reverse=True)

# -----------------------
# Streamlit Tabelle
# -----------------------
st.subheader("Rangliste aller Aktien")
st.table(pd.DataFrame(results_sorted))

# -----------------------
# Charts für jede Aktie
# -----------------------
for r in results_sorted:
    stock = r["Aktie"]
    st.subheader(f"Chart: {stock}")
    data = yf.download(stock, period="5d", interval="1h")
    st.line_chart(data["Close"])
