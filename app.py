import streamlit as st
from crypto_news_analyzer import CryptoNewsAnalyzer
import pandas as pd
import time
import sqlite3

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Crypto News Researcher", layout="wide")

@st.cache_resource(show_spinner=False)
def get_analyzer():
    return CryptoNewsAnalyzer()

analyzer = get_analyzer()

st.title("🚀 Crypto News Deep Research System")
tabs = st.tabs(["Dashboard", "Manual News Fetch", "Query News", "Article Browser"])

# --- Dashboard Tab ---
with tabs[0]:
    st.header("📊 Database Statistics")
    try:
        stats = analyzer.get_database_stats()
        st.metric("Total Articles", stats["total_articles"])
        st.metric("Articles Fetched Today", stats["articles_today"])
        st.subheader("Articles by Source")
        st.bar_chart(pd.DataFrame(list(stats["articles_by_source"].items()), columns=["Source", "Count"]).set_index("Source"))
    except Exception as e:
        st.error(f"Error loading stats: {e}")

# --- Manual News Fetch Tab ---
with tabs[1]:
    st.header("🔄 Manual News Fetch")
    if st.button("Fetch and Analyze News Now"):
        with st.spinner("Fetching and analyzing news..."):
            try:
                analyzer.fetch_and_analyze_news()
                st.success("Manual fetch completed!")
            except Exception as e:
                st.error(f"Error during fetch: {e}")

# --- Query News Tab ---
with tabs[2]:
    st.header("💬 Query Crypto News")
    user_query = st.text_input("Ask a question about crypto news:", "What are the latest trends in Bitcoin?")
    if st.button("Get AI-Powered Answer") and user_query.strip():
        with st.spinner("Analyzing news and generating answer..."):
            try:
                response = analyzer.query_database(user_query)
                st.markdown(response)
            except Exception as e:
                st.error(f"Error during query: {e}")

# --- Article Browser Tab ---
with tabs[3]:
    st.header("📰 Recent Articles")
    try:
        # Show recent articles from DB
        conn = sqlite3.connect(analyzer.db_path)
        df = pd.read_sql_query(
            "SELECT id, title, summary, sentiment, key_topics, source, published_date, url FROM news_articles ORDER BY published_date DESC LIMIT 20",
            conn
        )
        conn.close()
        if not df.empty:
            for idx, row in df.iterrows():
                with st.expander(f"{row['title']} ({row['source']}, {row['published_date']})"):
                    st.write(f"**Summary:** {row['summary']}")
                    st.write(f"**Sentiment:** {row['sentiment']}")
                    st.write(f"**Key Topics:** {row['key_topics']}")
                    st.write(f"[Read original article]({row['url']})")
        else:
            st.info("No articles found in the database.")
    except Exception as e:
        st.error(f"Error loading articles: {e}") 