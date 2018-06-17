#!/usr/bin/env python
from domtree import *
import re
import sys

keys = ["ch", "name", "sec", "file"]
ch_lst = []
default_style = [("tr.inf_down",
                  [("border-top", "1px solid #000")]),
                 ("tr.inf_down > td",
                  [("text-align", "center"),
                   ("padding", "0 10px")]),
                 ("tr.inf_up > td",
                  [("padding", "0px 10px"),
                   ("text-align", "center"),
                   ("vertical-align", "bottom")]),
                 ("tr.inf_up > td.inf_name",
                  [("vertical-align", "middle"),
                   ("font-size", "50%"),
                   ("padding", "0px")]),
                 ("table.inf",
                  [("border-collapse", "collapse"),
                   ("padding", "10px")]),
                 ("tr.horizon > td",
                  [("padding", "0 10px")]),
                 ("ul.no_num",
                  [("list-style", "none")]),
                 (".box",
                  [("padding", "10px"),
                   ("margin-bottom", "10px"),
                   ("display", "inline-block"),
                   ("border", "1px solid #333")]),
                 (".ch_title",
                  [("font-weight", "bolder"),
                   ("font-size", "130%")]),
                 (".ch",
                  [("margin", "10px 0")]),
                 (".ch_content",
                  []),
                 (".sec_header",
                  [("padding-bottom", "10px")]),
                 (".sec_title",
                  [("font-weight", "normal"),
                   ("font-size", "120%")]),
                 (".sec",
                  [("margin", "20px 0")]),
                 (".sec_content",
                  [("margin-left", "20px")])]
styles = None

doctype_tag = "<!DOCTYPE html>"
coding = "UTF-8"
meta_tag = "<meta charset=\"" + coding + "\">"
inline_scripts = ["src/script.js"]

def init_styles():
    global styles
    global default_style
    styles = Styles()
    for secretor , props in default_style:
        b = StyleBlock(secretor)
        for p , v in props:
            b.appendProp(p, v)
        styles.appendBlock(b)
    # print styles.to_css()

def parse_file(fname):
    f = open(fname, "r")
    lines = f.readlines()
    f.close()
    i = 0
    length = len(lines)

    result = {}
    # read header
    while True:
        if i == length:
            raise Exception("header error")
        elif lines[i][0] == '#':
            break
        elif lines[i].find(':') != -1:
            prop, val = lines[i].split(':', 1)
            result[prop.strip()] = val.strip()
        i += 1

    # read chapters
    chapters = []
    while True:
        if length <= i:
            break
        line = lines[i]
        m = re.match(r':ch +(\d+)$', line)
        if m:
            ch_n = int (m.group(1))
            ptr, chapter = parse_chapter(ch_n, i + 1, lines)
            i = ptr
            chapters.append(chapter)
            continue
        i += 1
    result['chapters'] = chapters

    return result

def parse_content_until_end(ptr, lines):
    i = ptr
    content = []
    while True:
        if len(lines) <= i:
            raise Exception("not found :e command")

        line = lines[i]
        if line.rstrip() == ":e":
            i += 1
            break
        else:
            content.append(line)
        i += 1
    return (i, content)

# section with no content is invalid
# section can handle only :s command
def parse_section(ch_n, sec_n, ptr, lines):
    title = lines[ptr]
    i = ptr

    sec_content = []
    while True:
        if len(lines) <= i:
            break
        
        line = lines[i]
        if line.rstrip() == ":s":
            ptr , content = parse_content_until_end(i + 1, lines)
            i = ptr
            sec_content = content
            break
        elif line[0] == ':':
            raise Exception("Unexpected command")
        i += 1
    return i , Section(ch_n, sec_n, title, sec_content)

# chapter can be empty
# chapter reads lines until next :ch command or end of lines
def parse_chapter(ch_n, ptr, lines):
    title = lines[ptr]
    i = ptr + 1

    # read chapter_content if it exists
    chapter_content = []
    while True:
        if len(lines) <= i:
            return i , Chapter(ch_n, title, [], [])

        line = lines[i]
        if line.startswith(":sec"):
            break
        elif line.rstrip() == (":s"):
            ptr , content = parse_content_until_end(i + 1, lines)
            i = ptr
            chapter_content = content
            break
        elif line.startswith(":ch"):
            return i , Chapter(ch_n, title, [], [])
        i += 1

    # read sections
    sections = []
    while True:
        if len(lines) <= i:
            break

        line = lines[i]
        m = re.match(r':sec +(\d+)$', line)
        if m:
            sec_n = int (m.group(1))
            ptr , section = parse_section(ch_n, sec_n, i + 1, lines)
            i = ptr
            sections.append(section)
        elif line.startswith(":ch"):
            break
        i += 1

    return i , Chapter(ch_n, title, chapter_content, sections)

def create_chapters_html(chapters):
    root = Element("ul.no_num")
    for ch in chapters:
        li = Element("li")
        li.appendChild(ch.to_html())
        root.appendChild(li)
    return root

def create_index(chapters):
    ch_ul = Element("ul")
    for ch in chapters:
        ch_li = Element("li")
        ch_link = LinkNode("#ch" + str(ch.n), "ch." + str(ch.n))
        ch_li.appendChild(ch_link)
        ch_li.appendChild(TextNode(" " + ch.title))
        sc_ul = Element("ul.no_num")
        for sec in ch.sections:
            li = Element("li")
            sc_id = "#sec" + str(ch.n) + "_" + str(sec.n)
            sc_link = LinkNode(sc_id, str(ch.n) + "-" + str(sec.n))
            li.appendChild(sc_link)
            li.appendChild(TextNode(" " + sec.title))
            sc_ul.appendChild(li)
        ch_li.appendChild(sc_ul)
        ch_ul.appendChild(ch_li)
    return ch_ul

def inject_scripts(f):
    f.write('\n')
    for fname in inline_scripts:
      script = open(fname, 'r')
      for line in script:
        f.write(line)
    f.write('\n')
    return

def generate_html(input_fname):
    parsed_result = parse_file(input_fname)
    chapters = parsed_result.get('chapters', [])
    title = parsed_result.get('title', '')
    _, default_oname = input_fname.rsplit('/', 1)
    output_fname = 'out/' +\
        parsed_result.get('ofname', default_oname) + '.html'
    body_elem = Element("body")
    body_elem.appendChild(create_index(chapters))
    body_elem.appendChild(create_chapters_html(chapters))
    f = open(output_fname, 'w')
    f.write(doctype_tag)
    f.write("<html>\n")
    f.write("<head>\n")
    f.write("<style>\n")
    f.write(styles.to_css())
    f.write("</style>\n")
    f.write("<script type=\"text/javascript\">");
    inject_scripts(f);
    f.write("</script>");
    f.write(meta_tag)
    f.write("\n")
    f.write("<title>" + title + "</title>")
    f.write("</head>")
    f.write(body_elem.to_html())
    f.write("</html>\n")
    f.close()
    return

def on_load():
    args = sys.argv
    if len(args) != 2:
        print "syntax: python conv_main.py <file-path>"
        return
    init_styles()
    input_fname = args[1];
    generate_html(input_fname)

on_load()
