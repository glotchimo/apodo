from time import time
from urllib import request
from multiprocessing import Pool


def call():
    for _ in range(1000):
        request.urlopen("http://127.0.0.1:7777")


if __name__ == "__main__":
    thread_count = int(input("Number of threads to spawn: "))

    start = time()

    with Pool(thread_count):
        call()

    end = time()

    request_count = thread_count * 1000
    duration = end - start
    rps = request_count / duration

    print(f"Finished in {duration} at {rps} average requests per second.")
