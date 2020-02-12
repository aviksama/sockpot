# sockpot

###### This is a `tcp` based multithreaded standalone socket server (with client) intended to be used by higher level packages.
###### The server also comes with a time-based authentication system to authenticate client and server.

* Download and install the package from git source

        pip install git+https://github.com/aviksama/sockpot.git

* Run the server by invoking the following command
        
        $ sockpot_serve [--host=0.0.0.0] [--port=9900] [--therads=5]
      
* Your client can communicate with the server like following

        >>> from sockpot.client import Connection
        >>> server = Connection(host='localhost', port=9900)
        >>> server.send('Hello', wait_for_reply=True)
        'received: Hello'
> In order to use your own shared authentication secret use a file named `settings.py` on your current path and define a variable `SECRET_KEY` inside the file.

> Note that the current handler in the server returns the original message to the client prepended by `received: `

* the default handler can be overriden by passing args with `sockpot_serve` like following
        
        $ sockpot_serve [--path="/home/<my_handler_path>"] [--calee==<my_handler>]
> The `--path` variable is set to the `PYTHONPATH` environment variable. The `--callee` can be a function or a class method or static method in the form of dotted import path
 