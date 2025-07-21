import sqlite3
import requests
import feedparser
from bs4 import BeautifulSoup
import openai
from datetime import datetime
import schedule
import time
import json
import os
import logging

logger = logging.getLogger(__name__)


class CryptoNewsAnalyzer:
    def __init__(self):
        """Initialize the crypto news analyzer"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_api_base = os.getenv("OPENAI_API_BASE")

        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required")

        self.client = openai.OpenAI(
            api_key=self.openai_api_key, base_url=self.openai_api_base
        )
        self.db_path = "crypto_news.db"
        self.init_database()

        # News sources - RSS feeds and API endpoints
        self.news_sources = {
            # "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
            # "cointelegraph": "https://cointelegraph.com/rss",
            "decrypt": "https://decrypt.co/feed",
            "theblock": "https://www.theblock.co/rss.xml",
            "cryptonews": "https://cryptonews.com/news/feed/",
        }

    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create news articles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                content TEXT,
                summary TEXT,
                sentiment TEXT,
                impact TEXT,
                key_topics TEXT,
                related_coins TEXT,
                category TEXT,
                source TEXT,
                published_date DATETIME,
                fetched_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                analysis_raw TEXT
            )
        """)

        # Create analysis cache table for user queries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT UNIQUE,
                query TEXT,
                response TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    def fetch_news_from_rss(self, source_name, rss_url):
        """Fetch news articles from RSS feed"""
        articles = []
        try:
            feed = feedparser.parse(rss_url)
            logger.info(f"Fetched {len(feed.entries)} articles from {source_name}")

            for entry in feed.entries[:10]:  # Limit to 10 most recent articles
                # Parse published date
                published_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published_date = datetime(*entry.published_parsed[:6])

                article = {
                    "title": entry.title,
                    "url": entry.link,
                    "content": self.extract_article_content(entry.link),
                    "source": source_name,
                    "published_date": published_date,
                }
                articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching from {source_name}: {str(e)}")

        return articles

    def extract_article_content(self, url):
        """Extract full article content from URL"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Try to find main content
            content = ""
            for selector in [
                "article",
                ".article-content",
                ".post-content",
                "main",
                ".content",
            ]:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(strip=True)
                    break

            if not content:
                content = soup.get_text(strip=True)

            # Truncate if too long (for API limits)
            return content[:4000] if len(content) > 4000 else content

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return ""

    def analyze_article_with_llm(self, article):
        """Analyze article using OpenAI GPT"""
        try:
            prompt = f"""
            Analyze this cryptocurrency news article and provide:
            1. A concise summary (2-3 sentences)
            2. Sentiment analysis (Bullish/Bearish/Neutral)
            3. Key topics and cryptocurrencies mentioned
            4. Market implications (if any)
            
            Title: {article["title"]}
            Content: {article["content"][:3000]}
            
            Please format your response as JSON with keys: summary, sentiment, key_topics, market_implications
            """

            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cryptocurrency market analyst. Provide detailed analysis of crypto news articles.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )

            analysis_text = response.choices[0].message.content

            # Try to parse as JSON, fallback to text if it fails
            try:
                analysis = json.loads(analysis_text)
            except Exception:
                analysis = {"raw_analysis": analysis_text}

            return analysis

        except Exception as e:
            print(e)
            logger.error(f"Error analyzing article: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}

    def save_article_to_db(self, article, analysis):
        """Save analyzed article to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO news_articles 
                (title, url, content, summary, sentiment, key_topics, source, published_date, analysis_raw)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    article["title"],
                    article["url"],
                    article["content"],
                    analysis.get("summary", ""),
                    analysis.get("sentiment", ""),
                    json.dumps(analysis.get("key_topics", [])),
                    article["source"],
                    article["published_date"],
                    json.dumps(analysis),
                ),
            )

            conn.commit()
            logger.info(f"Saved article: {article['title'][:50]}...")

        except Exception as e:
            logger.error(f"Error saving article: {str(e)}")
        finally:
            conn.close()

    def fetch_and_analyze_news(self):
        """Main function to fetch and analyze news from all sources"""
        logger.info("Starting news fetch and analysis cycle")

        for source_name, rss_url in self.news_sources.items():
            logger.info(f"Processing {source_name}...")
            articles = self.fetch_news_from_rss(source_name, rss_url)

            for article in articles:
                if article["content"]:  # Only analyze if we have content
                    analysis = self.analyze_article_with_llm(article)
                    self.save_article_to_db(article, analysis)

                    # Small delay to avoid rate limiting
                    time.sleep(1)

        logger.info("News fetch and analysis cycle completed")

    def query_database(self, user_query):
        """Query the database and provide contextual answer"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Search for relevant articles based on keywords in the query
            search_terms = user_query.lower().split()

            # Build dynamic query to search in title, content, and analysis
            search_conditions = []
            params = []

            for term in search_terms:
                search_conditions.append(
                    "(LOWER(title) LIKE ? OR LOWER(content) LIKE ? OR LOWER(analysis) LIKE ?)"
                )
                params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])

            if search_conditions:
                where_clause = " AND ".join(search_conditions)
                query = f"""
                    SELECT title, url, summary, sentiment, key_topics, source, published_date, analysis
                    FROM news_articles 
                    WHERE {where_clause}
                    ORDER BY published_date DESC 
                    LIMIT 10
                """
            else:
                # If no specific terms, get recent articles
                query = """
                    SELECT title, url, summary, sentiment, key_topics, source, published_date, analysis
                    FROM news_articles 
                    ORDER BY published_date DESC 
                    LIMIT 10
                """
                params = []

            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()

            if not results:
                return (
                    "I couldn't find any relevant crypto news articles for your query."
                )

            # Prepare context for LLM
            context = "Recent cryptocurrency news articles:\n\n"
            for i, (
                title,
                url,
                summary,
                sentiment,
                key_topics,
                source,
                pub_date,
                analysis,
            ) in enumerate(results, 1):
                context += f"{i}. Title: {title}\n"
                context += f"   Source: {source}\n"
                context += f"   Published: {pub_date}\n"
                context += f"   Summary: {summary}\n"
                context += f"   Sentiment: {sentiment}\n"
                if key_topics:
                    try:
                        topics = json.loads(key_topics)
                        context += f"   Key Topics: {', '.join(topics) if isinstance(topics, list) else topics}\n"
                    except Exception:
                        pass
                context += f"   URL: {url}\n\n"

            # Generate response using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cryptocurrency expert. Answer user questions based on the provided recent news articles. Be comprehensive and cite specific articles when relevant.",
                    },
                    {
                        "role": "user",
                        "content": f"Based on these recent crypto news articles, please answer this question: {user_query}\n\nNews Context:\n{context}",
                    },
                ],
                temperature=0.4,
                max_tokens=1000,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error querying database: {str(e)}")
            return (
                f"Sorry, I encountered an error while processing your query: {str(e)}"
            )

    def start_scheduler(self):
        """Start the background scheduler for periodic news fetching"""
        # Schedule news fetching every 4 hours
        schedule.every(4).hours.do(self.fetch_and_analyze_news)

        # Also run once immediately
        self.fetch_and_analyze_news()

        logger.info("Started news fetching scheduler (every 4 hours)")

        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def get_database_stats(self):
        """Get statistics about the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM news_articles")
        total_articles = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM news_articles WHERE DATE(fetched_date) = DATE('now')"
        )
        today_articles = cursor.fetchone()[0]

        cursor.execute("SELECT source, COUNT(*) FROM news_articles GROUP BY source")
        source_stats = cursor.fetchall()

        conn.close()

        return {
            "total_articles": total_articles,
            "articles_today": today_articles,
            "articles_by_source": dict(source_stats),
        }
