content_types = {
    'css': 'text/css',
    'gif': 'image/gif',
    'html': 'text/html',
    'jpg': 'image/jpeg',
    'js': 'application/javascript',
    'json': 'application/json',
    'png': 'image/png',
    'txt': 'text/plain',
}


def get_static_file(path, static_files):
    """Return the local filename and content type for the requested static
    file URL.

    :param path: the path portion of the requested URL.
    :param static_files: a static file configuration dictionary.

    This function returns a dictionary with two keys, "filename" and
    "content_type". If the requested URL does not match any static file, the
    return value is None.
    """
    if path in static_files:
        f = static_files[path]
    else:
        f = None
        rest = ''
        while path != '':
            path, last = path.rsplit('/', 1)
            rest = '/' + last + rest
            if path in static_files:
                f = static_files[path] + rest
                break
            elif path + '/' in static_files:
                f = static_files[path + '/'] + rest[1:]
                break
    if f:
        if isinstance(f, str):
            ext = f.rsplit('.')[-1]
            f = {'filename': f}
        if 'content_type' not in f:
            f['content_type'] = content_types.get(
                ext, 'application/octet-stream')
    return f
