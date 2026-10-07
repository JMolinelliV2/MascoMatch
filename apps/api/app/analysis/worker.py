from rq import SpawnWorker
from rq.serializers import JSONSerializer

from app.analysis.queue import get_queue


def main() -> None:
    queue = get_queue()
    SpawnWorker([queue], connection=queue.connection, serializer=JSONSerializer).work()


if __name__ == "__main__":
    main()
