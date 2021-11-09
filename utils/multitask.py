import multiprocessing as mp
import threading

method = 'fork' if 'fork' in mp.get_all_start_methods() else mp.get_all_start_methods()[0]
ctx = mp.get_context(method=method)
thread_id = 1000


def display_calling_process(source=''):
    print(source)


class MyThread(threading.Thread):
    def __init__(self, name, callback, params=None):
        global thread_id
        threading.Thread.__init__(self)
        thread_id += 1
        self.thread_ID = thread_id
        self.params = params
        self.callback = callback
        self.thread_name = str(name) + str(self.thread_ID)
        self.setName(self.thread_name)

    # helper function to execute the threads
    def run(self):
        message = self.thread_name + ' started'
        print(message)

        if self.params is None:
            self.callback()
        else:
            self.callback(self.params)


class MyProcess(ctx.Process):
    def __init__(self, callback, params=None):
        super().__init__()
        self.callback = callback
        self.data = params

    # helper function to execute the threads
    def run(self):
        if self.data is None:
            self.callback()
        else:
            self.callback(self.data)
