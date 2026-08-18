from app.database import SessionLocal

from app.ingestion.engine import IngestionEngine
from app.sources.public_source import PublicJobSource
from app.sources.remoteok_source import RemoteOKJobSource


def main():

    primary = PublicJobSource()

    fallback = RemoteOKJobSource()

    engine = IngestionEngine(
        sources=[
            primary,
            fallback,
        ]
    )

    session = SessionLocal()

    try:

        run = engine.run(session)

        print("\nINGESTION RESULT")
        print("----------------")
        print("Run ID:", run.id)
        print("Source:", run.source)
        print("Status:", run.status)
        print("Fetched:", run.records_fetched)
        print("Inserted:", run.records_inserted)
        print("Skipped:", run.records_skipped)

        if run.error:
            print("Error:", run.error)

    finally:
        session.close()


if __name__ == "__main__":
    main()