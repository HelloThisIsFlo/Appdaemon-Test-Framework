import asyncio
import appdaemon.utils

# Appdaemon 4 uses Python asyncio programming. Since our tests are not async
# we replace the sync_wrapper decorator with one that will always result in
# synchronizing appdatemon calls.
def sync_wrapper(coro):
    def inner_sync_wrapper(self, *args, **kwargs):
        start_new_loop = None
        # try to get the running loop
        # `get_running_loop()` is new in Python 3.7, fall back on privateinternal for 3.6
        try:
            get_running_loop = asyncio.get_running_loop
        except AttributeError:
            get_running_loop = asyncio._get_running_loop

        # If there is no running loop we will need to start a new one and run it to completion
        try:
            if get_running_loop():
                start_new_loop = False
            else:
                start_new_loop = True
        except RuntimeError:
            start_new_loop = True

        if start_new_loop is True:
            f = asyncio.ensure_future(coro(self, *args, **kwargs))
            asyncio.get_event_loop().run_until_complete(f)
            f = f.result()
        else:
            # don't use create_task. It's python3.7 only
            f = asyncio.ensure_future(coro(self, *args, **kwargs))

        return f

    return inner_sync_wrapper

# Monkey patch in our sync_wrapper
appdaemon.utils.sync_wrapper = sync_wrapper
