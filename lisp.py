import re

def parse(s):
    t = re.findall(r'[^\s()]+|[()]', s)
    def p(i):
        if t[i] == '(':
            L = []
            i += 1
            while t[i] != ')':
                x, i = p(i)
                L.append(x)
            return L, i + 1
        try:
            return int(t[i]), i + 1
        except:
            return t[i], i + 1
    return p(0)[0]

def ev(x, env):
    if isinstance(x, str):                      # 变量
        return env[x]
    if not isinstance(x, list):                 # 字面量
        return x
    if x[0] == 'quote':                         # (quote x)
        return x[1]
    if x[0] == 'if':                            # (if test conseq alt)
        return ev(x[2] if ev(x[1], env) else x[3], env)
    if x[0] == 'define':                        # (define var exp)
        env[x[1]] = ev(x[2], env)
        return
    if x[0] == 'lambda':                        # (lambda (params) body)
        return lambda *a: ev(x[2], dict(env, **dict(zip(x[1], a))))
    # 函数调用
    return ev(x[0], env)(*[ev(a, env) for a in x[1:]])

env = {
    '+': lambda *a: sum(a),
    '-': lambda a, b: a - b,
    '*': lambda *a: __import__('math').prod(a),
    '/': lambda a, b: a // b,
    '=': lambda a, b: a == b,
    '<': lambda a, b: a < b,
    '>': lambda a, b: a > b,
}

while True:
    try:
        print(ev(parse(input('> ')), env))
    except Exception as e:
        print(e)
