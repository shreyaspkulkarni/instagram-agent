"""
One-time script — scrapes top 10 image posts per account for RAG seeding.
Run once, saves to data/instagram_examples_raw.json. Never needs to run again.
"""
import json
import os
from collections import Counter
from pathlib import Path

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
APIFY_TOKEN = os.getenv("APIFY_API_TOKEN", "")

ACCOUNTS = ["joshuacoppen", "mencrucials", "alexcosta", "rohit_khandelwal77", "sankett25"]
SCRAPE_LIMIT = 50   # fetch 50 per account to have enough pool
TOP_N = 10          # keep only top 10 images by engagement
OUTPUT = Path("data/instagram_examples_raw.json")


def engagement_tier(likes: int) -> str:
    if likes >= 10_000:
        return "VIRAL"
    elif likes >= 1_000:
        return "HIGH"
    else:
        return "SOLID"


def scrape_account(client: ApifyClient, username: str) -> list[dict]:
    print(f"\nScraping @{username}...")

    run = client.actor("apify/instagram-scraper").call(run_input={
        "directUrls": [f"https://www.instagram.com/{username}/"],
        "resultsType": "posts",
        "resultsLimit": SCRAPE_LIMIT,
        "addParentData": False,
    })

    images = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        # Images and carousels only — skip videos and reels
        post_type = (item.get("type") or "").lower()
        if post_type not in ("image", "sidecar"):
            continue

        caption = (item.get("caption") or "").strip()
        if not caption:
            continue

        likes = item.get("likesCount") or 0
        comments = item.get("commentsCount") or 0

        images.append({
            "account": username,
            "type": post_type,
            "likes": likes,
            "comments": comments,
            "engagement": likes + comments,
            "engagement_tier": engagement_tier(likes),
            "caption": caption,
            "hashtags": item.get("hashtags") or [],
            "post_url": item.get("url") or "",
            "timestamp": item.get("timestamp") or "",
        })

    # Sort by total engagement, keep top N
    images.sort(key=lambda x: x["engagement"], reverse=True)
    top = images[:TOP_N]

    print(f"  {len(images)} images found → keeping top {len(top)}")
    for p in top:
        print(f"  [{p['engagement_tier']:5s}] {p['likes']:>6} likes — {p['caption'][:70].strip()}...")

    return top


def main():
    client = ApifyClient(APIFY_TOKEN)

    all_posts = []
    for username in ACCOUNTS:
        posts = scrape_account(client, username)
        all_posts.extend(posts)

    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, indent=2, ensure_ascii=False)

    tiers = Counter(p["engagement_tier"] for p in all_posts)
    print(f"\n✅ Saved {len(all_posts)} posts to {OUTPUT}")
    print(f"   Engagement breakdown: {dict(tiers)}")
    print(f"   Accounts: {len(ACCOUNTS)} | Posts per account: {TOP_N}")


if __name__ == "__main__":
    main()
