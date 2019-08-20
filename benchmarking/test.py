from time import time
from urllib import request
from multiprocessing import Pool


def call(port):
    for _ in range(1000):
        request.urlopen(f"http://127.0.0.1:{port}")


if __name__ == "__main__":
    port = str(input("Port to call: "))
    thread_count = int(input("Number of threads to spawn: "))

    start = time()

    with Pool(thread_count):
        call(port)

    end = time()

    request_count = thread_count * 1000
    duration = end - start
    rps = request_count / duration

    print(f"Finished in {duration} at {rps} average requests per second.")
