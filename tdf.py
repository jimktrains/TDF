import datetime
import binascii
import email
import re

class Int:
    @staticmethod
    def unmarshall(x):
        return int(x)
    @staticmethod
    def marshall(x):
        return str(x)

class Flt:
    @staticmethod
    def unmarshall(x):
        return float(x)
    @staticmethod
    def marshall(x):
        return str(x)

class Text:
    @staticmethod
    def unmarshall(x):
        return x
    @staticmethod
    def marshall(x):
        return x
class Plain:
    @staticmethod
    def unmarshall(x):
        return x
    @staticmethod
    def marshall(x):
        return x
class EncUTF8:
    @staticmethod
    def unmarshall(x):
        return x
    @staticmethod
    def marshall(x):
        return x

class Dec:
    @staticmethod
    def unmarshall(x):
        return x
    @staticmethod
    def marshall(x):
        return x

class TDF:
    types = {
        'integer': Int,
        'float': Flt,
        'text': Text,
    }
    formats = {
        'dec': Dec,
        'plain': Plain,
    }
    encodings = {
        'utf8': EncUTF8,
    }

    @staticmethod
    def escape(x):
        x = x.replace(',', '$%') 
        x = x.replace(';', '%$')
        x = x.replace('$', '$$')
        x = x.replace('%', '%%')
        return x
    @staticmethod
    def unescape(x):
        x = x.replace('$%',',')
        x = x.replace('%$',';')
        x = x.replace('$$','$')
        x = x.replace('%%','%')
        return x

    @staticmethod
    def find_err_default(lst, field, val, dft):
        if val in field:
            if field[val].lower() in lst:
                field[val] = lst[field[val].lower()]
            else:
                raise Exception("Field %s has an unknown %s: %s" % (field['name'], val, field[val]))
        else:
            field[val] = dft

    @staticmethod
    def init(header):
        lines = re.split(r'[\r\n]+', header.strip())
        last_start = None
        for i in range(len(lines)):
            if re.search(r'^\s', lines[i]) is not None:
                lines[last_start] = lines[last_start].rstrip() + ' ' + lines[i].lstrip()
            else:
                last_start = i
        
        lines = [ l for l in lines if re.search(r'^\s', l) is None]
        self = TDF()
        self.fields = {}
        lines = [x.split(':',1) for x in lines]
        for i in lines:
            k = i[0].lower()
            v = i[1]
            if k == 'field':
                field = dict(map(lambda x : map( lambda x : x.strip(), x.split('=', 1)), v.split(';')))
                for f in field:
                    field[f] = TDF.unescape(field[f])
                field = dict([(f.lower(), field[f]) for f in field])
                TDF.find_err_default(self.encodings, field, 'encoding', self.encodings['utf8'])
                TDF.find_err_default(self.formats, field, 'format',self.formats['plain'])
                if field['type'].upper() != 'CI':
                    TDF.find_err_default(self.types, field, 'type', self.types['text'])
                self.fields[TDF.unescape(field['name'].strip())] = field

        for f in self.fields:
            if self.fields[f]['type'] == 'CI':
                self.fields[f]['is_ci'] = True
                if 'for' in self.fields[f]:
                    if self.fields[f]['for'] in self.fields:
                        ffor = self.fields[f]['for']
                        self.fields[f]['type'] = self.fields[ffor]['type']
                        if 'ci_field' not in self.fields[ffor]:
                            self.fields[ffor]['ci_field'] = {}
                        self.fields[ffor]['ci_field'][self.fields[f]['offset'].strip().lower()] = f
                    else:
                        raise Exception("CI is for field %s, but that field doesn't exist" % self.fields['for'])
                else:
                    raise Exception("Field %s is a CI, but has no For" % f)
            else:
                self.fields[f]['is_ci'] = False
                if 'ci_field'  not in self.fields[f]:
                    self.fields[f]['ci_field'] = {}
        return self
    def parse_field_names_line(self, line):
        self.field_order = [self.fields[TDF.unescape(x).strip()] for x in line.split(',')]
        if len(self.field_order) != len(self.fields):
            raise Exception('Fields count is not equal to the number of field definitions')
    def parse_line(self, line):
        line = [TDF.unescape(x) for x in line.split(',')]
        if len(line) != len(self.field_order):
            raise Exception('Line does not have same number of fields')
        ret = {}
        for i in range(len(line)):
            x = self.field_order[i]['encoding'].unmarshall(line[i]) 
            x = self.field_order[i]['format'].unmarshall(x) 
            x = self.field_order[i]['type'].unmarshall(x) 
            ret[self.field_order[i]['name']] = x

        return ret
            
        
t = TDF.init('''Author: Jim <jim@example.com>
Description: This data was collected with a Blah Blah Spectrometer. The procedure can be found at http://example.com/proc
Field: Name=Abs_ci_max; 
       Type=CI; 
       Format=Dec; 
       For=Absorption; 
       Offset=max; 
       p-value=0.05
Field: Name=Abs_ci_min; 
       Type=CI; 
       Format=Dec; 
       For=Absorption; 
       Offset=min;
       p-value=0.05
Field: Name=Absorption; 
       Type=Float; 
       Format=Dec; 
       Description=Absorption at 520cm-1$% over 4 experiments
Field: Name=Time; 
       Type=Integer; 
       Format=Dec; 
       Description=Seconds from starting
Last-Modified: 2013-10-04T08:52:00EST
''')

t.parse_field_names_line('Time, Absorption, Abs_ci_min, Abs_ci_max')

print(t.parse_line('0,0.0,0.0,0.0'))
print(t.parse_line('10,1.0,0.0,3.0'))
print(t.parse_line('15,4.0,2.0,5.0'))
print(t.parse_line('20,9.0,6.0,12.0'))
print(t.parse_line('23,14.0,11.0,18.0'))
