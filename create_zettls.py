#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import yaml
import datetime

def read_header(buffer):
    global back_link

    header = yaml.safe_load(buffer)
    back_link = "[["+str(header["id"])+"]]"+" "+header["title"]

    index_file.write(back_link)
    index_file.write('\n\n')

    return header


def _parse_line(line):
    """
    Do a regex search against all defined regexes and
    return the key and match result of the first matching regex

    """

    for key, rx in rx_dict.items():
        match = rx.search(line)
        if match:
            return key, match
    # if there are no matches
    return None, None



def new_id():
    global num_zettl
    id = first_id+"{:02}".format(num_zettl)
    num_zettl += 1
    return id




def create_zettl(title):
    global header

    id = new_id()
    file_name = output_dir+"/"+id+".md"
    file = open(file_name,"w")
    header["id"] = id
    header["title"] = title
    yaml.dump(header,file,encoding='utf-8',allow_unicode=True,
              explicit_start=True,explicit_end=True,
              indent=True)

    index_file.write("[["+str(header["id"])+"]]"+" "+header["title"]+"\n")

    return file


def parse(state,file):

    global header

    line = file.readline()

    while line:
        key,match = _parse_line(line)

        if key:
            print(key, match)
            if key == "zettl":
                title = match.group('title')
                if state == "start":
                    state = "zettl"
                    zettl_file = create_zettl(title)
                    zettl_file.write('\n\n')
                    zettl_file.write(back_link)
                    zettl_file.write('\n\n')
                    zettl_file.write(line)

                elif state == "zettl":
                    #found the start of the next zettel, we continue with teh Zettl state till the end
                    zettl_file.close()
                    zettl_file = create_zettl(title)
                    zettl_file.write('\n\n')
                    zettl_file.write(back_link)
                    zettl_file.write('\n\n')
                    zettl_file.write(line)
            elif key == "start_yaml":
                if state =="start":
                    state="header"
                    header_buffer = line
            elif key == "end_yaml":
                if state == "header":
                    # unpack
                    header_buffer += line
                    header = read_header(header_buffer)
                    print(header)
                    state = "start"
                else:
                    print("ups no acabó el header")
        else:
            if state == "header":
                header_buffer += line
            elif state == "zettl":
                zettl_file.write(line)

        line = file.readline()
    zettl_file.close()
    index_file.close()



if len(sys.argv) < 2:
    print("Please provide file name of document to cut")
    exit()

input_file_name = sys.argv[1] # First argv is command name, second the file to process
output_dir = './out'

# Statistics and global variables
files_created = 0
files_processed = 0
index_file_name = "index.md"
header = {}
back_link = ""

# No seconds because it could be too fast

now = datetime.datetime.now()
first_id = now.strftime("%Y%m%d%H%M")
num_zettl = 0


if len(sys.argv) > 2:
    print("Output dir given! Using " + sys.argv[2])
    output_dir = sys.argv[2]

# Make sure the output directory exists
if not os.path.exists(output_dir):
    print("Output directory does not exist! Creating ...")
    os.makedirs(output_dir)

file = open(input_file_name)

#    set up regular expressions
# use https://regexper.com to visualise these if required

rx_dict = {
    'start_yaml': re.compile(r'---'),
    'end_yaml': re.compile(r'\.\.\.'),
    'zettl': re.compile(r'#### (?P<title>.*)\n'),
}

state = 'start'

index_file = open(index_file_name,"w")

parse(state,file)



