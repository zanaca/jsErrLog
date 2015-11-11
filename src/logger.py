from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError
import os
import string
from google.appengine.api import xmpp
import httpagentparser
import urlparse

class LogErr(db.Model):
        serverName = db.StringProperty()
        serverPath = db.StringProperty()
        fileLoc = db.StringProperty()
        lineNo = db.StringProperty()
        colNo = db.StringProperty()
        errMsg = db.StringProperty()
        infoMsg = db.StringProperty()
        IP = db.StringProperty()
        UA = db.StringProperty()
        OSName = db.StringProperty()
        OSVer = db.StringProperty()
        BrowserName = db.StringProperty()
        BrowserVer = db.StringProperty()
        guid = db.StringProperty()
        ts = db.DateTimeProperty( auto_now_add=True )

class LogUser(db.Model):
        userName = db.StringProperty()
        serverName = db.StringProperty()
        active = bool(False)

class MainHandler(webapp.RequestHandler):
    def get(self):
        data = {}
        data['QfileLoc'] = self.request.get("fl")
        data['QlineNo'] = self.request.get("ln")
        data['QcolNo'] = self.request.get("cn")
        data['QerrMsg'] = self.request.get("err")
        data['QinfoMsg'] = self.request.get("info")
        data['o'] = urlparse.urlsplit(self.request.get("sn"))
        data['Qguid'] = self.request.get("ui")
        data['Qi'] = self.request.get("i")
        self.__process(data)

    def post(self):
        jsonData = json.loads(self.request.body)
        data = {}
        data['QfileLoc'] = jsonData["fl"]
        data['QlineNo'] = jsonData["ln"]
        data['QcolNo'] = jsonData["cn"]
        data['QerrMsg'] = jsonData["err"]
        data['QinfoMsg'] = jsonData["info"]
        data['o'] = urlparse.urlsplit(jsonData["sn"])
        data['Qguid'] = jsonData["ui"]
        data['Qi'] = jsonData["i"]
        self.__process(data)


    def __process(self, data):
        QfileLoc = data['QfileLoc']
        QlineNo = data['QlineNo']
        QcolNo = data['QcolNo']
        QerrMsg = data['QerrMsg']
        QinfoMsg = data['QinfoMsg']
        o = data['o']
        Qguid = data['Qguid']
        Qi = data['Qi']

        QUA = os.environ['HTTP_USER_AGENT']
        try:
            QOSName = httpagentparser.detect(QUA)['os']['name']
        except:
            QOSName = "Unknown"
        try:
            QOSVer = httpagentparser.detect(QUA)['os']['version']
        except:
            QOSVer = "Unknown"
        try:
            QBrowserName = httpagentparser.detect(QUA)['browser']['name']
        except:
            QBrowserName = "Unknown"
        try:
            QBrowserVer = httpagentparser.detect(QUA)['browser']['version']
        except:
            QBrowserVer = "Unknown"
        QIP = os.environ['REMOTE_ADDR']
        QserverName = o.scheme + "://" + o.netloc
        QserverPath = o.path
        if o.query != "":
            QserverPath += "?" + o.query
        if o.fragment != "":
            QserverPath += "#" + o.fragment
        storeLog = LogErr(serverName=QserverName, serverPath=QserverPath, fileLoc=QfileLoc, lineNo=QlineNo, colNo=QcolNo, errMsg=QerrMsg, infoMsg=QinfoMsg, IP=QIP, UA=QUA, OSName=QOSName, OSVer=QOSVer, BrowserName=QBrowserName, BrowserVer=QBrowserVer, guid=Qguid)
        try:
            storeLog.put()
            errMsg = ""
        except CapabilityDisabledError, err:
            errMsg = "// AppEngine is in read-only mode at the moment: " + err + "\n"
        except Error, err:
            # fail gracefully if insert fails
            errMsg = "// Insert failed: " + err + "\n"
            pass

        self.response.out.write("jsErrLog.removeScript(" + Qi + ") // jsErrRpt\n")
        if errMsg !="":
            self.response.out.write(errMsg)

        q = db.GqlQuery("SELECT * FROM LogUser " +
            "WHERE serverName = :1 AND userActive = True",
            string.lower(QserverName))
        results = q.get()
        if results != None:
            # Send alert via XMPP/GTalk
            chat_message_sent = False
            user_address = results.userName
            if xmpp.get_presence(user_address):
                msg = ("An error was just reported for " + QserverName + " at line " + QlineNo + " in " + QfileLoc + ".\nVisit http://jsErrLog.appspot.com/report.html?sn=" + QserverName + " for more details.")
                status_code = xmpp.send_message(user_address, msg)
                chat_message_sent = (status_code == xmpp.NO_ERROR)


def main():
    application = webapp.WSGIApplication([('/logger.js', MainHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
