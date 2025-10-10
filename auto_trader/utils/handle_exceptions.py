class handle_exceptions:
    def __init__(self, reraise: bool = True, default_return=None):
        self.reraise = reraise
        self.default_return = default_return

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if self.reraise:
                    raise e
                else:
                    return self.default_return if self.default_return is not None else e
        return wrapper