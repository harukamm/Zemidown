import re

env = []
########################################
# Class for temporary DOM element
########################################
class Element:
    def __init__(self, n):
        self.children = []
        self.tag = None
        self.ids = []
        self.classes = []
        self.attributes = []
        for m in re.finditer(r'([#.])(\w+)', n):
            if self.tag is None:
                self.tag = n[:m.start()]
            if m.group(1) == '#':
                self.ids.append(m.group(2))
            elif m.group(1) == '.':
                self.classes.append(m.group(2))
        if self.tag is None:
            self.tag = n

    def appendChild(self, elem):
        if elem.to_html is None:
            raise Exception("appendChild")
        self.children.append(elem)
        return self

    def setAttribute(self, p, v):
        self.attributes.append((p, v))

    def br(self):
        self.appendChild(Br())
        return self

    def addClass(self, c):
        self.classes.append(c)
        return self
    def to_html(self):
        s = "<" + self.tag
        if len(self.ids) > 0 :
            s += " id=\"" + " ".join(self.ids) + "\""
        if len(self.classes) > 0:
            s += " class=\"" + " ".join(self.classes) + "\""
        if len(self.attributes) > 0:
            for p , v in self.attributes:
                s += " " + p + "=\"" + v + "\""
        s += ">"
        for child in self.children:
            s += child.to_html()
        s += "</" + self.tag + ">"
        return s

class TextNode():
    def __init__(self, text):
        if len(text) != 0 and text[0] != '\\':
            text = text.replace("&", "&amp;")
            text = text.replace("<", "&lt;")
            text = text.replace(">", "&gt;")
            text = text.replace("\"", "&quot;")
        else:
            text = text[1:]
        self.text = text

    def br(self):
        self.text += "<br>"
        return self

    def to_html(self):
        return self.text

class LinkNode():
    def __init__(self, link, text):
        self.link = link
        self.text = text

    def to_html(self):
        s = "<a href=\"" + self.link + "\">"
        s += self.text
        s += "</a>"
        return s

class Br():
    def to_html(self):
        return "<br>"

class Hr():
    def to_html(self):
        return "<hr>"

########################################
# Method for making DOM tree
########################################
def until_ends_command(name, ptr, lines):
    i = ptr
    lst = []
    while True:
        if len(lines) <= i:
            raise Exception("not found ends-command")
        line = lines[i]
        if line.startswith(":e-" + name):
            i += 1
            break
        lst.append(line)
        i += 1
    return i , lst

def skip(s, i, c):
    assert 0 <= i
    count = 0
    while i < len(s) and s[i] == c:
        i += 1
        count += 1
    return i , c * count

def until(s, i, sep, raiseErr=False, disableUnescaped=False):
    start = i
    assert 0 <= i
    skipped = ""
    while i < len(s):
        if s[i] == sep:
            break
        elif s[i] == '\\':
            if not disableUnescaped:
                if i + 1 < len(s) and not s[i + 1].isalnum():
                    i += 1
        skipped += s[i]
        i += 1
    if raiseErr:
        if len(s) <= i or s[i] != sep:
            raise Exception("`" + s[start:] + "` must have `" + sep +
              "` (in `" + s + "`)")
    return i , skipped

def split_and_unescape(s, sep):
    if s == "":
        return []
    i = 0
    tmp = ""
    tkn = []
    # Ignore a single `sep` in head and tail of `s`
    if 1 <= len(s) and s[0] == sep:
        s = s[1:]
    if 2 <= len(s) and s[-1] == sep and s[-2] != '\\':
        s = s[:-1]
    while True:
        if len(s) <= i:
            if tmp != "":
                tkn.append(tmp)
            break
        if s[i] == '\\':
            if i + 1 < len(s) and not s[i + 1].isalnum():
                tmp += s[i]
                i += 2
        elif s[i] == sep:
            tkn.append(tmp)
            tmp = ""
            i += 1
        else:
            tmp += s[i]
            i += 1
    return tkn

def define_and_return_domtree(info):
    # syntax : "(" + id + "," + name + "," + title + ")"
    id_ , name , title = "" , "" , ""
    m = re.match(r'\s*\(([^\,]+)\,\s*([^\,]+)\,\s*([^\)]+)\)$', info)
    if m:
        id_ = m.group(1)
        name = m.group(2)
        title = m.group(3)
    else:
        raise Exception("define stc doesn't follow the rule")
    env[id_] = name
    span = Element("span.define")
    b = Element("b")
    b.appendChild(TextNode(name))
    span.appendChild(b)
    span.appendChild(TextNode(" "))
    span.appendChild(TextNode(title))
    return span

# inf := :inf( inf , [inf] )
#      | string

def make_inf_domtree(info):
    # inf := :inf( inf', [inf'] )
    #
    # inf' := :inf( inf', [inf'] )
    #       | string
    info = info.strip()
    if ":inf" != info[:4]:
        raise Exception("inf-command must starts with `:inf`")
    _, tree = make_inf_domtree_impl(info, 0)
    return tree

def make_inf_domtree_impl(info, i):
    i , _ = skip(info, i, ' ')
    if info[i:].startswith(":inf"):
        i += 4
    else:
        ptr1 , text1 = until(info, i, ',')
        ptr2 , text2 = until(info, i, ']')
        if ptr1 < len(info) and info[ptr1] == ',':
            return ptr1 , TextNode(text1)
        elif ptr2 < len(info) and info[ptr2] == ']':
            return ptr2 , TextNode(text2)
        else:
            raise Exception("Inner inf-command ends illegally")

    # Read the inference name if it is written
    i , name = until(info, i, '(', raiseErr=True)
    if len(name) != 0 and name[0] == '-':
        name = name[1:]
    i += 1 # Skip '('

    # Find matched close parenthesis
    k = i
    nested = 0
    while k < len(info):
        if info[k] == '\\' and k + 1 < len(info):
            if info[k + 1] == '(' or info[k + 1] == ')':
                k += 1
        elif info[k] == '(':
            nested += 1
        elif info[k] == ')':
            if nested == 0:
                break
            nested -= 1
        k += 1
    assert k != len(info)

    # Read the conclusion
    rest = info[i:k]
    i , concl_elm = make_inf_domtree_impl(rest, 0)
    i += 1 # Skip ','

    # Read the premises
    rest = rest[i:]
    i , _ = until(rest, 0, '[', raiseErr=True)
    premise = rest[i:].rstrip()
    assert premise[0] == '['
    assert premise[-1] == ']'
    j = 1
    premise_elms = []
    while j < len(premise) - 1:
        j_nxt , p_elm = make_inf_domtree_impl(premise, j)
        assert j < j_nxt
        premise_elms.append(p_elm)
        j = j_nxt + 1 # Consume ',' or ']'

    inf = Element("table.inf")
    # make domtree for promises
    up = Element("tr.inf_up")
    if len(premise_elms) != 0:
        for p in premise_elms:
            td = Element("td")
            td.appendChild(p)
            up.appendChild(td)
    else:
        # add dummy td-element if promises is empty
        # in order to set name  vertically center
        td = Element("td")
        td.appendChild(TextNode("\&nbsp;"))
        up.appendChild(td)

    # add name
    name_elem = Element("td.inf_name")
    name_elem.appendChild(TextNode(name))
    name_elem.setAttribute("rowspan", "2")
    up.appendChild(name_elem)

    inf.appendChild(up)

    # make domtree for conslusion
    down = Element("tr.inf_down")
    dtd = Element("td")
    dtd.setAttribute("colspan", str(len(premise_elms)))
    dtd.appendChild(concl_elm)
    down.appendChild(dtd)
    inf.appendChild(down)

    return k + 1, inf

def make_item_domtree(lines, with_number):
    tag = ""
    if with_number:
        tag = "ol"
    else:
        tag = "ul"
    item = Element(tag)
    for line in lines:
        if len(line) != 0 and line[0] == '-':
            text = TextNode(line[1:])
            li = Element("li")
            li.appendChild(text)
            item.appendChild(li)
    return item

def make_horizon_domtree(elems):
    table = Element("table")
    tr = Element("tr.horizon")
    for x in elems:
        td = Element("td")
        td.appendChild(x)
        tr.appendChild(td)
    table.appendChild(tr)
    return table

# resolve reference for env
def scanning_one_line(s):
    i = 0
    tmp = ""
    lst = []

    while i < len(s):
        c = s[i]
        if c == ":":
            if s[i:].startswith(":ref") and i + 4 < len(s):
                lst.append(TextNode(tmp))
                tmp = ""

                ss = s[i+4:]
                i += 4

                # syntax : :ref(id)rest
                m = m = re.match(r'\(([^\)]+)\).*$', ss)
                id_ = m.group(1)
                i += len(id_) + 2
                if not env.has_key(id_):
                    raise Exception("not defined " + id_)
                name = env[id_]
                link = LinkNode(name, "#" + id_)
                lst.append(link)
            else:
                tmp += c
                i += 1
        else:
            tmp += c
            i += 1
    if tmp != "":
        lst.append(TextNode(tmp))

    if len(lst) == 1:
        return lst[0]
    e = Element("span")
    for x in lst:
        e.appendChild(x)
    return e

def make_table_domtree(lines):
    table = Element("table")
    for line in lines:
        tkn2 = split_and_unescape(line, '|')

        # create a single tr node
        tr = Element("tr")
        for t in tkn2:
            td = Element("td")
            td.appendChild(TextNode(t))
            tr.appendChild(td)
        table.appendChild(tr)
    return table

def make_domtree_at_single_line(ptr, lines):
    if len(lines) <= ptr:
        raise Exception("out of lst")
    line = lines[ptr]
    if line.startswith(":"):
        if line.startswith(":inf"):
            return ptr + 1 , make_inf_domtree(line)
        elif line.startswith(":define"):
            return ptr + 1 , define_and_return_domtree(inf[7:])
        elif line.startswith(":---"):
            return ptr + 1 , Hr()
        elif line.startswith(":s-"):
            m = re.match(r':s-([a-z]+)*', line)
            if not m:
                raise Exception("undefined command: " + name)
            else:
                name = m.group(1)
                x , lst = until_ends_command(name, ptr + 1, lines)
                i = ptr
                if name == "table":
                    return x , make_table_domtree(lst)
                elif name == "itemn":
                    return x , make_item_domtree(lst, True)
                elif name == "item":
                    return x , make_item_domtree(lst, False)
                elif name == "box":
                    e = Element("span.box")
                    a = 0
                    while a < len(lst):
                        a2 , b = make_domtree_at_single_line(a, lst)
                        a = a2
                        e.appendChild(b)
                    return x , e
                elif name == "horizon":
                    elems = []
                    a = 0
                    while a < len(lst):
                        a2 , b = make_domtree_at_single_line(a, lst)
                        a = a2
                        elems.append(b)
                    return x , make_horizon_domtree(elems)
                else:
                    raise Exception("not defined command name " + name)
    else:
        #e = scanning_one_line(line)
        if len(line) == 0 or (len(line) != 0 and line[-1] != '\\'):
            return ptr + 1 , TextNode(line).br()
        else:
            return ptr + 1 , TextNode(line)
    raise Exception("? " + line)

def make_domtree(lines):
    root = Element("div")
    i = 0
    while True:
        if len(lines) <= i:
            break
        ptr , elem = make_domtree_at_single_line(i, lines)
        root.appendChild(elem)
        i = ptr
    return root

########################################
# Class for File
########################################
class Chapter:
    def __init__(self, n, title, content, sections):
        self.n = n
        self.title = title.rstrip()
        cnt = []
        for line in content:
            cnt.append(line.rstrip())
        self.content = cnt
        self.sections = sorted(sections, key=lambda x: x.n)

    def to_html(self):
        idname = "ch" + str(self.n)
        elem = Element("div.ch#" + idname)
        link = LinkNode("#" + idname, "&nbsp;#&nbsp;")
        elem.appendChild(link)
        title = TextNode(" chapter " + str(self.n) + ". " + self.title)
        elem.appendChild(Element("span.ch_title").appendChild(title))
        if self.content != []:
            elem.appendChild(make_domtree(self.content).addClass("ch_content"))

        ul = Element("ul.no_num")
        for sec in self.sections:
            li = Element("li")
            li.appendChild(sec.to_html())
            ul.appendChild(li)
        elem.appendChild(ul)
        return elem

    def damp(self):
        print "chapter-start " + str(self.n)
        print self.title
        for line in self.content:
            print line
        for sec in self.sections:
            sec.damp()
        print "chapter-start " + str(self.n)

class Section:
    def __init__(self, ch_n, n, title, content):
        self.ch_n = ch_n
        self.n = n
        self.title = title.rstrip()
        cnt = []
        for line in content:
            cnt.append(line.rstrip())
        self.content = cnt

    def to_html(self):
        idname = "sec" + str(self.ch_n) + "_" + str(self.n)
        elem = Element("div.sec#" + idname)
        link = LinkNode("#" + idname, "&nbsp;#&nbsp;")
        elem.appendChild(link)
        title = TextNode(" section " + str(self.ch_n) + \
                         "-" + str(self.n) + ". " + self.title)
        elem.appendChild(Element("span.sec_title").appendChild(title))
        elem.appendChild(make_domtree(self.content).addClass("sec_content"))
        return elem

    def damp(self):
        print "section-start " + str(self.n)
        print self.title
        for line in self.content:
            print line
        print "section-end " + str(self.n)

########################################
# Class for Style sheet
########################################
class Styles():
    def __init__(self):
        self.styles = []

    def appendBlock(self, block):
        self.styles.append(block)

    def to_css(self):
        s = ""
        for style in self.styles:
            s += style.to_css()
            s += "\n"
        return s
    
class StyleBlock():
    def __init__(self, secretor):
        self.secretor = secretor
        self.props = []

    def appendProp(self, name, value):
        self.props.append((name, value))
        return self.props

    def to_css(self):
        s = self.secretor
        s += " {\n"
        for n , v in self.props:
            s += n + ": " + v + ";\n"
        s += "}"
        return s
        
        
