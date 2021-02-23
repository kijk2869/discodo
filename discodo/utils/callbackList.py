class CallbackList(list):
    CALLBACK_METHOD = [
        "append",
        "extend",
        "insert",
        "remove",
        "pop",
        "reverse",
        "clear",
    ]

    def callback(self, name, *args):
        ...

    def __setitem__(self, index: int, value):
        self.callback("setItem", index, value)

        return super().__setitem__(index, value)

    def __delitem__(self, index: int):
        self.callback("delItem", index)

        return super().__delitem__(index)

    def __iadd__(self, value):
        self.callback("extend", value)

        return super().__iadd__(value)

    def __getattribute__(self, name: str):
        results = super().__getattribute__(name)

        if callable(results) and results.__name__ in self.CALLBACK_METHOD:

            def wrapper(*args):
                self.callback(name, *args)

                return results(*args)

            return wrapper

        return results

    def sort(self):
        raise ValueError("cannot use sort on queue.")
