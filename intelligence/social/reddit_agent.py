"""ARK95X Reddit Intelligence Agent
Subreddit monitoring, sentiment scoring, anomaly detection.
"""
import os
import logging
from datetime import datetime

try:
    import praw
except ImportError:
    praw = None

logger = logging.getLogger(__name__)


class RedditIntelAgent:
    """Monitors subreddits and analyzes community sentiment."""

    WATCH_SUBS = ["stocks", "wallstreetbets", "crypto", "OSINT",
                  "technology", "artificial", "LocalLLaMA"]

    def __init__(self):
        self.reddit = None
        if praw:
            client_id = os.getenv("REDDIT_CLIENT_ID", "")
            client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
            if client_id and client_secret:
                self.reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent="ARK95X-Intel/1.0"
                )

    def scan_subreddit(self, sub_name: str, limit: int = 25) -> list:
        """Get hot posts from a subreddit."""
        if not self.reddit:
            return []
        try:
            sub = self.reddit.subreddit(sub_name)
            posts = []
            for post in sub.hot(limit=limit):
                posts.append({
                    "title": post.title,
                    "score": post.score,
                    "upvote_ratio": post.upvote_ratio,
                    "num_comments": post.num_comments,
                    "url": post.url,
                    "created": datetime.fromtimestamp(post.created_utc).isoformat(),
                    "author": str(post.author),
                    "is_self": post.is_self
                })
            return posts
        except Exception as e:
            logger.error(f"Subreddit scan failed: {e}")
            return []

    def scan_all_watched(self) -> dict:
        """Scan all watched subreddits."""
        results = {}
        for sub in self.WATCH_SUBS:
            results[sub] = self.scan_subreddit(sub)
        return results

    def detect_anomalies(self, sub_name: str) -> list:
        """Find posts with unusual engagement patterns."""
        posts = self.scan_subreddit(sub_name, limit=50)
        if not posts:
            return []
        avg_score = sum(p["score"] for p in posts) / len(posts)
        return [p for p in posts if p["score"] > avg_score * 3]

    def keyword_search(self, query: str, sub_name: str = "all") -> list:
        """Search Reddit for specific keywords."""
        if not self.reddit:
            return []
        try:
            results = []
            for post in self.reddit.subreddit(sub_name).search(query, limit=25):
                results.append({
                    "title": post.title,
                    "subreddit": str(post.subreddit),
                    "score": post.score,
                    "url": post.url,
                    "created": datetime.fromtimestamp(post.created_utc).isoformat()
                })
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []


if __name__ == "__main__":
    agent = RedditIntelAgent()
    print("Reddit Intel Agent initialized")
    print(f"Client active: {agent.reddit is not None}")
