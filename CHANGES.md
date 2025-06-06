# python-engineio change log

**Release 4.12.2** - 2025-06-04

- Support new monkey-patched gevent `Queue` class in the client [#403](https://github.com/miguelgrinberg/python-engineio/issues/403) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/dcde006b62e004c8a1d29d3478c95fbffbb11122))
- Better support of the ASGI spec when interpreting WebSocket events [#405](https://github.com/miguelgrinberg/python-engineio/issues/405) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/86cb4d22be1735f0346f35ecb912818479b74f05)) (thanks **Eric Zhang**!)

**Release 4.12.1** - 2025-05-11

- Accept empty binary values in the async server [#404](https://github.com/miguelgrinberg/python-engineio/issues/404) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/83691dd46336f10de8f288b3aa23b60e211307e1))
- Add SPDX license identifier [#401](https://github.com/miguelgrinberg/python-engineio/issues/401) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/b7f1e680f7d012294402c7e2a50d7dbcd9b2e40f)) (thanks **Marc Mueller**!)

**Release 4.12.0** - 2025-04-12

- Optimize packet parsing to avoid unnecessary calls to JSON parser [#399](https://github.com/miguelgrinberg/python-engineio/issues/399) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/2dda203103d93bc751ab0967719f18318cffc8da))
- Pass `environ` as a second argument to callable option `cors_allowed_origins` [#398](https://github.com/miguelgrinberg/python-engineio/issues/398) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/5cb561101dfcaed06bc9d73486515da93ead1752)) (thanks **wft-swas**!)

**Release 4.11.2** - 2024-12-29

- Fix incorrect disconnection reason reported when browser page is closed ([commit](https://github.com/miguelgrinberg/python-engineio/commit/132fbd9b2728c342fb989d559fa8c24b324c3cf3))

**Release 4.11.1** - 2024-12-17

- Remove debugging prints :blush: ([commit](https://github.com/miguelgrinberg/python-engineio/commit/ded35d682690bf8a74d6df1325ec5b7e28d6eed6))

**Release 4.11.0** - 2024-12-17

- Pass a `reason` argument to the disconnect handler [#393](https://github.com/miguelgrinberg/python-engineio/issues/393) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d782d9b9adc04fb691a490f29713239ad40de6c5))
- Add `maxPayload` to connection response [#392](https://github.com/miguelgrinberg/python-engineio/issues/392) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/12e423fecd15c17ddecbef396844634431c45836)) (thanks **HeySMMReseller & HeySMMProvider**!)
- Client option to disable timestamps in connection URLs [#386](https://github.com/miguelgrinberg/python-engineio/issues/386) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e8f9bbafc8c3ef8126dbe06343d0a30e32074627))
- Return disconnected sessions as 400 errors [#391](https://github.com/miguelgrinberg/python-engineio/issues/391) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/55a9e46ff91aacfc04cb21683e12345e71fe2f98))
- Handle unicode errors in ASGI driver [#389](https://github.com/miguelgrinberg/python-engineio/issues/389) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/44ce778c9a7e26d62254563e3de8c4a0c073bdc0))
- Replaced deprecated `get_event_loop` with `get_running_loop` [#384](https://github.com/miguelgrinberg/python-engineio/issues/384) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/a6e5d92ca98b41d2054737c6c49fc0511da0c3c6))
- Remove constructs required by older, now unsupported Python versions ([commit](https://github.com/miguelgrinberg/python-engineio/commit/2f257c3f83be91a464141ff4d8366cdcd7d9543b))
- Switched to pyenv-asyncio for async unit tests ([commit](https://github.com/miguelgrinberg/python-engineio/commit/08ea5ad5127e3505120ddc8ac12657f3f70f9fef))
- Adopted `unittest.mock.AsyncMock` in async unit tests instead of homegrown version ([commit](https://github.com/miguelgrinberg/python-engineio/commit/0a25a1d404dd8aab968e2b8aef870ad52c858dfc))
- Removed tests dependency on `unittest.TestCase` base class ([commit](https://github.com/miguelgrinberg/python-engineio/commit/7de6d63f4034c4e8610e02c0c3478f8b97e1bc65))

**Release 4.10.1** - 2024-10-15

- Reject request with incorrect transport [#367](https://github.com/miguelgrinberg/python-engineio/issues/367) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/7ad14481695df5adb070d52a377de49f43ddf399))

**Release 4.10.0** - 2024-10-13

- Reject requests with incorrect transport [#367](https://github.com/miguelgrinberg/python-engineio/issues/367) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4d614e5297ed2291ae97fcf30a3ee7223886440a))
- Fixed runtime error when disconnecting all clients [#368](https://github.com/miguelgrinberg/python-engineio/issues/368) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/b3339974c68dcf0e3f85c524450748c24c3a9223))
- More flexible handling of the ASGI path [#359](https://github.com/miguelgrinberg/python-engineio/issues/359) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/972687b10c9a0fecb1c08fcd30dbd7b5a97c3a52))
- Remove unused parameter in log message [#377](https://github.com/miguelgrinberg/python-engineio/issues/377) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f9a818d1444c9167457fc9f6fca3667ac7a46cf7))
- Minor updates to the server and client documentation ([commit](https://github.com/miguelgrinberg/python-engineio/commit/fe56a33fe37355dbdcd6a283f32e372f60115236))
- Add Python 3.13 CI builds ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e0e577dfd1bc8f79c5f8b033aed61947d44a5ec6))
- Run tests with mocked eventlet to avoid 3.13 failures ([commit](https://github.com/miguelgrinberg/python-engineio/commit/5b5d67d1ffd98b31eb8fb30417152cb05af6fc97))

**Release 4.9.1** - 2024-05-18

- Fix inverted shutdown logic in async service task [#354](https://github.com/miguelgrinberg/python-engineio/issues/354) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/8e688ba42de8aa9418f15943e0084f5626b092be))
- More robust WebSocket close detection in the sync client [#346](https://github.com/miguelgrinberg/python-engineio/issues/346) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/ec2df3f99fc02234c43ff01e2a75fb40c0df0409))
- Option to disable routing in ASGIApp [#345](https://github.com/miguelgrinberg/python-engineio/issues/345) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/1dbd57334499e839709ec951925b42ddfa70c57f)) (thanks **Rodja Trappe**!)

**Release 4.9.0** - 2024-02-05

- More robust handling of polling disconnects [#254](https://github.com/miguelgrinberg/python-engineio/issues/254) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e0bb263499525f5bd7eeb5195eea2dbf049d92b2))
- Clearer client logs after disconnect [#342](https://github.com/miguelgrinberg/python-engineio/issues/342) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/5b538a74061d893f255ac3544ffe1402ae97b58e))

**Release 4.8.2** - 2024-01-06

- Combine ssl_verify with other SSL options ([commit](https://github.com/miguelgrinberg/python-engineio/commit/cea2f92b7094dba8b1b0943bab9e833a5362affe)) (thanks **Simon Fonteneau**!)
- Hold references to background tasks to avoid garbage collection ([commit](https://github.com/miguelgrinberg/python-engineio/commit/0729554455d9ab1bdd36e6386272fb2d6b5607c6))
- Clearer documentation for the `max_http_buffer_size` argument ([commit](https://github.com/miguelgrinberg/python-engineio/commit/88b19f93ffea7bc1e9527889b9c2b830d082ce6b))

**Release 4.8.1** - 2023-12-28

- Fix invalid WebSocket responses [#331](https://github.com/miguelgrinberg/python-engineio/issues/331) [#332](https://github.com/miguelgrinberg/python-engineio/issues/332) [#338](https://github.com/miguelgrinberg/python-engineio/issues/338) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/ccc7a86886f507bd7aa6985e5d1b070f9505ac46))

**Release 4.8.0** - 2023-10-14

- Return consistent responses after Websocket connection ends ([commit](https://github.com/miguelgrinberg/python-engineio/commit/785c77c39d8c8fee37f969981f5a28ed2cc1b769))
- Migrate Python package metadata to pyproject.toml ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f13b64d489ea99764f1a889987b1087f879967ea))
- Remove Python 3.7 from builds ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f3717b244b6df09562760cc7e232d26a056bb1c2))
- Internal code restructure (no functional changes) ([commit #1](https://github.com/miguelgrinberg/python-engineio/commit/e26163c8bbc2341e30f91b6acba06b9157247562)) ([commit #2](https://github.com/miguelgrinberg/python-engineio/commit/f15527bc48e2d3da1668e09ab801e594f85b20d5)) ([commit #3](https://github.com/miguelgrinberg/python-engineio/commit/5c996bec85d864526fe41569438a6e15e4a53123)) ([commit #4](https://github.com/miguelgrinberg/python-engineio/commit/ca9ca5bdd1467929be311d5ddcbfd18b5f4231ae))

**Release 4.7.1** - 2023-09-12

- Replace gevent-websocket with simple-websocket when using gevent ([commit](https://github.com/miguelgrinberg/python-engineio/commit/614f564275c635dc8b03d33dab44bf80d280cbcc))
- Catch and log all errors that occur in event handlers ([commit](https://github.com/miguelgrinberg/python-engineio/commit/2bef6d6fbbe684e5718f9202cd7af0ad19153495))
- Use daemon threads for background tasks also in the threaded client ([commit](https://github.com/miguelgrinberg/python-engineio/commit/53578088046ca9f29b6119c182c7bed67d7a4ffb))
- Silence exception on websocket exit when using uWSGI [#330](https://github.com/miguelgrinberg/python-engineio/issues/330) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/9bc9e867e28e2495031bd1a552f4da0b1f0f575c))

**Release 4.7.0** - 2023-09-03

- Added `send_packet()` method ([commit](https://github.com/miguelgrinberg/python-engineio/commit/48451a3a18c40c58cc5d4127250e4776e5b7f8db))
- Fixed race condition when lots of connections are ended at the same time [#328](https://github.com/miguelgrinberg/python-engineio/issues/328) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/bb87ec652f55b41063400205971b0a667b78b162))
- Workaround for strange memory leak in Eventlet's `Thread` class [#328](https://github.com/miguelgrinberg/python-engineio/issues/328) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d29aa9c44450c4ea729a0846091e3b105b8b7497))
- Use daemon threads for background tasks in threading mode ([commit](https://github.com/miguelgrinberg/python-engineio/commit/541f172a4a61ebc16ee32fa38b0f410c4c711fbf))
- Upgrade to pypy-3.9 in unit tests ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4581e53ada773fef8976110cc6d4ae40783b38d8))

**Release 4.6.1** - 2023-08-23

- Fix double close of websockets in ASGI adapter [#327](https://github.com/miguelgrinberg/python-engineio/issues/327) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e629eee17d7df7dc9736763b4220daed54a6dbdf))

**Release 4.6.0** - 2023-08-21

- Improvements in the connection rejected flow ([commit](https://github.com/miguelgrinberg/python-engineio/commit/8051fc49f484585b786031a08617208efdc97f5a))
- Better handling of Gunicorn threaded worker ([commit](https://github.com/miguelgrinberg/python-engineio/commit/29e4492cdf836a2197479c5946089b2363305379))
- `shutdown()` method for the Engine.IO server ([commit](https://github.com/miguelgrinberg/python-engineio/commit/87f6003653b45fe2b230d8c33c8962e15e71e157))

**Release 4.5.1** - 2023-07-06

- Restore support for old versions of eventlet [#321](https://github.com/miguelgrinberg/python-engineio/issues/321) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/503c8651658e26276f3206655a819f79eb25739e))

**Release 4.5.0** - 2023-07-05

- Configure eventlet's websocket max frame length [#319](https://github.com/miguelgrinberg/python-engineio/issues/319) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/1b04a562322a386ef806f1ada73e83d40fa1f0ce))
- Remove old Python 2 syntax in `super()` calls ([commit](https://github.com/miguelgrinberg/python-engineio/commit/b37ee7697418c9a982af570758044d0e728e2ce2))

**Release 4.4.1** - 2023-04-19

- Prevent crash when closing simple-websocket connection [#311](https://github.com/miguelgrinberg/python-engineio/issues/311) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/71e7d3688947779d2f086014e117ebb66606145e))
- Fix server/client mixup in client docstrings [#312](https://github.com/miguelgrinberg/python-engineio/issues/312) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/911cf520034ee17bcc9311e244e616848cfff095)) (thanks **Sasja**!)

**Release 4.4.0** - 2023-03-16

- Allow configuring underlying websocket connection with custom options [#293](https://github.com/miguelgrinberg/python-engineio/issues/293) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/45e97b8cf885e998168857c46e29a7e257754f3e)) (thanks **Bruce Yu**!)
- Cancel all running tasks in async SIGINT handler [#306](https://github.com/miguelgrinberg/python-engineio/issues/306) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/0d263b0e40460c334a0b259804f2ff156bc3718c))
- Handle unexpected WebSocket close frames sent by server [#292](https://github.com/miguelgrinberg/python-engineio/issues/292) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4f67c95f8631e624e44afe5bdfccfff924b232c9))
- Close aiohttp session after a failed connection [#307](https://github.com/miguelgrinberg/python-engineio/issues/307) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/86ed2ae9f84578b9c6b7a6839c3b82304a65725f))
- Catch IOErrors from uWSGI and explicitly close the driver [#301](https://github.com/miguelgrinberg/python-engineio/issues/301) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/678ae8b0efa6c12ae36d5c5b362e50aabc8dc8e9)) (thanks **June Oh**!)
- Recommend ASGI integration for Sanic in Documentation ([commit](https://github.com/miguelgrinberg/python-engineio/commit/bf9d8eabe02c2aadce22e70b71375ccc2bd21e79))
- Fix documentation for `max_http_buffer_size` [#310](https://github.com/miguelgrinberg/python-engineio/issues/310) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/8182f783830b9fda9abc8e2410e7f397c0f62482)) (thanks **Lawrence Ong**!)
- Add Python 3.11 to builds ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4a8a9a640fd4567d8c6001e1058e9980af3067ff))

**Release 4.3.4** - 2022-08-03

- Let companion ASGI app handle lifespan events [#287](https://github.com/miguelgrinberg/python-engineio/issues/287) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/1c9001c537fd669a3b0e28d75f707216ec48befa))
- Use configured request timeout when making a WebSocket connection [#286](https://github.com/miguelgrinberg/python-engineio/issues/286) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f6df30b841a86f96765c307efa99a7505dd9b4c1)) (thanks **jpfarias**!)

**Release 4.3.3** - 2022-07-04

- Handle ASGI lifespan when running with a secondary ASGI app [#284](https://github.com/miguelgrinberg/python-engineio/issues/284) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c4a021ee9c4d760bbe4066887ca816fc7c718f98)) (thanks **mozartilize**!)
- Update deprecated usage of `asyncio.wait()` [#281](https://github.com/miguelgrinberg/python-engineio/issues/281) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d3a23c0936cda2ff3de8c5ae0c834ffef515e8cb)) (thanks **Ben Beasley**!)
- Better handling of queued WebSocket messages in uWSGI [#256](https://github.com/miguelgrinberg/python-engineio/issues/256) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/ec7b3da2e48060e177bf8ad6a9f5fae445207c82))
- Gracefully fail to decode empty packets [#269](https://github.com/miguelgrinberg/python-engineio/issues/269) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/9c657071f3d42a88fd1615b5edd245a89445ea1b))
- Only attempt to set an async signal handler once [#276](https://github.com/miguelgrinberg/python-engineio/issues/276) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/6869751aafb6db83d1a53fbd47d3fbfd2a8ae490))

**Release 4.3.2** - 2022-04-24

- Option to use a callable for `cors_allowed_origins` [#264](https://github.com/miguelgrinberg/python-engineio/issues/264) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/60e8e553e1fc64a5b0dbb846a86c5c0698101a9e))
- Close aiohttp session when disconnecting [#272](https://github.com/miguelgrinberg/python-engineio/issues/272) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/a9fb317c29d93b98a729df800f124b6b923fc82c))
- Remove 3.6 and pypy-3.6 builds, add 3.10 and pypy-3.8 ([commit](https://github.com/miguelgrinberg/python-engineio/commit/06480be268852ffc96793ef52213ad598b85fa69))

**Release 4.3.1** - 2022-01-11

- Fix support for Sanic v21.9.0 and up ([commit](https://github.com/miguelgrinberg/python-engineio/commit/b0157d5a7e35ad83bc33f363b154402838fac83b)) (thanks **13g10n**!)
- Include example code in flake8 pass ([commit](https://github.com/miguelgrinberg/python-engineio/commit/776bb86bb560bcd1912350bc24382fe6090c9c84))
- Remove unused `__version__` constant [#262](https://github.com/miguelgrinberg/python-engineio/issues/262) ([commit 1](https://github.com/miguelgrinberg/python-engineio/commit/e882f5949bdd1618d97b0cade18a7e8af8670b41) [commit 2](https://github.com/miguelgrinberg/python-engineio/commit/ed4b1e2b8b18ac5adb2ee9a2ef126a4e5ffee128))

**Release 4.3.0** - 2021-10-26

- **Backward incompatible change**: Reject websocket messages larger than `max_http_buffer_size` [#260](https://github.com/miguelgrinberg/python-engineio/issues/260) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/5f519a22b9543f585adc352e13f2a9b3cbfca727))
- Enable or disable specific transports [#259](https://github.com/miguelgrinberg/python-engineio/issues/259) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/8a0e4c3a406358065ef4eb878e60d2dc3b758bf4)) (thanks **Maciej Szeptuch**!)
- Option to disable the `SIGINT` handler in the client ([commit](https://github.com/miguelgrinberg/python-engineio/commit/14ed9f1d8f19e87a13b427427a6597e72d51db57))
- Support binary packets with zero length [#257](https://github.com/miguelgrinberg/python-engineio/issues/257) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/bcd1a42f86aad12460b6eb836a5c317db55cba77))
- Improve documentation on `start_background_task()` function ([commit](https://github.com/miguelgrinberg/python-engineio/commit/531d28ae2583e30c17ec7a0c911cde0343663244))
- Remove unsanitized client input from error messages [#250](https://github.com/miguelgrinberg/python-engineio/issues/250) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/72b7136cffd67d4299cb3dab17d1632a30ef5207)) (thanks **André Carvalho**!)
- Use plaintext Content-Type when using polling [#248](https://github.com/miguelgrinberg/python-engineio/issues/248) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c2603e9ddc7ff96a8fe7beced751aea1480ec5e6)) (thanks **Tobias**!)
- Return better error messages for client connection errors [#243](https://github.com/miguelgrinberg/python-engineio/issues/243) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/3daa02e198aca9657cb04ea91ba4e3234113bde9))
- Reuse the aiohttp client session on reconnects [#226](https://github.com/miguelgrinberg/python-engineio/issues/226) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/3c8fdfe05864e43ad8f35214fa2ad27bcb24965f))

**Release 4.2.1** - 2021-08-02

- Support setting `socketio_path` to the root URL [#242](https://github.com/miguelgrinberg/python-engineio/issues/242) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/47ada56b1ada2ed6eeb8c0fe172045bed321a037))
- Use the gevent selector to avoid 1024 file handle limitation of select[#228](https://github.com/miguelgrinberg/python-engineio/issues/228) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/6a4fd582e23d03d90b67b6825518a6c73431c6dd))
- Pass reason when closing a WebSocket connection ([commit](https://github.com/miguelgrinberg/python-engineio/commit/583c7db1f9dfa62290481634b4f9ab4d39a8ec6b))
- Improved project structure ([commit](https://github.com/miguelgrinberg/python-engineio/commit/bf37732b38b6d798f86fdf5c3d26b8e306e34655))
- Remove executable permissions from files that lack shebang lines [#240](https://github.com/miguelgrinberg/python-engineio/issues/240) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/7a4e2780f9ea3466a8a14e3f1720561773faee7c)) (thanks **Ben Beasley**!)

**Release 4.2.0** - 2021-05-15

- WebSocket support for threading mode ([commit](https://github.com/miguelgrinberg/python-engineio/commit/b84537af22e547211163521f7bc85995faab3625))
- Fixed CORS handling of scheme proxy server header [#1501](https://github.com/miguelgrinberg/Flask-SocketIO/issues/1501) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/fb47df6949c10c35d6630daacb3d511d2086f1b3))
- Correct handling of static files when secondary WSGI/ASGI app is set [#653](https://github.com/miguelgrinberg/python-socketio/issues/653) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/bd2e59d0b37e86fd561f716f2d805081200f896e))
- Remove outdated binary argument from example code ([commit](https://github.com/miguelgrinberg/python-engineio/commit/090454ffe66ebe7e830ecbd859f0416c7bc74eee))
- Added Open Collective funding option ([commit](https://github.com/miguelgrinberg/python-engineio/commit/9e3497a9749aebc87268250673cebba35c6922cf))

**Release 4.1.0** - 2021-04-15

- Change pingTimeout to 20 seconds to match JavaScript's Socket.IO 4.x releases ([commit](https://github.com/miguelgrinberg/python-engineio/commit/1e29203b41ee5f1bbde17bf77a909183fc66033a))
- Configure the JSON decoder for safer parsing ([commit](https://github.com/miguelgrinberg/python-engineio/commit/dd1db2ec6b75a95bfab5e73a8f71fdb69bd54534)) (thanks **Onno Kortmann**)
- Remove obsolete 'mock' dependency [#218](https://github.com/miguelgrinberg/python-engineio/issues/218) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/845fc6201a783d14e02924c593028d3d06600d73)) (thanks **Michał Górny**!)

**Release 4.0.1** - 2021-03-10

- Support for client to verify server with custom CA bundle ([commit](https://github.com/miguelgrinberg/python-engineio/commit/792bdd040a460d0f77309ed1c7d9fea236542140)) (thanks **Brandon Hastings**!)
- Report missing websocket client as an error in log [#557](https://github.com/miguelgrinberg/python-socketio/issues/557) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/2f806acc927ac334541f77455b3a51a879649aeb))
- Remove asyncio client delay before attempting reconnection [#622](https://github.com/miguelgrinberg/python-socketio/issues/622) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/1d174b7bc47d4958a9829130321f8c87141007d7))
- Fix error handling for ASGI WebSocket errors [#210](https://github.com/miguelgrinberg/python-engineio/issues/210) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e8e4ba5d1c832e14568e575ecdd173395493ea48))
- Fix logging of missing sid [#1472](https://github.com/miguelgrinberg/Flask-SocketIO/issues/1472) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/cdfc1d88151a9f9f81082810db74fa3882d8adca))
- Change deprecated `body_bytes` in sanic to `body` [#207](https://github.com/miguelgrinberg/python-engineio/issues/207) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e16bbcac1c76dbab61dd378768128af5dfeb8357)) (thanks **Alison Almeida**!)
- Remove references to Python 3.5 in the documentation [#211](https://github.com/miguelgrinberg/python-engineio/issues/211) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/753656374ee74aedc8a70e92ea717d4ddb5c95dc))
- Added performance testing scripts ([commit](https://github.com/miguelgrinberg/python-engineio/commit/28fe975daf239a2612e59843f06c52a72cfea84b))

**Release 4.0.0** - 2020-12-07

- Implementation of the Engine.IO v4 protocol revision
    - v4 protocol: ping/ping reversal in the server ([commit](https://github.com/miguelgrinberg/python-engineio/commit/52774aaf019c1560ba2d46d7fb32668516fb9aff))
    - v4 protocol: ping/ping reversal in the client ([commit](https://github.com/miguelgrinberg/python-engineio/commit/76a0615ec02818b1aba38ced38e5f6cefc40790d))
    - v4 protocol: change max http buffer size to 1MB ([commit](https://github.com/miguelgrinberg/python-engineio/commit/38e20a3f31ffc566d521a80f0d13499a4de8e67e))
    - v4 protocol: do not set the io cookie by default ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f17663608178d4ee5f0ab9f1d4523813b96f3e1f))
    - v4 protocol: use EIO=4 in connection URL ([commit](https://github.com/miguelgrinberg/python-engineio/commit/b474d70b413307be5b713d3f7e3b79dbd1b631a4))
    - v4 protocol: new payload separator ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e895d6f5d0fa88566df61ffd316ce31d7cecfb90))
    - v4 protocol: new binary encoding format ([commit](https://github.com/miguelgrinberg/python-engineio/commit/38beea5f7903af2e79ab3654b0c299aba2f226da))
- Use a sid generator algorithm similar to JavaScript's version of Socket.IO ([commit](https://github.com/miguelgrinberg/python-engineio/commit/0583c1e8b122e4c7620e04429bf4f901bad551bd))
- Ignore case when comparing transport argument against 'HTTP_UPGRADE' header ([commit](https://github.com/miguelgrinberg/python-engineio/commit/3d7ea22e8a9930544c711c5e124f75121b300ef3)) (thanks **Matthew Barry**!)
- Remove dependency on the six package ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c181e8563edf1586eb3f2baacaf4f2c26b1a2593))

**Release 3.14.2** - 2020-11-30

- Log first occurrence of bad request errors at level ERROR for higher visibility ([commit](https://github.com/miguelgrinberg/python-engineio/commit/3fc702f459554ccbdfaaad2673b6063d2ef4485e))

**Release 3.14.1** - 2020-11-28

- Catch more connection exceptions in the asyncio client [#561](https://github.com/miguelgrinberg/python-socketio/issues/561) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/0d8d3a66292e2bc71b5af5b3e2162fde02c3f487))
- Revert "On Windows use SIGBREAK to break client" since the fix was not effective ([commit](https://github.com/miguelgrinberg/python-engineio/commit/788cf86a0b6223546b085966e800466a25fe07e1))

**Release 3.14.0** - 2020-11-28

- Reject incorrect Engine.IO protocol versions ([commit](https://github.com/miguelgrinberg/python-engineio/commit/00330bbc4292f50e5a7726f28c028f6cd7c90aa5))
- Accept an initialized requests or aiohttp session object ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f371ad17f3a261366cde124f926bf62dc191a9ea))
- Handle ping interval and timeout given as strings [#201](https://github.com/miguelgrinberg/python-engineio/issues/201) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/1751039070da3fee381568f2b017aa83bef36bf1)) (thanks **Akash Vibhute**!)
- Handle websocket connections without upgrade header [#72](https://github.com/miguelgrinberg/python-engineio/issues/72) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/da4afaa6ed80f7cce6e102a51ff03390267b51a1))
- Catch broken pipes and OS errors in websocket thread [#177](https://github.com/miguelgrinberg/python-engineio/issues/177) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/0dde7d7ae19478a56610b3a06f76419013e60d62))
- Expose ASGI scope in connect environ [#192](https://github.com/miguelgrinberg/python-engineio/issues/192) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/3a58d406427a5ac99803c4b4d516b5478022b3c6)) (thanks **Korijn van Golen**!)
- Emit ASGI lifespan shutdown event [#200](https://github.com/miguelgrinberg/python-engineio/issues/200) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/2fb17746e72c74a2bce6a1169b6f841ac3473ea9))
- Add option to set cookie SameSite and Secure settings. ([commit](https://github.com/miguelgrinberg/python-engineio/commit/8f175760eb95b9c67548c5d9969765f710d40296)) (thanks **Billy Felton**!)
- Stop event loop when client is interrupted with Ctrl-C [#197](https://github.com/miguelgrinberg/python-engineio/issues/197) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/402402f7c19760e84d0c32abc8e729baff51623d))
- Do not try to install signal handler if unsupported [#199](https://github.com/miguelgrinberg/python-engineio/issues/199) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c0a1c2801cb35e6d192ddf542f79359c823655aa)) (thanks **Philippe**!)
- On Windows use SIGBREAK to break client [#570](https://github.com/miguelgrinberg/python-socketio/issues/570) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f5fda518d8943be7846321275760a589a1e63bc0))
- Client: handle error responses with invalid JSON [#553](https://github.com/miguelgrinberg/python-socketio/issues/553) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f543839512b960c904f73cf5ea2a647b058c8bf7))
- Added troubleshooting section to the documentation ([commit](https://github.com/miguelgrinberg/python-engineio/commit/32e0e2992f9d109dbad7124b615e97d6e8b3285d))
- Move builds to GitHub actions ([commit](https://github.com/miguelgrinberg/python-engineio/commit/232f165a2d2b41b62f540ed6b77c8db722c6dc4f))

**Release 3.13.2** - 2020-08-18

- Improved signal handler for the async client [#523](https://github.com/miguelgrinberg/python-socketio/issues/523) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/eabfdaa9d1644d3346ec3ec7fae040c85029b75e))
- Add SameSite attribute to Socket.IO cookie [#1344](https://github.com/miguelgrinberg/Flask-SocketIO/issues/1344) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/2ec2bac6d7738b89ae0fe0645e30d50dd100cab1))
- Handle GeneratorExit exception appropriately [#182](https://github.com/miguelgrinberg/python-engineio/issues/182) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c7ab55269e0cf94c7684675101d910d740f179cc)) (thanks **PaulWasTaken**!)
- Simplify asserts in unit tests ([commit](https://github.com/miguelgrinberg/python-engineio/commit/638c1fa4d54a7cfa20711df5a1b3e8e1e3754c3d))
- Use pytest as test runner ([commit](https://github.com/miguelgrinberg/python-engineio/commit/dcea3a09775cc054b4b937d6d8c1caff5af4f617))

**Release 3.13.1** - 2020-07-02

- Fix KeyError during WebSocket disconnection in AsyncServer [#179](https://github.com/miguelgrinberg/python-engineio/issues/179) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f43807b26ea1a185ff0b9f569dd586ca77b8da67))

**Release 3.13.0** - 2020-05-23

- Support direct WebSocket connections in ASGI server ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c0e2817bddf2c12e72cbfe7e2ca4bb3f41392af5))
- ASGI startup and shutdown lifespan handlers [#169](https://github.com/miguelgrinberg/python-engineio/issues/169) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/38cc39f527e4913f3fee519a2f13f218056343a7)) (thanks **avi**!)
- Improved handling of rejected connections ([commit](https://github.com/miguelgrinberg/python-engineio/commit/0e0b26f89bea6b0662c1d1748c5ae1fde5668207))
- Make client disconnects more robust [#417](https://github.com/miguelgrinberg/python-socketio/issues/417) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4297eb4a9033029cd0061e3ddd5d46974b8e4d9e))
- End WebSocket connection gracefully when user is intentionally disconnected [#168](https://github.com/miguelgrinberg/python-engineio/issues/168) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e4d9c33216a851ca0261b0944d4c08afcc05ae1e)) (thanks **Mohammad Almoghrabi**!)
- Enable locking in websocket-client package [#170](https://github.com/miguelgrinberg/python-engineio/issues/170) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f7bbd97a68022b25f7d70c044cbff4328c50e909))
- Correctly parse cookies with a "=" in their values [#175](https://github.com/miguelgrinberg/python-engineio/issues/175) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/8c1d98c056ac69b04d8a1412a70563909b19f7e6)) (thanks **Ignacio Pascual**!)
- Removed references to Python 2.7 in the documentation ([commit](https://github.com/miguelgrinberg/python-engineio/commit/5b79e28d8a2c5349590f9ea23d9cb8142c165295))

**Release 3.12.1** - 2020-03-17

- Asyncio client: correctly update cookie jar [#166](https://github.com/miguelgrinberg/python-engineio/issues/166) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/5f2c7f640cbe1620387b6843683b2150dc713d82))

**Release 3.12.0** - 2020-03-14

- Correct handling of cookies in the client [#162](https://github.com/miguelgrinberg/python-engineio/issues/162) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/59a0cd43f7fabc2c6b2546c59e72f8376b9f85cc))
- Fixed infrequent race condition when upgrading from polling to WebSocket [#160](https://github.com/miguelgrinberg/python-engineio/issues/160) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f2cce2bccb7fca58bb6115630d5c221569e52ba4))
- Only add signal handler when client is created in main thread [#163](https://github.com/miguelgrinberg/python-engineio/issues/163) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e1ed079a8dafe2b9ca596fa2fc2885a91d1b486d))
- More robust handling of a closing connection [#164](https://github.com/miguelgrinberg/python-engineio/issues/164) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/bdd584b3b3ca87f37f89921e54d5b27ec5fd7953))
- More accurate logging documentation [#158](https://github.com/miguelgrinberg/python-engineio/issues/158) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/5260f5c4d8e6091fb913be9b688d61e36c11fb26))

**Release 3.11.2** - 2020-01-03

- Last version to support Python 2
- Detect unreported websocket closures in asyncio client [#401](https://github.com/miguelgrinberg/python-socketio/issues/401) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/a67b3d76d80e665ec071292dc4aadffb50be6d3f))
- Initialize aiohttp when client connects directly through websocket [#152](https://github.com/miguelgrinberg/python-engineio/issues/152) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/9a3d6453bd35bc9581b5dd9226dc9e6bba3a18aa))
- Initialize the client's SIGINT signal handler only if a client is created [#147](https://github.com/miguelgrinberg/python-engineio/issues/147) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/6534d324f3dce2e1e4927932660d5e5e8bcab202))
- Add better exception handling for errors thrown by the websocket-client package [#155](https://github.com/miguelgrinberg/python-engineio/issues/155) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/33c7cf1ba9ecc8dd24b0d850dfe334d425474612)) (thanks **Adam Grant**!)
- Missing timeout when closing websocket client connection [#148](https://github.com/miguelgrinberg/python-engineio/issues/148) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/02a2c705b01f171edea106a7ee867b6112074853))

**Release 3.11.1** - 2019-12-10

- Reset event when it is reused after a reconnect [#153](https://github.com/miguelgrinberg/python-engineio/issues/153) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/179d0df931724f1c518d09417012e0adc90501fd))

**Release 3.11.0** - 2019-12-07

- Use aiohttp's WebSocket client [#324](https://github.com/miguelgrinberg/python-socketio/issues/324) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/280aa0f00c0ca3d099c2a693f6c2ce7919d2dc86))
- Support user created loops on the asyncio client [#1065](https://github.com/miguelgrinberg/Flask-SocketIO/issues/1065) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e38daad301d4b855cabf6a289b7348a58a314273))
- Fix occasional server disconnect crashes [#146](https://github.com/miguelgrinberg/python-engineio/issues/146) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/9f96cd827c59776cb7da72614891be05681e5063)) (thanks **Dominik Winecki**!)
- Use X-Forwarded headers if present to verify origin ([commit](https://github.com/miguelgrinberg/python-engineio/commit/3c221aaec7173a046ca42f6aff9be0915cf92237))
- Support async `make_response` function in ASGI driver [#145](https://github.com/miguelgrinberg/python-engineio/issues/145) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/3f6391ca3229d26f081a16436cd4acd292ee69df))
- Support not having a sigint handler [#143](https://github.com/miguelgrinberg/python-engineio/issues/143) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/fc984aaa5e5dc91f6632729e56b34628f2fd2563)) (thanks **Robin Christine Burr**!)
- Fix websocket exception handling on python2.7 [#149](https://github.com/miguelgrinberg/python-engineio/issues/149) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/b714f81a0ee27e30070a5ca702a1823236df9981)) (thanks **Payton Yao**!)

**Release 3.10.0** - 2019-10-22

- Added support for SSL connection to unverified host in the client. [#137](https://github.com/miguelgrinberg/python-engineio/issues/137) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/51da0bed3c93c41b980bb565560c7233da3501f5)) (thanks **sgaron-cse**!)
- Performance improvements in parsing long-polling payloads ([commit](https://github.com/miguelgrinberg/python-engineio/commit/64a34fc1550458ded57014301d5f9e97534f0843))
- Prevent heavy CPU usage when decoding payloads ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c8407ae97821bb00c33a91114f425b8454f5e50e))
- Handle case where no original SIGINT handler existed and call signal.… [#140](https://github.com/miguelgrinberg/python-engineio/issues/140) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/9b4a10fede2ef3a9e85f370f48b6720fe7a15f35)) (thanks **Robin Christine Burr**!)
- Accept any 2xx response as valid in the client [#331](https://github.com/miguelgrinberg/python-socketio/issues/331) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/9d4ab4bb519d898ef170815deb767b85aeefd141))
- Avoid loop without yield when sockets are >60 [#138](https://github.com/miguelgrinberg/python-engineio/issues/138) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/5c6fbeac0e9f0788d300cf06de74ce65f8994f05)) (thanks **Gawen Arab**!)
- Configurable ping interval grace period [#134](https://github.com/miguelgrinberg/python-engineio/issues/134) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/bb2401354c3b7c3cf6a5577db83cc51ae071836e))

**Release 3.9.3** - 2019-08-05

- Apply timeouts to all HTTP requests sent from the client [#127](https://github.com/miguelgrinberg/python-engineio/issues/127) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/6666d6a092333aa60f48ccdc42b250be60e9f33c))
- Shutdown non responding websocket connections in the client [#326](https://github.com/miguelgrinberg/python-socketio/issues/326) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/95731e9e2d66e8ee91faeb5538dcde84b88466bd))
- Catch OSError exceptions from websockets package [#328](https://github.com/miguelgrinberg/python-socketio/issues/328) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/0adc074e58dac1d81f769ed1a2edfcab5e0644d1))

**Release 3.9.2** - 2019-08-03

- Skip CORS headers when origin is not given by client [#131](https://github.com/miguelgrinberg/python-engineio/issues/131) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/a349d4e3ce25ff771027f986c7594d840cc9e941))
- Add `async_handler`s sub-package to setup.py ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e4163b64f3482d2d97dccf813a880cb6ad088533))

**Release 3.9.1** - 2019-08-02

- Restore CORS disable option [#329](https://github.com/miguelgrinberg/python-socketio/issues/329) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/9f4cd8cf9e7be6baf4bc8c485e7ad204dd87be75))

**Release 3.9.0** - 2019-07-29

- Address potential websocket cross-origin attacks [#128](https://github.com/miguelgrinberg/python-engineio/issues/128) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/7548f704a0a3000b7ac8a6c88796c4ae58aa9c37))
- Documentation for the Same Origin security policy ([commit](https://github.com/miguelgrinberg/python-engineio/commit/5b5879469348c529c283e1d81032a603c5e69b31))
- Remove tests from built package [#124](https://github.com/miguelgrinberg/python-engineio/issues/124) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/399dc8acf2077856c4bd8edb22d0f254b47f0ca2)) (thanks **Pablo Escodebar**!)

**Release 3.8.2** - 2019-06-29

- Correctly autodetect asgi async mode [#122](https://github.com/miguelgrinberg/python-engineio/issues/122) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/2690ea08b3d3beeaf34b5b4871ac1b567e048a9f))
- Omit response when asyncio websocket ends [#120](https://github.com/miguelgrinberg/python-engineio/issues/120) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f13074670dcd95e578d17f00b91845139e4f25eb))
- Improved ocumentation on user session behavior on disconnections ([commit](https://github.com/miguelgrinberg/python-engineio/commit/6b8e667ad26c4e654f84b7f12b851c07d801211d))
- Correct spelling mistakes in documentation [#119](https://github.com/miguelgrinberg/python-engineio/issues/119) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/a4404989a1c48b3522c09a7f6335f2ad401805a2)) (thanks **Edward Betts**!)

**Release 3.8.1** - 2019-06-08

- Optimization to static file serving ([commit](https://github.com/miguelgrinberg/python-engineio/commit/5b8701042678b3e092e2be365bdd31b425b714f6))
- Do not reset connection when packet queue timeouts [#110](https://github.com/miguelgrinberg/python-engineio/issues/110) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e64e5a67b723400e20cb7c5a014413a4445d9184)) (thanks **Victor Moyano**!)

**Release 3.8.0** - 2019-06-03

- Much more flexible support for static files in the server ([commit](https://github.com/miguelgrinberg/python-engineio/commit/b27cafb207589cc52b5ba1ffa60f9a2e1e553af9), [commit](https://github.com/miguelgrinberg/python-engineio/commit/a56aed103c39a25ff6afb316d171cfeca5bf9894))
- Correctly handle rejected websocket connections in Tornado [#114](https://github.com/miguelgrinberg/python-engineio/issues/114) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/51f5ad28d5c3a17bfad7d9b55555b23223eff43b))

**Release 3.7.0** - 2019-05-29

- Add JSONP support in the server [#98](https://github.com/miguelgrinberg/python-engineio/issues/98) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/36a15987a677ba5a61675250f9b4a9e7c6cbaa74)) (thanks **StoneMoe**!)
- Send binary packets as such in the sync client [#112](https://github.com/miguelgrinberg/python-engineio/issues/112) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/076232e86fa923c2f44472f8eb358b141c61783a))
- Handle CLOSE packet in the client [#100](https://github.com/miguelgrinberg/python-engineio/issues/100) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/612815f793f4c749c9a9459ff08804ddd629da31))
- Document how to access the sid for the connection ([commit](https://github.com/miguelgrinberg/python-engineio/commit/3de448881989485e0f986441896a1871354ba36a))

**Release 3.6.0** - 2019-05-25

- Tornado 6 support ([commit](https://github.com/miguelgrinberg/python-engineio/commit/99359e43188f05e1844b68fef862f3af99919044)) (thanks **Michel Llorens**!)
- added note on CORS support for sanic ([commit](https://github.com/miguelgrinberg/python-engineio/commit/a3a4cb82059e2229d1b5e9ed9404dacc1b9afc34))
- added python 3.7 build ([commit](https://github.com/miguelgrinberg/python-engineio/commit/805aa9fd7156425a2dce6b782b96f0e805ee4501))
- auto-generate change log during release ([commit](https://github.com/miguelgrinberg/python-engineio/commit/be2c76e3e5b803284a6f2a9e4abed3314b9af7b6))
- added change log ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f8b15d1c06439581ca6b0d697f67cd034fb5bbf5))
- helper release script ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d36548cade90ddf8c6ab68178cb9747d5ac0d51f))

**Release 3.5.2** - 2019-05-19

- migrate to ASGI3 [#108](https://github.com/miguelgrinberg/python-engineio/issues/108) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/5a7f9e719b6fb3bfc9da07b882c4b77b102aef0d)) (thanks **Florimond Manca**!)
- updated asgi examples to latest uvicorn ([commit](https://github.com/miguelgrinberg/python-engineio/commit/261fd67103cb5d9a44369415748e66fdf62de6fb))
- remove security alert in requirements ([commit](https://github.com/miguelgrinberg/python-engineio/commit/1b044aaac9657ff947c6666638cf89315303bf6c))
- removed unused arguments and methods ([commit](https://github.com/miguelgrinberg/python-engineio/commit/951b4c39af9ec22dbc06046d562866e0f32152cd))

**Release 3.5.1** - 2019-04-07

- Downgrade log levels in some areas [#103](https://github.com/miguelgrinberg/python-engineio/issues/103) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/57b81be14b1d2fd4701c1b1d3c07710661807983)) (thanks **Aaron Bach**!)
- capture timeouts and other exceptions from requests ([commit](https://github.com/miguelgrinberg/python-engineio/commit/45397f1d2f7a7ea7ae6fb87049579bccf6cb1b87))

**Release 3.5.0** - 2019-03-16

- not necessary to hold the packet queue when upgrading ([commit](https://github.com/miguelgrinberg/python-engineio/commit/330c6b9379afb4a098c24456f1a96fed8c314b10))
- add link to stack overflow for questions ([commit](https://github.com/miguelgrinberg/python-engineio/commit/138fb60a9bb8a4aae86e08a5fd5485563733b9d1))
- pep8 fixes for previous commit ([commit](https://github.com/miguelgrinberg/python-engineio/commit/0c15cdc29ff130dba2887f5bfc2623f57b4fb45c))
- Use the correct text type for upgrade probes in both Python 2 and 3 [#101](https://github.com/miguelgrinberg/python-engineio/issues/101) [#265](https://github.com/miguelgrinberg/python-engineio/issues/265). ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4f0b4ea83298701a2e192c1e42fc3e917f1ee989)) (thanks **Sam Brightman**!)

**Release 3.4.4** - 2019-03-14

- Pass cookies to websocket connection creation ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c4c9178951aa2b9ede3ccec9af79324444e09314)) (thanks **Adrien Gavignet**!)
- close the aiohttp client to prevent exit warnings ([commit](https://github.com/miguelgrinberg/python-engineio/commit/9f6db446034a579415ae17dc0490ba23d92c723d))
- readme fixes ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d6a33d22cfd3ebe8b4d78cd5c27607de837d16e9))

**Release 3.4.3** - 2019-02-20

- exit service task if event loop is closed ([commit](https://github.com/miguelgrinberg/python-engineio/commit/ee6e00d5d4131f1d120797528b94140c2006b848))
- more tornado fixes ([commit](https://github.com/miguelgrinberg/python-engineio/commit/68ca0c2f3ebe2d255449a1f3a8b1b11d2deb84ef))

**Release 3.4.2** - 2019-02-19

- added missing await in tornado driver ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4ac92d4642f248ae763493c1d26e9e5f2058ac93))

**Release 3.4.1** - 2019-02-16

- check for origin in Tornado's WebSocket handler ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c4b506a0eb91a67e68944c8048ca9a867407c182))

**Release 3.4.0** - 2019-02-15

- replace urllib3 with requests to get cookie support ([commit](https://github.com/miguelgrinberg/python-engineio/commit/41b8e29e49560170e852df1c5c070c6d311452d5))

**Release 3.3.2** - 2019-02-12

- reset sid after a disconnect ([commit](https://github.com/miguelgrinberg/python-engineio/commit/9aa774270b41c7ef5f7e7c3bee6c2b8c40936951))
- uniform service task cancellation ([commit](https://github.com/miguelgrinberg/python-engineio/commit/82f6982b5f81f749600565266d9da9c108991eed))
- Fix hang on KeyboardInterrupt when running with asyncio. [#95](https://github.com/miguelgrinberg/python-engineio/issues/95) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c60499e689fd8ea1ee4db269fcd3a7f2ab7fbb08)) (thanks **Ingmar Steen**!)

**Release 3.3.1** - 2019-02-09

- better error handling during websocket connection handshake ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f4c49c44a9b83a9fdc286bb38ff3be39b165118b))
- more places where connection shouldn't be reset too quickly ([commit](https://github.com/miguelgrinberg/python-engineio/commit/693b51b2221d59863e2680acbf0f02170bb87a81))

**Release 3.3.0** - 2019-01-23

- do not reset connection when ping loop exits ([commit](https://github.com/miguelgrinberg/python-engineio/commit/dafbdb80ffb5eba0522adc14728bb47e13f0ac54))

**Release 3.2.3** - 2019-01-12

- never import invalid async drivers ([commit](https://github.com/miguelgrinberg/python-engineio/commit/61b04ea89cf2cc358a40f7854c31859aea8e30d6))

**Release 3.2.2** - 2019-01-10

- fixed unreliable unit test ([commit](https://github.com/miguelgrinberg/python-engineio/commit/7e53442afa93d7155c49681050a7aacaaf7222e9))
- Fixes [#236](https://github.com/miguelgrinberg/python-socketio/issues/236) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e6c285882ed023c17e319cf2bd9c3322a524125a))
- fixed handling of queue empty exceptions [#88](https://github.com/miguelgrinberg/python-engineio/issues/88) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/bc128c2e3f41a69d855acabdbdbad072f662df92))

**Release 3.2.1** - 2019-01-09

- add a grace period of 5 seconds to ping timeout ([commit](https://github.com/miguelgrinberg/python-engineio/commit/b5f15e34ed9ef3a9f75d778c67e9bde4265618a7))
- do not use six in setup.py ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c41bb5d0431c0a5d3c49a98392f530a93fd093c0))
- minor refactor of clients for consistency with servers ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d9c278f326db52da1343c0f7fb4257ff7087e83c))
- minor refactor of the async drivers ([commit](https://github.com/miguelgrinberg/python-engineio/commit/0478110179f91f51c6a7a972b3e284b06c3db2ee))

**Release 3.2.0** - 2019-01-03

- unit test reorganization ([commit](https://github.com/miguelgrinberg/python-engineio/commit/3786502ed57920d6b78283bf16150f1711721d38))
- do not block upgrades with high packet traffic [#16](https://github.com/miguelgrinberg/python-engineio/issues/16) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/919d8ea639d5190d345b22168d6cbfbdebc421af))
- user session documentation ([commit](https://github.com/miguelgrinberg/python-engineio/commit/af3a0aa7d5b83f8c407f792cb688ef6f983b056b))
- remove python 3.4 from builds ([commit](https://github.com/miguelgrinberg/python-engineio/commit/8c9bbf4132f4cf4082c96d58a6e7270ad7eea0ff))
- user sessions ([commit](https://github.com/miguelgrinberg/python-engineio/commit/561efad215661bfce3d00ffcb5c3290555de8f12))

**Release 3.1.2** - 2018-12-22

- fixed dependency ([commit](https://github.com/miguelgrinberg/python-engineio/commit/8f8cbfd866086c3689a65bc049e0a9ce597e08c2))
- small documentation updates ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d59648c663e2f54f96a824e947a86f62f45f637d))

**Release 3.1.1** - 2018-12-20

- bug fixes on handling of timeouts in the client ([commit](https://github.com/miguelgrinberg/python-engineio/commit/de1dbbd39f8516a89525282f4d24c7d854ecb321))
- make ping loop task more responsive to cancellation ([commit](https://github.com/miguelgrinberg/python-engineio/commit/6a997b960c985b35f28b5f60f1dc8d9e99e05c08))
- correct handling of disconnect event ([commit](https://github.com/miguelgrinberg/python-engineio/commit/ccf1ddfa132a43fbe147c322608d913ede1d6c75))
- make unit tests compatible with python 3.5 ([commit](https://github.com/miguelgrinberg/python-engineio/commit/aeabccdd59f7d8939c6af47d5357e6545e9525d2))
- do not drop extra packets included in first response ([commit](https://github.com/miguelgrinberg/python-engineio/commit/0ffdb0a31b9b5be8d24d8208521fdd2121cb9a88))

**Release 3.1.0** - 2018-12-14

- initial Engine.IO client implementation
- client examples ([commit](https://github.com/miguelgrinberg/python-engineio/commit/916bd7aa5f8df3a3caf7611133ff82cd2d0cdda7))
- pass custom headers in client connection requests ([commit](https://github.com/miguelgrinberg/python-engineio/commit/6bacd03c9cf997af09f638cbcc9e1add441edc9b))
- restructure async drivers into a subpackage ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4621ff8d6ce8bd2e6dd8381ee9764887970aa056))
- documentation updates ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d014ca534e20ad37c75484ae151e3cec3809c200))

**Release 3.0.0** - 2018-12-01

- ASGI support
- support serving static files in wsgi and asgi middlewares ([commit](https://github.com/miguelgrinberg/python-engineio/commit/0c697591b44f6f849b45cec112e00331bbf537aa))
- refactor wsgi and asgi middlewares ([commit](https://github.com/miguelgrinberg/python-engineio/commit/1f7878536a62f9f5285e0a3ed8a83a9ec379d945))
- minor documentation fixes ([commit](https://github.com/miguelgrinberg/python-engineio/commit/00d713d8094233439e5bb888dd5c3b5ec363a5b1))
- reorganized documentation ([commit](https://github.com/miguelgrinberg/python-engineio/commit/84faa991890f33e8fbb5e5db884674d2dd32b1f3))

**Release 2.3.2** - 2018-10-09

- address potential lock of the service thread ([commit](https://github.com/miguelgrinberg/python-engineio/commit/b702f6f98861e78f8c48f9aaee7b9f941de56d99))
- graceful exit for service task ([commit](https://github.com/miguelgrinberg/python-engineio/commit/2f5cd48f0f574c4cabd63f0b46dd652ff93ffc89))

**Release 2.3.1** - 2018-09-30

- updated requirements file ([commit](https://github.com/miguelgrinberg/python-engineio/commit/2ab69b819bec6bea273b124c91cb2163b13266f3))
- more fixes towards cleaning up abruptly disconnected clients ([commit](https://github.com/miguelgrinberg/python-engineio/commit/759dc5e8a3c4301f68ffe72ac8af8422a4099dad))

**Release 2.3.0** - 2018-09-23

- Actively monitor clients for disconnections ([commit](https://github.com/miguelgrinberg/python-engineio/commit/3f583c88449f88200fa5f484954248bfad517aa8))
- parse integer packets as strings [#75](https://github.com/miguelgrinberg/python-engineio/issues/75) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/6735659d5cca69476e8a7e98a16a7529ab63a604))
- missing unit test ([commit](https://github.com/miguelgrinberg/python-engineio/commit/a51feef59da8fb491b50a05adb665e980dd9eaa9))
- add Python 3.7 to build ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d9d617a5c62cab692fda4b9664750787303de411))
- removed unused import ([commit](https://github.com/miguelgrinberg/python-engineio/commit/ff3403f1216d838e1930d2322c66bcf609f790e8))
- Tornado docs ([commit](https://github.com/miguelgrinberg/python-engineio/commit/0ef4fbfeeb188a76095de2631cdef9ab4f01839d))

**Release 2.2.0** - 2018-06-28

- tornado unit tests ([commit](https://github.com/miguelgrinberg/python-engineio/commit/cb1fe75cea4573dfe3320e5b415c24aaad51d0a0))
- Tornado 5 support ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e0dc7f16c562869d8b48d63f9ee049a413b2f1a2))

**Release 2.1.1** - 2018-05-12

- support OPTIONS request method in aiohttp and sanic [#70](https://github.com/miguelgrinberg/python-engineio/issues/70) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/27261c7d6563bc5c494e9ff345617a923e17452b))
- More flexible specification of CORS allowed origins Suggested in https://github.com/miguelgrinberg/Flask-SocketIO/issues/697#issuecomment-385203087 ([commit](https://github.com/miguelgrinberg/python-engineio/commit/8f3d6ecff45d474da1a407d654d06fd3f8f882a8))

**Release 2.1.0** - 2018-04-27

- basic support for cors allowed headers ([commit](https://github.com/miguelgrinberg/python-engineio/commit/08e3766244b12f704ef20f266f10bdfc7381d43a))
- add pypy3 target to travis builds ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d11b9dae19bf4a5b74b0f6636072e2527a5b8dfe))
- respond to CORS preflight requests [#630](https://github.com/miguelgrinberg/Flask-SocketIO/issues/630) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/eac1e516589604a6831f47959047050af23ff01b))

**Release 2.0.4** - 2018-03-13

- suppress queue empty errors [#65](https://github.com/miguelgrinberg/python-engineio/issues/65) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/861dd52ca2c4fdd9ee1684f1a24bf7acd698039d))

**Release 2.0.3** - 2018-03-06

- more aiohttp unit test fixes ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4fd45b8fb86d287c5ba47e7a74cdfb25fa4acb6a))
- fix aiohttp unit test ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4b3ee9309e0250d428fb2faabbb2aa15d377db12))
- support for aiohttp 3.x ([commit](https://github.com/miguelgrinberg/python-engineio/commit/810e759762dd24afa108c8b714fffdced49d3cc1))

**Release 2.0.2** - 2018-01-04

- fix documentation builds ([commit](https://github.com/miguelgrinberg/python-engineio/commit/107b751f16aafff5842894a6eff26eb6f784ea5c))
- Suppress "socket is closed" stack trace from logs [#57](https://github.com/miguelgrinberg/python-engineio/issues/57) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/7dfc60e91f076e4a70a771cf98f16ceaa3de077c))
- Reraise exceptions in a Py2/Py3 compatible way [#58](https://github.com/miguelgrinberg/python-engineio/issues/58) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4a3320051aac532918b1e0448aad8cc8da615697))

**Release 2.0.1** - 2017-11-21

- Fixed poll() method to always empty the queue [#589](https://github.com/miguelgrinberg/Flask-SocketIO/issues/589) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e8e665b1737987a2b7c59cd6a96464842b864bad))

**Release 2.0.0** - 2017-11-19

- remove double-utf8 encoding hack this hack that made some incorrectly encoded packets sent by the JS socket.io 1.x clients does not always work, and is not needed anymore since the 2.x clients have been fixed. ([commit](https://github.com/miguelgrinberg/python-engineio/commit/83d2277de727e418b0abd1b1115a15307835d582))
- Documented protocol defaults ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e6985ccfa9001aebfa31007dcae70989f2a4792f))

**Release 1.7.0** - 2017-07-02

- cleaner disconnecting of polling clients ([commit](https://github.com/miguelgrinberg/python-engineio/commit/8d541fa2eb2f464b659baf0904de37567120f4bc))
- Support async_handlers option for the asyncio server [#95](https://github.com/miguelgrinberg/python-socketio/issues/95) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/6609416d2a0c7b8e750dcf1634f8a4218f5360e9))

**Release 1.6.1** - 2017-06-27

- Tolerate errors when cleaning up a task cancellation [#110](https://github.com/miguelgrinberg/python-engineio/issues/110) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/a504e6b53fbb963c817755e57164ba07621aa253))

**Release 1.6.0** - 2017-06-23

- better error handling strategy [#49](https://github.com/miguelgrinberg/python-engineio/issues/49) (again and hopefully better) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/8cc004a4a8014924dd822ca14ecabdad4e858c0d))
- Reraise app exceptions with the correct traceback [#49](https://github.com/miguelgrinberg/python-engineio/issues/49) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/66b8f5d63d9583ea1cbd3bb0eb9b4db8f8047ce5))

**Release 1.5.4** - 2017-05-30

- Workaround to prevent the "exception never retrieved" asyncio bug [#48](https://github.com/miguelgrinberg/python-engineio/issues/48) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/dab2d2e9fd33896bbbb772b18323574ddc1b8ce5))

**Release 1.5.3** - 2017-05-29

- Handle buggy and correct encodings for engine.io unicode packets [#102](https://github.com/miguelgrinberg/python-socketio/issues/102) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/efc341ab321209007bddd75333c48d4e74527d53))

**Release 1.5.2** - 2017-05-16

- be a bit more forgiving with socket timeouts ([commit](https://github.com/miguelgrinberg/python-engineio/commit/05da51a41d4a1a7a08e5f19194a248923780fff8))

**Release 1.5.1** - 2017-05-09

- fixed typo ([commit](https://github.com/miguelgrinberg/python-engineio/commit/30445b239227daf88290a972349ba01cd31bd525))

**Release 1.5.0** - 2017-05-09

- another fix in the lost connection detection logic ([commit](https://github.com/miguelgrinberg/python-engineio/commit/73ac2ea7791b79a01974a1ebdb97104f99c1d7a7))
- detect lost connections (asyncio) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/9a96896bbda37613bd8b29ac658427366e5d49be))
- detect lost connections (eventlet/gevent) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e9a3161fdcb7767d77a2370d003f4e74ef3ecd1d))

**Release 1.4.0** - 2017-04-21

- properly handle crashes in connect/disconnect handlers ([commit](https://github.com/miguelgrinberg/python-engineio/commit/5b24410016f334e739690438345782fb5dcece02))
- invoke disconnect handler when websocket handler crashes ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f772cf62193e0dcc8be43814c1bfda7b987a2a15))
- invoke disconnect handler when application handler crashes ([commit](https://github.com/miguelgrinberg/python-engineio/commit/246edc3e84bce055284936745023ed4491897a5b))

**Release 1.3.2** - 2017-04-09

- Accept leading and trailing slashes in engineio_path [#83](https://github.com/miguelgrinberg/python-socketio/issues/83) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/924d3cb7a0416f7ccbc2364cc94dd07234f6f894))
- Use custom exceptions for internal errors [#44](https://github.com/miguelgrinberg/python-engineio/issues/44) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/36814a48a58b6fdb996a0eed42e32e927711e182))
- Fix sanic url parsing [#43](https://github.com/miguelgrinberg/python-engineio/issues/43) According to sanic docs, `request.url` already contains query string, so adding it results in data corruption. This fix worked for me. [#42](https://github.com/miguelgrinberg/python-engineio/issues/42) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/7dda70cb46a0e782d42c0a175ec61d0b95ebced8)) (thanks **Семён Марьясин**!)
- fixed aiohttp unit test ([commit](https://github.com/miguelgrinberg/python-engineio/commit/2b629096cd26378c6755e4db83286a0f573be477))

**Release 1.3.1** - 2017-03-22

- Do not depends on SERVER_SOFTWARE constant from aiohttp [#86](https://github.com/miguelgrinberg/python-socketio/issues/86) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e1136aa4fda888f8f74135a94fadf8ac739cd6ad))
- proper handling of closed sockets ([commit](https://github.com/miguelgrinberg/python-engineio/commit/2144535e9dfe31a17ce6b9d40012d310b34a8c9a))
- use Python 3.6 for docs build ([commit](https://github.com/miguelgrinberg/python-engineio/commit/52b37e50a816635cc363b4655fa984f4519f64e5))
- release 1.3.0 ([commit](https://github.com/miguelgrinberg/python-engineio/commit/51e620e3d49999c8bfff7afa68f712e1ee95bc44))
- Better handling of close packets from the client [#41](https://github.com/miguelgrinberg/python-engineio/issues/41) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/db988f1c24db10db0a5969b0292834c4ac7b8882))
- rename `async` to `_async` to avoid conflicts [#36](https://github.com/miguelgrinberg/python-engineio/issues/36) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/6fcf926ec7ec28a3f97f94ffcc6b665ffbbd6bcc))
- websocket support for sanic ([commit](https://github.com/miguelgrinberg/python-engineio/commit/317472459af6c04d26aa9255c0c8dc71ea81fa53))

**Release 1.2.4** - 2017-03-02

- Use non-blocking reads for uwsgi websocket handles [#417](https://github.com/miguelgrinberg/Flask-SocketIO/issues/417) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4148c9470b8d73fc2b35feeeb2d5048cc52b9250))
- handle unexpected disconnects from uwsgi websocket ([commit](https://github.com/miguelgrinberg/python-engineio/commit/10ebccf6766a85da11fee4447a914ac338401d36))

**Release 1.2.3** - 2017-02-22

- Use correct key name for ACCEPT_ENCODING header [#39](https://github.com/miguelgrinberg/python-engineio/issues/39) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f1df2e4a3595207c9f0e91b67a5131af19c0528f))

**Release 1.2.2** - 2017-02-15

- updated examples readme ([commit](https://github.com/miguelgrinberg/python-engineio/commit/ea9ab79e25a9fbba561782a55aeeb5e76d68137f))
- Fix crash on invalid packet type. Add test [#37](https://github.com/miguelgrinberg/python-engineio/issues/37) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/7eacdd98edfbf5ce7b1f0da0c3d2343cdf1cbffe)) (thanks **Dmitry Voronin**!)
- minor updates to sanic examples ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c39a7751c72a90085d2bc88ab2487cb673724ee1))
- sanic examples ([commit](https://github.com/miguelgrinberg/python-engineio/commit/251485dcea260f38136bf27bb7676430f458c4f0))
- sanic support (long-polling only) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/b2da2283451d558298cae888b9ef148186830a7e))
- updated documentation logo ([commit](https://github.com/miguelgrinberg/python-engineio/commit/54e7115d35de20581e1328eded902c8d40788084))
- ensure iscoroutinefunction works well for mocks ([commit](https://github.com/miguelgrinberg/python-engineio/commit/917df6f57a32e278ee38ef3c6201c90fdab6d061))
- updated requirement files for examples ([commit](https://github.com/miguelgrinberg/python-engineio/commit/20db20f1764d25f50433e088d1d3486994b24139))

**Release 1.2.1** - 2017-02-11

- various minor improvements for asyncio support ([commit](https://github.com/miguelgrinberg/python-engineio/commit/24131a90d0ca5bfdafec0e02ee11ec433e81d44a))
- Fixed asyncio example code [#35](https://github.com/miguelgrinberg/python-engineio/issues/35) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f86847beaff82054f677a4e18c08fb5056b61a78))

**Release 1.2.0** - 2017-02-09

- minor documentation updates ([commit](https://github.com/miguelgrinberg/python-engineio/commit/af2834dd7fb75c579b8e00d155649ce7c71528a1))
- async socket unit tests ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c19c4477377fe0126a6dda8937414f669dc137f9))
- more asyncio unit tests ([commit](https://github.com/miguelgrinberg/python-engineio/commit/039eb59b021ae59347be6a5614709756b915a5d0))
- catch cancelled tasks due to client leaving ([commit](https://github.com/miguelgrinberg/python-engineio/commit/3abadf1962ef433eb62c83d43522a8d636738fde))
- some initial async server unit tests ([commit](https://github.com/miguelgrinberg/python-engineio/commit/5796794ef2d12823f7306d3cf890fac1290da798))
- asyncio documentation ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d1789caa27e509dcdc0cf76c665f5adab4ad1e41))
- reorganized examples ([commit](https://github.com/miguelgrinberg/python-engineio/commit/824cdd541103f2d52e68848c8cacb2dc4df23c11))
- Preliminary asyncio support! Yay! ([commit](https://github.com/miguelgrinberg/python-engineio/commit/cbeb025e808e9935fb979a042f5884c9ab1a4241))

**Release 1.1.2** - 2017-01-30

- Clean websocket exit for uWSGI [#377](https://github.com/miguelgrinberg/Flask-SocketIO/issues/377) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d15842383b1cd0fbaa741c5125b5ef26d1915a7a))

**Release 1.1.1** - 2017-01-23

- Use text/plain content type for base64 encoded responses [#33](https://github.com/miguelgrinberg/python-engineio/issues/33) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/297ff98e0d9f8f3b32ca5d2afe566a80bb16c6d8))
- removed py33 from tests, added py36 ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e0541bcfa069df0f54195a9031630baf7a46c069))
- additional fix regarding bytearray support ([commit](https://github.com/miguelgrinberg/python-engineio/commit/268e3cba424391dd32950d0ba08d28a65c4ef14b))
- Merge branch 'wwqgtxx-patch-1' ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4f25274a0e2e66b2a867b1cdcdf1e820c487e630))
- allow binary packets to be given as bytearrays ([commit](https://github.com/miguelgrinberg/python-engineio/commit/eb8f357082369422464237f47a3c419fb7d14490)) (thanks **wwqgtxx**!)

**Release 1.1.0** - 2016-11-27

- Prevent recursive disconnect handlers [#329](https://github.com/miguelgrinberg/Flask-SocketIO/issues/329) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/84d5800c027fe093db0d7624cbc1e73e176ec221))

**Release 1.0.4** - 2016-11-26

- Use a statically allocated logger by default ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e6b3a6d8bce3d7f53fde7b56037fd9e9f7cbe492))
- fix unit test to work on python 2.7 ([commit](https://github.com/miguelgrinberg/python-engineio/commit/aab2182cea4f4fd3c64b512b443d6f0f3f35a5a9))

**Release 1.0.3** - 2016-09-05

- workaround double utf-8 encode bug in javascript client [#315](https://github.com/socketio/engine.io/issues/315) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/00d2459fcc7d89c7f35a2b3734b339c0fc148b1f))
- upgrade to a more recent engineio.js for the examples ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d61c3ac9d6abd0e0af4518bd6486ec5c218f3ba9))
- do not close a socket that is already closed [#312](https://github.com/miguelgrinberg/Flask-SocketIO/issues/312) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/ef20ffcf9abc074493501b284ef2289cfaf6417d))

**Release 1.0.2** - 2016-09-04

- add __version__ to package ([commit](https://github.com/miguelgrinberg/python-engineio/commit/8e1f4e0b3cbfda8d1ac1dcae7102e9f1b3046c88))

**Release 1.0.1** - 2016-09-01

- corrected logic that selects gevent_uwsgi as async mode [#28](https://github.com/miguelgrinberg/python-engineio/issues/28) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/db2fb14a252f0b142525d734bf60f665cb043367))
- documentation fixes ([commit](https://github.com/miguelgrinberg/python-engineio/commit/43fbe9a52e0a36c2cc73cf6e8064c55083c5ad61))

**Release 1.0.0** - 2016-08-26

- updated Server class docstring ([commit](https://github.com/miguelgrinberg/python-engineio/commit/8b5304808bf62cd5215a4e75d1a3c97b07615ec9))
- added async_handlers option to server ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c9133c2392baee13d7e3234d8aebfe550f106131))
- documentation for new gevent_uwsgi async_mode ([commit](https://github.com/miguelgrinberg/python-engineio/commit/3f0b4e3a5cb1f221702b4182c4dda7b91a1fdbd0))
- add unit test for complete code coverage ([commit](https://github.com/miguelgrinberg/python-engineio/commit/36bb48c66b3b54635f55c77cf7b54c9bbc006b84))
- Merge branch 'efficiosoft-uwsgi-gevent-support' ([commit](https://github.com/miguelgrinberg/python-engineio/commit/ad64b54be24e5df17b4e08150693997eb404c0f1))
- Added websocket support for uWSGI with gevent ([commit](https://github.com/miguelgrinberg/python-engineio/commit/8f92f4eba2f94d9388a98fadc38b95611a49056d)) (thanks **Robert Schindler**!)
- minor updates to readme file ([commit](https://github.com/miguelgrinberg/python-engineio/commit/298310af53f1e8bc87468d1b3ed1f146167c090a))

**Release 0.9.2** - 2016-06-28

- minor comment additions to examples ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c85d06ebb3c5414c2b6b28a900e0e6d5f1916dd5))
- async message events, sleep function, better client timeout Several improvements in this commit: 1. Message event handlers are invoked in a thread so that they are non-blocking. 2. Added a sleep function that is generic across async modes. 3. The timeout to declare a client gone has been extended to match the ping timeout setting. ([commit](https://github.com/miguelgrinberg/python-engineio/commit/6670627ea404679fc794b496c21ffce689fc6151))

**Release 0.9.1** - 2016-05-15

- do not crash if recipient of a message is gone ([commit](https://github.com/miguelgrinberg/python-engineio/commit/95c9a55457e9cbd36597b14ad840e31abdb2030e))

**Release 0.9.0** - 2016-03-06

- Correct generation of binary xhr2 packets ([commit](https://github.com/miguelgrinberg/python-engineio/commit/5e5e0a34faa218de32b5bf7a2358d12a3fd6493d))
- Do not write binary packets to the log ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d338ee8787738aab7b7b2fcac9b31127dcb2e9b1))
- Hopefully addressed some tests that fail intermittently on travis ([commit](https://github.com/miguelgrinberg/python-engineio/commit/27bc79f91ad32a90f6f3ea8bd87cead8f4a14f41))

**Release 0.8.8** - 2016-02-21

- Dispose of disconnected sockets ([commit](https://github.com/miguelgrinberg/python-engineio/commit/08c518db6c6dd12d81890cd6239113cfd84e9eec))
- disable imports warning in flake8 ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e3badf30f89e4981ed419cf645ccec976370c376))

**Release 0.8.7** - 2016-01-26


**Release 0.8.6** - 2016-01-10

- Graceful failure when websocket is request and the async mode does not support it ([commit](https://github.com/miguelgrinberg/python-engineio/commit/2a5cdf289d2f1af97270f3bbf58669a507aecb9c))

**Release 0.8.5** - 2016-01-02

- additional eventlet unit test ([commit](https://github.com/miguelgrinberg/python-engineio/commit/abd54e58d274355d961ed9272d7b7fda9e3ef9fc))
- Update tests to correspond with flake8 ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d1969d6bc016b0e3dc66df7eeb30a9c76debc6b6)) (thanks **Artemiy Rodionov**!)
- Fix eventlet wsgi websocket __call__ return [#12](https://github.com/miguelgrinberg/python-engineio/issues/12) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/3f8ecccd40c3f05ef966a6f7e0e2953dc992dfa6)) (thanks **Artemiy Rodionov**!)

**Release 0.8.4** - 2015-12-18

- Revert "_websocket_handler waits on writer even after the socket is closed" [#11](https://github.com/miguelgrinberg/python-engineio/issues/11) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/a4ffc8e916aabdc96b0cc7bb5262baf8bd39c661))

**Release 0.8.3** - 2015-12-14

- _websocket_handler waits on writer even after the socket is closed This patch wakes up the writer with a null message when the socket gets closed ([commit](https://github.com/miguelgrinberg/python-engineio/commit/0c439be734b29b1006b7c6d43f1acc6d2260ed9c)) (thanks **Babu Shanmugam**!)

**Release 0.8.2** - 2015-12-13

- Runtime error when websocket is missing from environment ([commit](https://github.com/miguelgrinberg/python-engineio/commit/2ba8a89df6558f088d2cccb541602893929954c0))

**Release 0.8.1** - 2015-12-03

- fix python 3.5 build ([commit](https://github.com/miguelgrinberg/python-engineio/commit/bba8f4bb39634b1523e6932f4b6378251dc0d401))
- tolerate payloads in UPGRADE packet [#7](https://github.com/miguelgrinberg/python-engineio/issues/7) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/0193b5c9935f9dd56e48610499ea6b528cf09582))

**Release 0.8.0** - 2015-11-21

- expose start_background_thread() as a public method ([commit](https://github.com/miguelgrinberg/python-engineio/commit/16aa518d565b7af12c3de07d3416700da5bc99ec))
- Added python 3.5 to the tox build ([commit](https://github.com/miguelgrinberg/python-engineio/commit/5be3c32d2688655891b203aef2d0a31b2b536d6a))

**Release 0.7.2** - 2015-11-04

- Correctly end eventlet's websocket connection See miguelgrinberg/flask-socketio[#167](https://github.com/miguelgrinberg/python-engineio/issues/167) for the problem this fixes. ([commit](https://github.com/miguelgrinberg/python-engineio/commit/fef4b4739d074cebc741d58e099d8b6459e96112))

**Release 0.7.1** - 2015-10-19

- More robust handling of the upgrade exchange ([commit](https://github.com/miguelgrinberg/python-engineio/commit/66b4bc14cb514230799e116a08410e4c3b1deb15))

**Release 0.7.0** - 2015-10-17

- Add kwargs to server constructor ([commit](https://github.com/miguelgrinberg/python-engineio/commit/933ef62fcfd7dedced4b5660084b172181fb4cc9))

**Release 0.6.9** - 2015-10-16

- Give eventlet access to the socket when running under gunicorn ([commit](https://github.com/miguelgrinberg/python-engineio/commit/3c63157f14c2c7443aa2fa8f339bd9afdadb8fa4))

**Release 0.6.8** - 2015-10-07

- Raise a runtime error when gevent-websocket's custom server is not used ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e38cad9d1fb5924db48db4e6632fb756ef6f9767))

**Release 0.6.7** - 2015-09-26

- Better handling of connection state ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c3715e6e6e401d6bc217a99573a8d3b90cf025b1))
- Small improvements to example apps ([commit](https://github.com/miguelgrinberg/python-engineio/commit/48d999d75e60ef2a11f5db6007385046702f50fa))
- Correctly set state of socket connected directly with websocket transport ([commit](https://github.com/miguelgrinberg/python-engineio/commit/86ed25d19fe6f97d7906891172a44f7d0c5fe185))
- Add wrapper to create threads compatible with the selected async mode ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d20c114e6b5bae6d23e756fe4dedb9293d63bdbc))

**Release 0.6.6** - 2015-09-06

- Accept direct websocket connections ([commit](https://github.com/miguelgrinberg/python-engineio/commit/448acfb367c5d9bae464bf7175e77205a970380b))
- Fix executable bit, once again ([commit](https://github.com/miguelgrinberg/python-engineio/commit/fbc018f9a7592f166647ffa4dec3c534769705db))

**Release 0.6.5** - 2015-09-02

- Added transport() method ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f3aeeb51eed439dad82f7fc808a79e6a6718d261))

**Release 0.6.4** - 2015-09-01

- Preserve exception in case it is lost before it is re-reaised ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f0c2f5b444b57c7b80f262e90fcd608cd3af2deb))
- Added a port of the "latency" example from the official Javascript client ([commit](https://github.com/miguelgrinberg/python-engineio/commit/b976ff304e045aa375ec3f9f1f8f17483b2d1934))
- Allow application to provide a custom JSON encoder/decoder. ([commit](https://github.com/miguelgrinberg/python-engineio/commit/1e8fab676f83eab1b82778ab6dcd362609301d57))

**Release 0.6.3** - 2015-08-30

- added b64 unit tests ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c270acf1da2eb39e12049b86e58287aa9ce0dd71))
- Added b64 checks and encoding during initial connect [#4](https://github.com/miguelgrinberg/python-engineio/issues/4) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/ac90ed68668f617f347c08d0ea4c37ea56ac12c3)) (thanks **Myles Ringle**!)

**Release 0.6.2** - 2015-08-23

- Improved handling of logging ([commit](https://github.com/miguelgrinberg/python-engineio/commit/142b9a66e1e29e5069696a8a2e9757bcb394b268))
- Make gevent websocket optional in example app ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c6b1ae91e2e7c3ee8dfec3caf8a8dfa8c2800aa2))

**Release 0.6.1** - 2015-08-20

- Make gevent thread arguments optional ([commit](https://github.com/miguelgrinberg/python-engineio/commit/3c4f10f266e694380104234294b9ccf2730c1263))

**Release 0.6.0** - 2015-08-20

- Add WebSocket support for gevent (Idea derived from pull request [#1](https://github.com/miguelgrinberg/python-engineio/issues/1) by @drdaeman) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/96dc09b0119a816aada9ad787344ccc912608d55))
- Made parsing of HTTP connection header more robust ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f1ce5e0f5b904e44d587d6dc5aab44800f73cf40))
- Refactored the three async modes as separate modules for greater flexibility (Idea derived from pull request [#1](https://github.com/miguelgrinberg/python-engineio/issues/1) by @drdaeman) ([commit](https://github.com/miguelgrinberg/python-engineio/commit/a85ac4c97e5a5e0d2ecdfd273673b479c0b6c7ff))
- Fix executable bit on several files ([commit](https://github.com/miguelgrinberg/python-engineio/commit/47bc67efc86c3043f4b3c786eea9776a04222e04))

**Release 0.5.1** - 2015-08-17

- Correct handling of CORS origin header ([commit](https://github.com/miguelgrinberg/python-engineio/commit/394a87877e49424461a2c4053e9ce8c216c093b8))
- minor improvements to the example application ([commit](https://github.com/miguelgrinberg/python-engineio/commit/c02a58795bb133f4eb80e7f4d0c64c3a9281c7c3))
- documentation improvements ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f9eaa604d3025aa88a075ab13908ad27ca2b32f1))

**Release 0.5.0** - 2015-08-04

- Support for gevent and threading in addition to eventlet. Also improved example application. ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e72e4883a7301b8dc4bc1128597191d167776331))

**Release 0.4.0** - 2015-08-03

- ensure all HTTP response payloads are returned as bytes ([commit](https://github.com/miguelgrinberg/python-engineio/commit/d38d57f6af139a02adeb5e73f8a3308542ffc3a7))
- Added robustness when dealing with disconnected clients ([commit](https://github.com/miguelgrinberg/python-engineio/commit/7b39dbb6c547ed9dde19f4537e6b3f8e725a4fb6))
- removed assert_called_once from tests ([commit](https://github.com/miguelgrinberg/python-engineio/commit/e6f1b8b7f6c5acb1f37f595cd9696bc5d855c987))
- Added logging for websocket upgrade ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4b5cecab56f4891040f7da04ced523ea50cb8dca))
- Fixed incorrect unit test ([commit](https://github.com/miguelgrinberg/python-engineio/commit/583736a3af266d15c31ee03546f11d018fb97e42))
- rename close() to disconnect() for consistency ([commit](https://github.com/miguelgrinberg/python-engineio/commit/12cc2830374a4848127614f1a21fe8712574219b))

**Release 0.3.1** - 2015-07-04

- Switch README to rst format ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4fb16f8574004ad5b846d81eb9a9d958b448a7da))
- minor documentation and code fixes ([commit](https://github.com/miguelgrinberg/python-engineio/commit/f0e6be6ce16e98f270327a516754ec4d18d7b2f1))

**Release 0.3.0** - 2015-07-04

- Better support for unicode in Python 2 ([commit](https://github.com/miguelgrinberg/python-engineio/commit/9fb200cbf81992cc6cc1cf8f1c9fc15471e5f0f9))
- allow connect event handler to send data to client ([commit](https://github.com/miguelgrinberg/python-engineio/commit/a0dbf69fec47db0bfdca6585267eed21bfc2da91))

**Release 0.2.0** - 2015-06-29

- Added non-decorator format for Server.on() ([commit](https://github.com/miguelgrinberg/python-engineio/commit/2d8d41c514f317e4c2e347030d82c351fbe0fb4e))
- declared vendered js file ([commit](https://github.com/miguelgrinberg/python-engineio/commit/584aba250334fe10949cefbbb99afff89222f024))
- Added pypy to travis builds ([commit](https://github.com/miguelgrinberg/python-engineio/commit/b982ed13d64ece4c76c6af323e2b29db4bdabfdf))
- minor documentation updates ([commit](https://github.com/miguelgrinberg/python-engineio/commit/a25b639ea3e833a28725fd22b36de5b5f6973744))
- Initial commit ([commit](https://github.com/miguelgrinberg/python-engineio/commit/4303b86e4f363e746957e6adecea303089e90f70))
- initial version ([commit](https://github.com/miguelgrinberg/python-engineio/commit/1d53a103ffcc43d1482fecb489d748c1ffaadbe0))
