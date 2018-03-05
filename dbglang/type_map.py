mapping = {
    'int': 'Integer',
}

mapping.update(dict(TinyStr="String(20)",
              NameStr="String(50)",
              TextStr="String(200)",
              InfoStr="String(500)"
              ))


def type_map(t: str):
    ret = mapping.get(t)
    if ret:
        return ret
    return t
