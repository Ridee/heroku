Heroku API wrapper

Really it just takes care of authentication and a few more things. The rest of
the clients are probably better abstractions. Features:

* Bring your own request maker: We use asyncio or requests, and forcing one doesn't seem right

* Simple API wrapping to make calls, easier to maintain



.. image:: https://coveralls.io/repos/github/Ridee/heroku/badge.svg?branch=master
    :target: https://coveralls.io/github/Ridee/heroku?branch=master


.. image:: https://travis-ci.org/Ridee/heroku.svg?branch=master
    :target: https://travis-ci.org/Ridee/heroku