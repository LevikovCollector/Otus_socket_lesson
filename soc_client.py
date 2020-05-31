import socket
import argparse
import re
from html.parser import HTMLParser
import collections

def process_respons(data):
    if data.find('<!doctype html>') != -1:
        header, html = data.split('<!doctype html>')
    elif data.find('<html>') != -1:
        header, html = data.split('<html>')
    else:
        header = data
        html = 'None'
    status_code = re.search('\s(\d+)\s', header.split('\n')[0]).group(0)

    return {'header':header,
            'html':html,
            'status_code':status_code
            }


class MyHTMLParser(HTMLParser):
    def __init__(self, *, convert_charrefs=True):
        super(HTMLParser).__init__()
        self.convert_charrefs = convert_charrefs
        self.reset()
        self.raw_tag_data = []
        self.current_tag = ''
        self.all_tags = []
        self.its_link = False
        self.other_attribute = ''

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self.all_tags.append(tag)
        if tag == 'a':
            self.its_link = True
            self.get_attribute('href', attrs)

        elif tag == 'img':
            self.get_attribute('src', attrs)
            self.raw_tag_data.append((self.current_tag, self.other_attribute))

    def handle_data(self, data):
        if self.its_link:
            self.raw_tag_data.append((self.current_tag, data, self.other_attribute))
            self.its_link = False
        else:
            self.raw_tag_data.append((self.current_tag, data))

    def get_attribute(self, atribute, attrs):
        for attr in attrs:
            if attr[0] == atribute:
                self.other_attribute = attr[1]
                break

    def tag_data_to_str(self):
        tag_data_for_str = []
        for info in self.raw_tag_data:
            try:
                tag, val = info
                tag_data_for_str.append('({}, {})'.format(tag, val))
            except ValueError:
                tag, val, other_val = info
                tag_data_for_str.append('({}, {}, {})'.format(tag, val,other_val))
        res_str = ', '.join(tag_data_for_str)
        return res_str


parser = argparse.ArgumentParser(description='Socket requests', argument_default=None)
parser.add_argument('-u', dest='url',  action='store', help='Url for request', default='www.google.com')
parser.add_argument('-header', dest='header',  action='store', help='Header for request', default='HTTP/1.1')
parser.add_argument('-m', dest='method',  action='store', default='GET')
args = parser.parse_args()

server = args.url
port = 80
server_ip = socket.gethostbyname(server)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

request = "{0} / {2}\nHost:{1}\n\n".format(args.method, server, args.header)
data = []
sock.connect((server,port))
sock.send(request.encode())
result = sock.recv(4096)
data.append(result.decode('utf-8'))
while result.decode('utf-8').find("</html>") == -1 :
    if result.decode('utf-8').find("X-Content-Type-Options: nosniff") == -1:
        result = sock.recv(4096)
        data.append(result.decode('utf-8'))
    else:break

all_data = ''.join(data)
proc_res = process_respons(all_data)

print('Status code: '+ proc_res['status_code'])
print('\n')
print('#'*50)
print('Header:\n' + proc_res['header'])

if proc_res['html'] != 'None':
    print('\n')
    print('#' * 50)
    print('HTML:\n' + proc_res['html'])
    print('\n')
    print('#' * 50)
    parser = MyHTMLParser()
    parser.feed(proc_res['html'])
    all_result = {'all_tags_html': parser.all_tags,
                  'tags_with_info':parser.tag_data_to_str(),
                  'most_popular_tag':collections.Counter(parser.all_tags).most_common(1)[0]
                  }

    print(all_result)
