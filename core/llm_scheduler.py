import threading
import queue
import time

task_queue = queue.Queue()
lock = threading.Lock()

OLLAMA_BUSY = False


def worker_loop():
    global OLLAMA_BUSY

    while True:

        task = task_queue.get()

        if task is None:
            continue

        func, args, kwargs, result_holder = task

        with lock:
            OLLAMA_BUSY = True

            try:
                result_holder["result"] = func(*args, **kwargs)

            except Exception as e:
                result_holder["error"] = str(e)

            finally:
                OLLAMA_BUSY = False

        task_queue.task_done()


# inicia worker único
threading.Thread(target=worker_loop, daemon=True).start()


def run_llm_safely(func, *args, **kwargs):

    result_holder = {"result": None, "error": None}

    task_queue.put((func, args, kwargs, result_holder))

    # espera execução terminar
    while result_holder["result"] is None and result_holder["error"] is None:
        time.sleep(0.05)

    if result_holder["error"]:
        raise Exception(result_holder["error"])

    return result_holder["result"]