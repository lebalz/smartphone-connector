class DictX(dict):
    '''
    dict with the ability to access keys over dot notation,
    e.g.

    ```py
    data = DictX({
        "foo": "bar"
    })

    print(data.foo)     # use dot to get
    data.foo = 'blaa'   # use dot to assign
    del data.foo        # use dot to delete
    ```
    credits: https://dev.to/0xbf/use-dot-syntax-to-access-dictionary-key-python-tips-10ec
    '''

    def __getitem__(self, key):
        try:
            val = dict.__getitem__(self, key)
            if type(val) is dict:
                return DictX(val)
            return val
        except KeyError as k:
            # deepcopy does not work propperly when no AttributeError is raised here!!!
            raise AttributeError(k)

    def __getattr__(self, key):
        try:
            if type(self[key]) is dict:
                return DictX(self[key])
            return self[key]
        except KeyError as k:
            pass

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __repr__(self):
        return '<DictX ' + dict.__repr__(self) + '>'


if __name__ == '__main__':
    a = DictX({'a': DictX({'b': 12, 'c': {'a': 113}})})
    a['b'] = {'c': 18}
    print(a['b'])
    print(a.b)
    print(a['a'])
    print(a.a)
    print(a.a.b)
    print(a['a']['c'])
    print(a.a.c.a)
