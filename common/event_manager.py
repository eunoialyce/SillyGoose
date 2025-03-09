class Listener:
    def __init__(self, observer, event, callback):
        self.Observer = observer
        self.Event = event
        self.Callback = callback

class EventManager:
    def __init__(self):
        self.listeners = {}

    def listen(self, listener: Listener):
        event = listener.Event
        if event in self.listeners:
            self.listeners[event].append(listener)
        else:
            self.listeners[event] = [listener]

    def clean(self, listener: Listener):
        event = listener.Event
        if event in self.listeners:
            self.listeners[event].remove(listener)
            if not self.listeners[event]: #if the list is empty
                del self.listeners[event]

    def fire(self, event, *args, **kwargs):
        if event in self.listeners:
            for listener in self.listeners[event]:
                listener.Callback(*args, **kwargs)