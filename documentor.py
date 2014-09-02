from re import sub

class Doc:
   def __init__(self):
      self.blocks = []
   
   def append(self, block):
      self.blocks.append(block)

class Block:
   def __init__(self, line):
      self.name = 'text'
      self.data = ''
      self.code = ''
      self.line = line
      self.tags = {}
      self.params = []
   
   def append(self, type, data):
      data = data.rstrip()
      try:
         param = globals()[type.title() + 'Param'](type, data)
      except:
         param = Param(type, data)
      param.block = self
      param.parse()
      # set block definition
      if param.dfn:
         self.name = param.dfn
      # add param tags
      if param.tags:
         if type in self.tags:
            self.tags[type] += param.tags
         else:
            self.tags[type] = param.tags
      self.params.append(param)

class Param:
   dfn = ''
   def __init__(self, type, data):
      self.type = type
      self.data = data
      self.tags = ''

   def parse(self):
      pass

   def __str__(self):
      return '%s %s' % (self.type, self.data)

class VersionParam (Param):
   dfn = ''
   def parse(self):
      try:
         spc = self.data.index(' ')
         self.version = self.data[:spc]
         self.data = self.data[:spc+1]
      except:
         self.version = self.data
         self.data = ''

class SinceParam (Param):
   dfn = ''
   def parse(self):
      self.tags = [self.data]

class ParamParam (Param):
   dfn = 'method'
   def parse(self):
      data = self.data.split(' ', 2)
      self.var_type = data[0].strip('{}')
      self.var_name = data[1]
      self.data = data[2] if len(data) == 3 else '(empty)'
      self.tags = [self.var_type, self.var_name]

class ReturnParam (Param):
   dfn = 'method'
   def parse(self):
      data = self.data.split(' ', 1)
      self.ret_type = data[0].strip('{}')
      self.data = data[1] if len(data) == 2 else ''
      self.tags = [self.ret_type]

class VarParam (Param):
   dfn = 'property'
   def parse(self):
      self.default = ''
      spc = self.data.find(' ')
      if  spc > -1:
         self.block.data = self.data[spc+1:]
         self.data = self.data[0:spc]

class ExampleParam (Param):
   pass

class CategoryParam (Param):
   pass

class LinkParam (Param):
   def __str__(self):
      return '<i>link</i> <a href="%s" target="_blank">%s</a>' % (self.data, self.data)

class DefaultParam (Param):
   def parse(self):
      self.tags = [self.data]

def parse(chs):
   doc = Doc()
   block = None
   param = ['', '']

   stw = '/**'
   enw = '*/'
   cur = 0
   lns = 0
   skp = True
   prs = 0
   bkt = 0
   qut = ''
   tmp = ''

   for c in chs:
      # count line numbers
      if c == '\n':
         lns += 1
      
      # reading comment block
      if prs > 0:
         # maching end of block
         if c == enw[cur]:
            cur += 1
            # matched
            if cur == len(enw):
               block.append(*param)
               doc.append(block)
               param = ['', '']
               prs = 0
               cur = 0
               continue
         else:
            cur = 0

         if skp and c in ('\n', '\t', ' ', '*'):
            continue
         else:
            skp = False

         # new param
         if c == '@':
            if prs == 3:
               block.append(*param)
               param = ['', '']
            prs = 2
         # param type
         elif prs == 2:
            if c == ' ' or c == '\n':
               prs = 3
            else:
               param[0] += c
         # param value
         elif prs == 3:
            param[1] += c
         # block text
         else:
            block.data += c

         # skip after new lines
         if c == '\n':
            skp = True

      # reading code
      else:
         # matching comment block
         if c == stw[cur]:
            cur += 1
            # matched
            if cur == len(stw):
               block = Block(lns)
               prs = 1
               cur = 0
               skp = True
               bkt = 0
               tmp = ''
               continue
         else:
            cur = 0
         
         # code complement for previous block
         if block:
            # variable or property
            if block.name == 'property':
               # quoted
               if qut:
                  if c == qut:
                     qut = ''
               # quotes
               elif c in ('"', "'"):
                  qut = c
               # new bracket
               elif c in ('(', '[', '{'):
                  bkt += 1
               # end bracket
               elif c in (')', ']', '}'):
                  bkt -= 1
               elif not bkt:
                  if c in ('=', ':'):
                     block.code = tmp.strip()
                     tmp = ''
                     continue
                  # ignore spaces
                  elif c in (' ', '\n', '\t') and not tmp:
                     continue
                  # code end
                  elif c in (';', ',', ' ', '\n', '\t') and block.code:
                     if 'default' not in block.tags:
                        block.append('default', tmp)
                     block = None
                     tmp = ''
                     continue
               tmp += c
            # function or method
            elif block.name == 'method':
               if c == '(':
                  block.code = sub(r'\b(def|function|var|#macro)\b|=|:', '', tmp).strip()
                  block = None
                  tmp = ''
               else:
                  tmp += c
            else:
               block = None
   return doc

def doctohtml(doc):
   vrs = ''
   cat = []
   txt = ''
   prp = ''
   mtd = ''
   bid = 0

   for block in doc.blocks:
      bid += 1
      
      # default
      txt += '<div id="i'+ str(bid) +'" class="'+ block.name +'">'
      txt += '<samp>'+ str(block.line) +'</samp>'

      if block.code:
         txt += '<h2>'+ block.code +'</h2>'

      txt += '<p>'+ block.data.replace('\n', '<br/>') +'</p>'
      
      # parts
      typ = ''
      prm = ''
      ret = ''
      oth = ''
      
      if block.name == 'property' and block.code:
         txt += '<code>'
         txt += block.code
         if 'default' in block.tags:
            txt += ' = '+ block.tags['default'][0]
         txt += '</code>'
         
         prp += '<li rel="'+ str(bid) +'">'+ block.code +'</li>'
      elif block.name == 'method' and block.code:
         txt += '<code>'
         txt += '<q>%s</q> ' % (block.tags['return'][0] if 'return' in block.tags else 'void')
         txt += block.code + ' ( '
         if 'param' in block.tags:
            txt += ', '.join(['<q>%s</q> <var>%s</var>' % (k, v) \
                              for k, v in zip(block.tags['param'][0::2], block.tags['param'][1::2])])
         else:
            txt += '<q>void</q>'
         txt += ' )</code>'

         # methods reference
         mtd += '<li rel="'+ str(bid) +'">'+ block.code +'</li>'

      for param in block.params:
         if isinstance(param, VersionParam):
            vrs += '<li>' + param.version
            for sblock in doc.blocks:
               rel = ''
               if 'since' in sblock.tags and param.version in sblock.tags['since']:
                  rel += '<li>'+ sblock.name +'</li>'
               if rel:
                  vrs += '<ul>'+ rel +'</ul>'
            vrs += '</li>'
         elif isinstance(param, DefaultParam):
            continue
         elif isinstance(param, ExampleParam):
            txt += '<pre>'+ param.data +'</pre>'
         elif isinstance(param, ParamParam):
            prm += '<dt>'+ param.var_name +'</dt>' +\
                   '<dd>'+ param.data +'</dd>'
         elif isinstance(param, ReturnParam):
            ret += param.data.replace('\n', '<br/>')
         elif isinstance(param, VarParam):
            typ += param.data
         else:
            oth += '<li title="'+ param.type +'">'+ param.data +'</li>'
            
         if isinstance(param, CategoryParam) and not param.data in cat:
            cat.append(param.data)

      # type required
      if typ:
         txt += '<h3>Type</h3>' +\
                '<p>'+ typ +'</p>'
      
      # parameters
      if prm:
         txt += '<h3>Parameters</h3>' +\
                '<dl>'+ prm +'</dl>'
      
      # return value
      if ret:
         txt += '<h3>Return value</h3>' +\
                '<p>'+ ret +'</p>'
      
      # other parameters
      if oth:
         txt += '<ol>'+ oth +'</ol>'

      txt += '</div>'
            
   return \
      '<!doctype html>' +\
      '<html>' +\
      '<meta charset="utf-8"/>' +\
      '<link href="http://www.moraga.com.br/Documentor/style.css" rel="stylesheet"/>' +\
      '<body>' +\
      '<nav>' +\
      '	<ul id="version">'+ vrs +'</ul>' +\
      '	<ul id="category">'+ ''.join(['<li>%s</li>' % v for v in cat]) +'</ul>' +\
      '	<ul id="method">'+ mtd +'</ul>' +\
      '	<ul id="property">'+ prp +'</ul>' +\
      '</nav>' +\
      '<main>'+ txt +'</main>' +\
      '<script src="http://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js"></script>' +\
      '<script src="http://www.moraga.com.br/Documentor/script.js"></script>' +\
      '</body>' +\
      '</html>'

def doctowiki(doc):
   txt = ''
   for block in doc.blocks:
      typ = ''
      prm = ''

      if block.code:
         txt += 'h3. ' + block.code + '\n\n'
      txt += block.data + '\n'

      if block.name == 'property':
         txt += '{{'
         txt += block.code
         if 'default':
            txt += ' = ' + block.tags['default'][0]
         txt += '}}\n'
      elif block.name == 'method':
         txt += '{{'
         txt += '*%s* ' % (block.tags['return'][0] if 'return' in block.tags else 'void')
         txt += block.code + ' ( '
         # parameters
         if 'param' in block.tags:
            txt += ', '.join(['_%s_ %s' % (k, v) \
                              for k, v in zip(block.tags['param'][0::2], block.tags['param'][1::2])])
         else:
            txt += 'void'
         txt += ' ) '
         txt += '}}\n'
      
      for param in block.params:
         if isinstance(param, VarParam):
            pass
         elif isinstance(param, ParamParam):
            prm += '|'.join(['', param.var_name, param.var_type, param.data, '']) +'\n'

      txt += '\n'

      if prm:
         txt += '||Parametro||Tipo||Descricao||\n' + prm
      
      txt += '\n\n'
   return txt

def doctojson(doc):
    import json
    
    data = {'blocks': []}
    for block in doc.blocks:
        tmp = {
            'name': block.name,
            'code': block.code,
            'line': block.line,
            'data': block.data
        }

        ext = ''
        prm = []
        ret = ''
        exm = []

        if block.code:
            if block.name == 'property':
                pass
            elif block.name == 'method':
                ret = block.tags['return'][0] if 'return' in block.tags else 'void'
                ext += '  ' + ret + ' '
                ext += block.code
                ext += ' ( '
                if 'param' in block.tags:
                    ext += ', '.join(['%s %s' % (k, v) \
                                       for k, v in zip(block.tags['param'][0::2], block.tags['param'][1::2])])
                else:
                    ext += 'void'
                ext += ' )\n'
        
        for param in block.params:
            if isinstance(param, DefaultParam):
                pass
            elif isinstance(param, ParamParam):
                prm.append('  %s (%s)\n    %s' % (param.var_name, param.var_type, param.data))
            elif isinstance(param, ReturnParam):
                ret = '  (%s) %s' % (param.ret_type, param.data)
            elif isinstance(param, ExampleParam):
                exm.append(param.data)

        if prm:
            ext += '\n\nParameters:\n...........\n\n' + '\n\n'.join(prm) + '\n'

        if ret:
            ext += '\n\nReturn:\n.......\n\n' + ret + '\n'
        
        if exm:
            ext += '\n\nExamples:\n.........\n\n' + '\n\n'.join(exm) + '\n'

        if ext:
            tmp['data'] += '\n' + ext

        data['blocks'].append(tmp)
            
    return json.dumps(data, indent=4)

def io():
   while True:
      try:
         flo = input('Filename: ')
      except:
         exit()

      try:
         chs = open(flo, 'r').read()
      except IOError as e:
         print(e.strerror)
         continue

      try:
         fmt = input('\n[1] Confluence\n[2] html (default)\nFormat: ')
         if fmt == '1':
            fnc = 'doctowiki'
            ext = 'txt'
         else:
            fnc = 'doctohtml'
            ext = 'html'
      except:
         exit()

      try:
         fls = input('Save ['+ flo +'.doc.'+ ext +']: ')
      except:
         pass

      if fls:
         if flo == fls:
            print('Error. Can not override the original file')
            exit()
      else:
         fls = flo + '.doc.' + ext

      doc = parse(chs)

      try:
         f = open(fls, 'w')
         f.write(globals()[fnc](doc))
         f.close()
      except:
         print('Error. Can not save.')
      break

def io2():
    pth = '//set/your/path/'

    while True:
        try:
            flo = input('Filename: ')
            fls = pth + flo.split('/')[-1]
            chs = open(flo).read()
            doc = parse(chs)
            
            # html
            f = open(fls + '.html', 'w')
            f.write(doctohtml(doc))
            f.close()

            # confluence
            f = open(fls + '.txt', 'w')
            f.write(doctowiki(doc))
            f.close()
        
            # json
            f = open(fls + '.json', 'w')
            f.write(doctojson(doc))
            f.close()
        except:
            exit()

if __name__ == '__main__':
    io2()

