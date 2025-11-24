class Env:
    def __init__(self, **builtins):
        self.vals = dict(builtins)
    
    def __repr__(self):
        return '[\n' + '\n'.join([f'    {k}: {v}' for k, v in self.vals.items()]) + '\n]'
    
    def __getitem__(self, key):
        return self.vals[key]
    
    def __setitem__(self, key, val):
        self.vals[key] = val
    
    def __contains__(self, key):
        return key in self.vals

if __name__ == '__main__':

    print(k)

    k['test'] = 5

    print(k)
    print(k['copyright'])