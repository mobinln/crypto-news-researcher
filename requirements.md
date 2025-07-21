# Crypto News Researcher - Requirements Draft

## Overview
A system for automated collection, AI-powered analysis, and interactive research of cryptocurrency news, with a planned Streamlit UI for user-friendly exploration.

## Functional Requirements

### 1. News Collection
- Fetch news articles from multiple crypto news sources (RSS feeds, APIs).
- Support for adding/removing news sources easily.
- Schedule background fetching (e.g., every 4 hours) and allow manual fetches.

### 2. Article Analysis
- Use OpenAI GPT models to analyze articles:
  - Generate concise summaries.
  - Perform sentiment analysis (Bullish/Bearish/Neutral).
  - Extract key topics and mentioned cryptocurrencies.
  - Assess market implications.
- Store both raw and structured analysis in a local database.

### 3. Database & Storage
- Store articles, metadata, and analysis in SQLite.
- Cache user queries and responses for efficiency.
- Ability to generate a full database for testing purposes.

### 4. Query & Research
- Allow users to query the news database using natural language.
- Return AI-generated answers based on recent news context.
- Provide statistics (e.g., total articles, articles by source, sentiment distribution).

### 5. User Interface (UI)
- Implement a web UI using Streamlit:
  - Dashboard for recent news, stats, and trends.
  - Search/query interface for natural language questions.
  - Article detail and analysis views.
  - Visualizations (e.g., sentiment over time, topic trends).
- (Optional) Authentication for user-specific features.

### 6. Extensibility
- Modular design to support new sources, analysis methods, or storage backends (e.g., vector DB).
- (Planned) Integration with markitdown for improved markdown rendering.
- (Planned) Option to save post-analysis in a database.
- (Planned) Setup and integration of a vector database for semantic search (optional).

## Non-Functional Requirements
- Easy setup and deployment (documented in README).
- Secure handling of API keys and sensitive data (via .env).
- Responsive UI and efficient background processing.
- Scalable to support more sources and larger datasets.

## TODOs (from README)
- Use markitdown for better markdown rendering.
- Save the post analysis in db.
- Generate a full db for testing.
- Setup a UI with Streamlit.
- Setup a vector db (maybe?).

## Dependencies
- Python 3.8+
- requests, feedparser, beautifulsoup4, openai, schedule, python-dotenv, sqlite3
- pandas, matplotlib (for data analysis/visualization)
- streamlit (for UI)
- (Optional) markitdown, vector DB libraries
