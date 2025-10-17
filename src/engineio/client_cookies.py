from http.cookies import SimpleCookie


def decode_cookie_string(cookie_string: str) -> dict:
    c = SimpleCookie()
    c.load(cookie_string)
    return {
        morsel.key: morsel.value for morsel in c.values()
    }


def encode_cookie_dict(cookie_dict: dict) -> str:
    c = SimpleCookie()
    c.load(cookie_dict)
    result = []
    for morsel in c.values():
        result.append(
            "%s=%s" % (morsel.key, morsel.coded_value)
        )
    return '; '.join(result)
