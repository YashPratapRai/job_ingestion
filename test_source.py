from app.sources.public_source import PublicJobSource


def main():
    source = PublicJobSource()
    jobs = source.fetch()

    print(f"Jobs fetched: {len(jobs)}")

    print("\nRAW FIRST JOB:")
    print(jobs[0])


if __name__ == "__main__":
    main()