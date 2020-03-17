import datetime
#decorators that happen to be usefull

DEFAULT_PORT = 5667

LOG_STR = lambda event, x="" : (f"{datetime.datetime.now()} [{event}] "+x+"\n")
if __name__ != "__main__":
    _log_f = open("logs.txt", "w+")
    LOG = lambda e,x: _log_f.write(LOG_STR(e,x))
else:
    LOG = lambda e,x: print(LOG_STR(e,x))

def DO_FOREVER(f):
    def _f(*args, **kwargs):
        while True: f(*args, **kwargs)
    return _f

def PASS_EXCEP(f):
    def _f(*args, **kwargs):
        try: 
            return f(*args, **kwargs)
        except Exception as e:
            pass
    return _f

def LOG_CALL(f):
    def _f(*args, **kwargs):
        return f(*args, **kwargs)
        LOG("Called", f"function {f.__name__}, with args {args[1:]}")
    return _f
