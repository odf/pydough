import sys, time
import threading, Queue
import Tkinter


class GUI:
    def __init__(self, master, worker):
        self.master = master
        self.worker = worker
        self.start_GUI()
        self.poll()

    def poll(self):
        item = self.worker.get()
        if item:
            self.process_output(item)
        self.master.after(100, self.poll)

    def process_output(self, item):
        self.output.configure(text = str(item))

    def start_GUI(self):
        self.counter = 0

        Tkinter.Button(self.master,
                       text = "Work!", command = self.work).pack()
        self.output = Tkinter.Label(self.master, text = "")
        self.output.pack()

    def work(self):
        self.counter = self.counter + 1
        self.worker.put(self.counter)


class Worker:
    def __init__(self):
        self.tasks = Queue.Queue(1)
        self.results = Queue.Queue(10)

        self.worker_thread = threading.Thread(target = self.go)
        self.worker_thread.setDaemon(1)
        self.worker_thread.start()

        sys.stdout = self

    def put(self, x):
        self.tasks.put(x)

    def get(self):
        try:
            return self.results.get_nowait()
        except Queue.Empty:
            return None

    def go(self):
        while 1:
            try:
                task = self.tasks.get_nowait()
            except Queue.Empty:
                time.sleep(0.1)
            else:
                self.work(task)

    def work(self, task):
        self.results.put("Task %s started." % task)

        # Pretend to do a lengthy computation:
        time.sleep(20)

        self.results.put("Task %s completed." % task)

    def write(self, string):
        self.results.put(string)


if __name__ == "__main__":
    root = Tkinter.Tk()
    root.title("Threading test")
    GUI(root, Worker())
    root.mainloop()
