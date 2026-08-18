from app.sources.remoteok_source import RemoteOKJobSource


def main():

    source = RemoteOKJobSource()

    jobs = source.fetch()

    print("Jobs fetched:", len(jobs))

    for job in jobs[:5]:

        print("\n--------------------")
        print("ID:", job["external_id"])
        print("Title:", job["title"])
        print("Company:", job["company"])
        print("Location:", job["location"])
        print("URL:", job["url"])
        print("Source:", job["source"])


if __name__ == "__main__":
    main()