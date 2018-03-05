import re

comments = re.compile("#[^\n]*")
_token = re.compile('[a-zA-Z][a-zA-Z_]*|\^|\,|\:|\=|\-|\~|\?|\!|\(|\)|\{|\}|\~|\n|\d+|\.|\>|\<')


def token(strings):
    return _token.findall(comments.sub('', strings))


if __name__ == '__main__':
    with open('db.def', 'r') as f:
        s = f.read()
    s = comments.sub('', s)
    print(s)
    print(token.findall(s))
