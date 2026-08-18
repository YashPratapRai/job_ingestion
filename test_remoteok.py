import httpx


URL = "https://remoteok.com/api"


response = httpx.get(
    URL,
    timeout=20,
    follow_redirects=True,
    headers={
        "User-Agent": "JobIngestionDemo/1.0"
    },
)

print("Status:", response.status_code)
print("Content-Type:", response.headers.get("content-type"))
print("Response size:", len(response.content))

data = response.json()

print("Records:", len(data))

for job in data[:3]:
    if isinstance(job, dict):
        print("\n----------------")
        print("Title:", job.get("position"))
        print("Company:", job.get("company"))
        print("Location:", job.get("location"))
        print("URL:", job.get("url"))