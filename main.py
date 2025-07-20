import threading
from dotenv import load_dotenv
import logging

from crypto_news_analyzer import CryptoNewsAnalyzer


load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CryptoNewsCLI:
    """Command Line Interface for the Crypto News System"""

    def __init__(self):
        self.analyzer = CryptoNewsAnalyzer()
        self.scheduler_thread = None

    def start_background_fetching(self):
        """Start background news fetching in a separate thread"""
        if not self.scheduler_thread or not self.scheduler_thread.is_alive():
            self.scheduler_thread = threading.Thread(
                target=self.analyzer.start_scheduler, daemon=True
            )
            self.scheduler_thread.start()
            print("✅ Background news fetching started (every 4 hours)")
        else:
            print("ℹ️  Background fetching is already running")

    def manual_fetch(self):
        """Manually trigger news fetching"""
        print("🔄 Starting manual news fetch...")
        self.analyzer.fetch_and_analyze_news()
        print("✅ Manual fetch completed")

    def query_news(self):
        """Interactive news querying"""
        while True:
            query = input("\n💬 Ask me about crypto news (or 'quit' to exit): ").strip()
            if query.lower() in ["quit", "exit", "q"]:
                break

            if not query:
                continue

            print("🤔 Analyzing news to answer your question...")
            response = self.analyzer.query_database(query)
            print(f"\n📰 Answer:\n{response}\n")

    def show_stats(self):
        """Show database statistics"""
        stats = self.analyzer.get_database_stats()
        print("\n📊 Database Statistics:")
        print(f"Total articles: {stats['total_articles']}")
        print(f"Articles fetched today: {stats['articles_today']}")
        print("\nArticles by source:")
        for source, count in stats["articles_by_source"].items():
            print(f"  {source}: {count}")

    def run(self):
        """Main CLI loop"""
        print("🚀 Crypto News Deep Research System")
        print("=" * 40)

        while True:
            print("\nOptions:")
            print("1. Start background news fetching")
            print("2. Manual news fetch")
            print("3. Query crypto news")
            print("4. Show database stats")
            print("5. Quit")

            choice = input("\nSelect option (1-5): ").strip()

            if choice == "1":
                self.start_background_fetching()
            elif choice == "2":
                self.manual_fetch()
            elif choice == "3":
                self.query_news()
            elif choice == "4":
                self.show_stats()
            elif choice == "5":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option, please try again")


if __name__ == "__main__":
    try:
        cli = CryptoNewsCLI()
        cli.run()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("Please make sure you have set your OPENAI_API_KEY in the .env file.")
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
