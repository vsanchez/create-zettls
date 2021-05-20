#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import yaml
import datetime
from enum import Enum


class stage(Enum):
    """ Defines the states of the process """

    START = 1
    HEADER = 2
    BODY = 3
    ZETTL = 4

class parser():
    """ Reads lines from the input file and detects events """

    def __init__(self, file):

        self.f = open(file,'r')
        self.re = {
            '---': re.compile(r'---'),
            '...': re.compile(r'\.\.\.'),
            'zettl': re.compile(r'#### (?P<title>.*)\n'),
        }

    def next_line(self):
        """ Reads the line and finds matches """

        line = self.f.readline()

        key = None
        title = None

        for key, rx in self.re.items():
            match = rx.search(line)
            if match:
                if key == "zettl":
                    title = match.group('title').replace(':','-')
                return line,key,title
        return line,None,None

class fileid():

    def __init__(self):

        now = datetime.datetime.now()
        self.first_id = now.strftime("%Y%m%d%H%M")
        self.num_zettl = 0

    def next_id(self):
        id = self.first_id+"{:02}".format(self.num_zettl)
        self.num_zettl += 1
        return id

class process_header():

    def __init__(self,line):

        self.buffer = "";

    def add_line(self,line):

        self.buffer += line;

    def get_header(self):
        return yaml.safe_load(self.buffer)

class zettels:
    """ Creates the new zettel """

    def __init__(self,path,header,back_link):

        # Store session long data

        self.path = path
        self.header = header
        self.back_link = back_link
        self.index_title = header["title"]

    def new_zettl(self,id,title):

        file_name = self.path+"/"+id+".md"
        self.f = open(file_name,"w")
        self.header["id"] = id
        self.header["title"] = title
        yaml.dump(self.header,self.f,encoding='utf-8',allow_unicode=True,
                  explicit_start=True,explicit_end=False, sort_keys=False,
                  indent=True)
        self.f.write("---\n\n")
        self.f.write(f"#### {title}\n")

    def add_line(self,line):
        self.f.write(line)

    def close_zettl(self):
        self.f.write("\n\n")
        self.f.write("##### Origin of Zettl\n\n")
        self.f.write(f"[[{self.back_link}]] {self.index_title}")
        self.f.close()

class index():

    def __init__(self,id,header):
        file_name = id+".md"
        self.f = open(file_name,"w")
        title = header["title"]
        header["id"] = id
        yaml.dump(header,self.f,encoding='utf-8',allow_unicode=True,
                  explicit_start=True,explicit_end=False, sort_keys=False,
                  indent=True)
        self.f.write("---\n\n")
        self.f.write(f"## {title}\n")
        self.id = id

    def add_line(self,line):
        self.f.write(line)

    def add_link(self,id,title):

        self.f.write(f"[[{id}]] {title}\n")

    def close_index(self):
        self.f.close()

# Main program

if len(sys.argv) < 2:
    print("Please provide file name of document to cut")
    exit()

input_file_name = sys.argv[1] # First argv is command name, second the file to process
output_dir = './out' #default if not specified

if len(sys.argv) > 2:
    print("Output dir given! Using " + sys.argv[2])
    output_dir = sys.argv[2]

# Make sure the output directory exists
if not os.path.exists(output_dir):
    print("Output directory does not exist! Creating ...")
    os.makedirs(output_dir)


fid = fileid()  # Initializes files ID

state = stage.START

p = parser(input_file_name)

line,key,title = p.next_line()

while line:

    if state == stage.START:
        # Will disregard anything before the YAML header
        if key == '---':
            create_header = process_header(line)
            state = state.HEADER
    elif state == stage.HEADER:
        if key == '---' or key ==  '...': # We finished the header with ... or ---
            header = create_header.get_header()
            toc = index(fid.next_id(), header) # Creates the Index or TOC file
            ztl = zettels(output_dir,header,toc.id) # Initializes the writting of Zettls
            state = stage.BODY
        else:
            create_header.add_line(line)

    elif state == stage.BODY:
        if key == 'zettl':
            zid = fid.next_id()
            ztl.new_zettl(zid, title)
            toc.add_link(zid,title)
            state = stage.ZETTL
        else:
            toc.add_line(line) # Add lines up to the first Zettl

    elif state == stage.ZETTL:
        if key == 'zettl': # Next zettl found, close current
            ztl.close_zettl()
            zid = fid.next_id()
            ztl.new_zettl(zid, title)
            toc.add_link(zid,title)
        else:
            ztl.add_line(line)
    else:
        sys.exit("Unkown state! %s".format(state))

    line,key,title = p.next_line()

ztl.close_zettl()
toc.close_index()

os.rename(input_file_name,input_file_name+".bak")















