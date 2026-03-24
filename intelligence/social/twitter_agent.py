"""ARK95X Twitter/X Intelligence Agent
Real-time social intel collection from X platform.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

try:
    import tweepy
except ImportError:
    tweepy = None

logger = logging.getLogger(__name__)


class TwitterIntelAgent:
    """Collects and analyzes public Twitter/X data for intelligence."""

    def __init__(self):
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN", "")
        self.client = None
        if tweepy and self.bearer_token:
            self.client = tweepy.Client(bearer_token=self.bearer_token)

    def search_recent(self, query: str, max_results: int = 100) -> list:
        """Search recent tweets with advanced operators."""
        if not self.client:
            logger.warning("Twitter client not initialized")
            return []
        try:
            response = self.client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),
                tweet_fields=["created_at", "public_metrics", "geo", "lang"],
                user_fields=["username", "public_metrics", "verified"],
                expansions=["author_id"]
            )
            return self._parse_tweets(response)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def monitor_keywords(self, keywords: list) -> dict:
        """Monitor multiple keywords and return aggregated results."""
        results = {}
        for kw in keywords:
            results[kw] = self.search_recent(kw)
        return results

    def profile_analysis(self, username: str) -> dict:
        """Analyze a public user profile."""
        if not self.client:
            return {}
        try:
            user = self.client.get_user(
                username=username,
                user_fields=["public_metrics", "description", "created_at", "verified"]
            )
            if user.data:
                return {
                    "username": user.data.username,
                    "followers": user.data.public_metrics["followers_count"],
                    "following": user.data.public_metrics["following_count"],
                    "tweets": user.data.public_metrics["tweet_count"],
                    "description": user.data.description,
                    "created": str(user.data.created_at),
                    "verified": user.data.verified
                }
        except Exception as e:
            logger.error(f"Profile analysis failed: {e}")
        return {}

    def sentiment_scan(self, query: str) -> dict:
        """Basic sentiment analysis on search results."""
        tweets = self.search_recent(query, max_results=50)
        if not tweets:
            return {"positive": 0, "negative": 0, "neutral": 0}
        positive = sum(1 for t in tweets if t.get("likes", 0) > 10)
        total = len(tweets)
        return {
            "total": total,
            "high_engagement": positive,
            "engagement_rate": round(positive / total * 100, 1) if total else 0,
            "query": query,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _parse_tweets(self, response) -> list:
        """Parse tweepy response into clean dicts."""
        if not response or not response.data:
            return []
        tweets = []
        for tweet in response.data:
            tweets.append({
                "id": tweet.id,
                "text": tweet.text,
                "created_at": str(tweet.created_at),
                "likes": tweet.public_metrics.get("like_count", 0),
                "retweets": tweet.public_metrics.get("retweet_count", 0),
                "replies": tweet.public_metrics.get("reply_count", 0)
            })
        return tweets


if __name__ == "__main__":
    agent = TwitterIntelAgent()
    print("Twitter Intel Agent initialized")
    print(f"Client active: {agent.client is not None}")
