import feedparser
import httpx


URL = "https://himalayas.app/jobs/rss"


response = httpx.get(
    URL,
    timeout=20,
    follow_redirects=True,
    headers={
        "User-Agent": "JobIngestionDemo/1.0"
    },
)

response.raise_for_status()

feed = feedparser.parse(response.content)

print("Feed entries:", len(feed.entries))

entry = feed.entries[0]

print("\nENTRY KEYS:")
for key in entry.keys():
    print(key)

print("\nFULL ENTRY:")
for key, value in entry.items():
    print(f"\n--- {key} ---")
    print(value)