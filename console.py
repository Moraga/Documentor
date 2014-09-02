import json
from glob import glob

pth = '//set/your/path/'

blocks = []

for f in glob(pth + '*.json'):
    try:
        f = open(f, 'r').read()
        blocks.extend(json.loads(f)['blocks'])
    except IOError as e:
        pass

bcodes = [block for block in blocks if block['code']]
tmp = []

def princ(block):
    print('===== ['+ block['name'] + ' line: ' +  str(block['line']) +'] =====\n\n' + block['data'] + '\n')

while True:
    try:
        ipt = input()
        
        if ipt:
            print('\n')
            try:
                idx = int(ipt)
                src = tmp if tmp else bcodes
                tmp = []
                princ(src[idx])
            except:
                tmp = [block for block in bcodes if ipt in block['data']]
                if not tmp:
                    print('Not found.\n')
                elif len(tmp) == 1:
                    print("aqui")
                    princ(tmp[0])
                else:
                    print('\n'.join(['%d) %s' % (i, block['code']) \
                                     for i, block in enumerate(tmp)]) + '\n')
        else:
            tmp = []
            print('\n'.join(['%d) %s' % (i, block['code']) \
                             for i, block in enumerate(bcodes)]) + '\n')
    except:
        exit()
