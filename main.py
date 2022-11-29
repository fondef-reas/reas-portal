#!/usr/bin/env python3
"""
HTTP server for antenna rfid UHF EPC Gen2, catch antenna json read tags request
and send request to API to storage this data
Usage::
    install service or configure parameters in /etc/reas-portal.ini then run
    ./main.py
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import requests
import configparser
from datetime import datetime
from dateutil import tz


globals()['server4antennaPort'] = ''
globals()['apiHost'] = ''
globals()['apiPort'] = ''
globals()['portalId'] = ''
tagList = set()
globals()['deadline'] = time.time() + 5


def loadConfig():
    config = configparser.ConfigParser()

    # Production
    config.read('/etc/reas-portal.ini')

    globals()['server4antennaPort'] = config['ServerForAntenna']['port']
    globals()['apiHost'] = config['API']['host']
    globals()['apiPort'] = config['API']['port']
    globals()['portalId'] = config['PortalConfig']['id']
    globals()['PortalhasScale'] = config['PortalConfig']['hasScale']

    # Test local
    # config.read('C:\\Users\\Marcelo\\PycharmProjects\\ReasNodeV1\\reas-portal.ini')

    # globals()['server4antennaPort'] = '8181'
    # globals()['apiHost'] = 'localhost'
    # globals()['apiPort'] = '8080'

    print('Config sections:\n\t', str(config.sections()), str(config), '\n\t\t', 'server4antennaPort:',
          globals()['server4antennaPort'], '\n\t\t', 'apiHost:', globals()['apiHost'], '\n\t\t',
          'apiPort:', globals()['apiPort'], '\n\t\t', 'PortalID: ', int(globals()['portalId']), '\n\t\t',
          'PortalHasScale: ', int(globals()['PortalhasScale']))


def insertPortalActivity():
    while True:
        if time.time() >= globals()['deadline']:
            # print('5 seconds elapsed...')
            url = 'http://' + globals()['apiHost'] + ':' + globals()['apiPort'] + \
                  '/api/v1/portalActivity/'
            payload = []

            logging.info("tagList: " + str(list(globals()['tagList'])))

            # Weight Stub
            if bool(globals()['PortalhasScale']):
                pass

            if list(globals()['tagList']):
                hexTagIdList = list(globals()['tagList'])

                for i in range(len(hexTagIdList)):
                    element = {
                        "crossingMomment": datetime.now(tz=tz.tzlocal()).isoformat(),
                        "weight": 0,
                        "portalId": int(globals()['portalId']),
                        "uhfTagHexId": str(hexTagIdList[i])
                    }
                    payload.append(element)
                try:
                    print(payload)
                    req = requests.post(url, json=payload)
                    print('content:\n\t', req.content)
                except Exception as e:
                    print(e)
                globals()['tagList'] = set()
            globals()['deadline'] = time.time() + 5


class S(BaseHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    # def do_GET(self):
    #     logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
    #     self._set_response()
    #     self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        # logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
        #             str(self.path), str(self.headers), post_data.decode('utf-8'))
        if self.path == '/Tags':
            bodyJson = json.loads(post_data.decode('utf-8'))

            # logging.info('Tags quantity: ' + bodyJson['tagRecNums'])

            for item in bodyJson['tagRecords']:
                globals()['tagList'].add(item['epcID'])

            #logging.info(globals()['tagList'])

        self._set_response()
        # self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))


def run(server_class=HTTPServer, handler_class=S):
    logging.basicConfig(level=logging.INFO)
    loadConfig()
    d = threading.Thread(target=insertPortalActivity, name='Daemon')
    d.setDaemon(True)
    d.start()
    server_address = ('', int(globals()['server4antennaPort']))
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')


if __name__ == '__main__':
    run()
