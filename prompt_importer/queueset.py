class QueueSet:
    # A queue that bumps duplicate items to the front instead of prepending them
    def __init__(self, size):
        self.size = size
        self.queue = []

    def push(self, item):
        self.queue = [item] + list(filter(lambda i: i != item, self.queue))
        self.queue = self.queue[: self.size]

    def __iter__(self):
        return iter(self.queue)
