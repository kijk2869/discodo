# ClientManager

## ``class discodo.ClientManager(**kwargs)``

This class manage voice client

### parameters

* id(Optional[[int](https://docs.python.org/3/library/functions.html#int)]) - user_id
* session_id(Optinal[[str](https://docs.python.org/3/library/stdtypes.html#str)]) - session_id

### ``discordDispatch(data)``

Description here

#### parameter

* data([dict](https://docs.python.org/3/library/stdtypes.html#dict)) - data

### ``getVC(guildID, safe=None)``

Description here

#### parameter

* guildID([int](https://docs.python.org/3/library/functions.html#int)) - discord guild id
* safe([bool](https://docs.python.org/3/library/functions.html#bool)) - defualt is False

#### returns
* VoiceClient
  
### ``delVC(guildID)``

Description here

#### parameter

* guildID([int](https://docs.python.org/3/library/functions.html#int)) - discord guild id

### ``getSource(Query)``

This function is a coroutine.
Description here

#### parameter

* Query([str](https://docs.python.org/3/library/stdtypes.html#str)) - query

#### returns

* AudioData

### ``putSource(guildID, *args, **kwargs)``

Description here

#### parameter

* guildID([int](https://docs.python.org/3/library/functions.html#int)) - discord guild id
* args - args
* kwargs - kwargs

### ``loadSource(guildID, *args, **kwargs)``

This function is a coroutine.
Description here

#### parameter

* guildID([int](https://docs.python.org/3/library/functions.html#int)) - discord guild id
* args - args
* kwargs - kwargs

#### returns

* AudioData

### ``skip(guildID, offset)``

Description here

#### parameter

* guildID([int](https://docs.python.org/3/library/functions.html#int)) - discord guild id
* offset([int](https://docs.python.org/3/library/functions.html#int)) - offset
  
### ``seek(guildID, offset)``

This function is a coroutine.
Description here

#### parameter

* guildID([int](https://docs.python.org/3/library/functions.html#int)) - discord guild id
* offset([int](https://docs.python.org/3/library/functions.html#int)) - offset

### ``setVolume(guildID, value)``

Description here

#### parameter

* guildID([int](https://docs.python.org/3/library/functions.html#int)) - discord guild id
* value([float](https://docs.python.org/3/library/functions.html#float)) - value

### ``setCrossfade(guildID, value)``

Description here

#### parameter

* guildID([int](https://docs.python.org/3/library/functions.html#int)) - discord guild id
* value([float](https://docs.python.org/3/library/functions.html#float)) - value

### ``setGapless(guildID, value)``

Description here

#### parameter

* guildID([int](https://docs.python.org/3/library/functions.html#int)) - discord guild id
* value([bool](https://docs.python.org/3/library/functions.html#bool)) - value

### ``setAutoplay(guildID, value)``

Description here

#### parameter

* guildID([int](https://docs.python.org/3/library/functions.html#int)) - discord guild id
* value([bool](https://docs.python.org/3/library/functions.html#bool)) - value
