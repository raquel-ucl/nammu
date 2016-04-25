import requests
import logging
import re
import StringIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import httplib as http_client
from HTTPRequest import HTTPRequest

class SOAPClient(object):
    """
    Sends and retrieves information to and from the ORACC SOAP server.
    """
    def __init__(self, url, method):
        self.url = url
        self.method = method
        logging.basicConfig()
        self.logger, self.request_log = self.setup_logger()

    def setup_logger(self):
        """
        Creates logger to debug HTTP messages sent and responses received.
        Output should be sent to Nammu's console.
        """
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        request_log = logging.getLogger("requests.packages.urllib3")
        request_log.setLevel(logging.DEBUG)
        request_log.propagate = True
        return logger, request_log

    def create_request(self, **kwargs):
        request = HTTPRequest(self.url, self.method, **kwargs)
        self.request = request

    def send(self):
        """
        Elaborate HTTP POST request and send it to ORACC's server.
        """
        url = "http://oracc.museum.upenn.edu:8085"
        headers = dict(self.request.get_headers())
        body = self.request.get_body()
        self.response = requests.post(url, data=body, headers=headers)
        # try:
        #    response = requests.post(url, data=body, headers=headers, timeout=10)
        # except ReadTimeout:
        #          print "Timed out!"

    def get_response_text(self):
        return self.response.text

    def get_response_id(self):
        xml_root = ET.fromstring(self.response.text)
        # This should be done with xpath. See XPath and namespaces sections
        # here: https://docs.python.org/2/library/xml.etree.elementtree.html
        return xml_root[0][0][0][0].text

    def wait_for_response(self, id):
        """
        Check for a response to the request and obtain response zip file.
        """
        while True:
            url = "http://oracc.museum.upenn.edu/p/" + id
            try:
                ready_response = requests.get(url, timeout=5)
            except Timeout:
                return False
            if ready_response.text == "done\n":
                return True
            if ready_response.text == "err_stat\n":
                return False

    def get_response(self):
        return self.response.content

    def parse_response(self):
        """
        Extract information sent in server response.
        """
        pass

    def _check_response_ready(self, id):
        """
        Send a HTTP GET request to ORACC's server and retrieve status.
        """
        pass

    def create_request_zip(self):
        """
        Pack attachment in a zip file.
        """
        pass

    def get_server_logs(self):
        """
        Manipulate response to substract the content of oracc.log that is in the
        returned binary-coded zip file.
        """
        self.response.content
        binary_body = re.split('--==.*==', self.response.content)[2].split('\r\n')[5]

        f = StringIO.StringIO()
        f.write(bytearray(binary_body))

        # if zipfile.is_zipfile(f):
        memory_zip = ZipFile(f)
        zip_content = {name: memory_zip.read(name) for name in memory_zip.namelist()}
        oracc_log = zip_content['oracc.log']
        request_log = zip_content['request.log']
        # See if server returns a lemmatised file
        autolem = None
        for key, value in zip_content.iteritems():
            if key.endswith("autolem.atf"):
                autolem = zip_content[key]

        print "@"*30
        print oracc_log
        print "@"*30
        print request_log
        print "@"*30
        if autolem:
            print autolem
            print "@"*30

        return oracc_log, request_log, autolem

    def get_autolem(self):
        """

        """
