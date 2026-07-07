import requests
from bs4 import BeautifulSoup
import time
import random as rd
import pymysql
import json

def pars(sf,string,sto):
    res = ''
    if sf == '' or sto == '' or string == '':
        return res
    pos1 = string.find(sf)
    if pos1 < 0:
        return res
    else:
        pos1 = pos1 + len(sf)
    string = string[pos1:]

    pos2 = string.find(sto)
    if pos2 > 0:
        res = string[:pos2]

    return res

class Arsenkin:

    def __init__(self):
        self.rec = requests.Session()
        self.login = "podpart@yandex.ru"
        self.password = "XCp-5aP-mLR-t2t"
        self.r = self.rec.get("https://arsenkin.ru/tools/login")
        self.token = self.givemetoken()
        self.auth()

    def givemetoken(self):
        soup = BeautifulSoup(self.r.text,'lxml')
        tokblock = soup.find('input', {'name': '_token'})
        #<input type="hidden" name="_token" value="hJHAcPSSb8XMXVQxNxfHNygekPrFS3fG9nIorrla">
        return(tokblock.get('value'))

    def auth(self):
        self.r = self.rec.post('https://arsenkin.ru/tools/login/', data = {
            '_token':self.token,
            'email':self.login,
            'password':self.password
        }) 
        self.r = self.rec.get('https://arsenkin.ru/tools/cabinet')
    
    def getlimits(self):
        self.r = self.rec.post('https://arsenkin.ru/tools/getlimits/', data = {
            'url':''
            })
        lim = self.r.text
        lim = 100-int(lim)
        return lim

    def getnumofchar(self,key):
        #winkey = key.encode('cp1251')
        self.r = self.rec.post('https://arsenkin.ru/tools/check-seotext/',data = {
            'mode':'single',
            'keys':key,
            'urls':'',
            'stoplist':'',
            'city':'213',
            'citygoogle':'1011969',
            'ss':'1',
            'url':'', 
            'filefirstline':'yes',
            'file':'undefined'               
        })
        t = self.r.text
        taskid = ''
        while taskid == '':
            taskid = self.gettaskid() 
        status = 0
        maxnum = 450/5
        num = 0        
        while status < 100:
            if num > maxnum:
                raise Exception('Зависло походу') 
            time.sleep(5)
            self.r = self.rec.get(
                'https://arsenkin.ru/tools/get-progress/',
                params = {
                'task_id':taskid
            })             
            status = int(self.r.text)
            num+=1
        time.sleep(5)    
        self.r = self.rec.post('https://arsenkin.ru/tools/get_history/',data = {
            'hid':taskid,
            'hash':'',
            'tools_id':'28'    
        })
        numofchar = self.gettopten()
        return(numofchar)


    def gettopten(self):
        soup = BeautifulSoup(self.r.text,'lxml')
        tbody = soup.find("tbody")
        tr = tbody.find_all("tr")
        needtr = tr[0]
        tds = needtr.find_all("td")
        needtd = tds[3]
        numcount = pars('(',needtd.text,' /')
        numcount = int(numcount)
        return(numcount)

    def gettaskid(self):
        task_id = pars("task_id: '",self.r.text,"'")
        return(task_id)  

    def killtask(self, onlybag):
        self.r = self.rec.post('https://arsenkin.ru/tools/queue/',data = {
            'action':'list'    
        })
        t = self.r.text
        soup = BeautifulSoup(t,'lxml')
        trs = soup.find_all("tr")
        for tr in trs:
            tds = tr.find_all("td")
            if len(tds) == 1:
                return
            needtd = tds[4]
            kill = False
            if onlybag:
                if needtd.text.find('зависла')>0:
                    kill = True
            else:
                kill = True
            if kill:            
                needtd = tds[1]
                taskid = needtd.text
                self.r = self.rec.post('https://arsenkin.ru/tools/queue/',data = {
                    'action':'delete',
                    'id':taskid    
                })                

    def checkkilltask(self):
        self.r = self.rec.post('https://arsenkin.ru/tools/queue/',data = {
            'action':'list'    
        })
        t = self.r.text
        soup = BeautifulSoup(t,'lxml')
        trs = soup.find_all("tr")
        for tr in trs:
            tds = tr.find_all("td")
            needtd = tds[3]
            if needtd.text.find('зависла')>0:
                needtd = tds[5]
                taskid = needtd.attrs['data-id']
                self.r = self.rec.post('https://arsenkin.ru/tools/queue/',data = {
                    'action':'restart',
                    'id':taskid    
                }) 
                data = json.loads(self.r.text)
                if data['status'] == 'ok':
                    return taskid

class Mysql:  
        
    def connectionopen(self):
        self.connection = pymysql.connect(host='94.228.120.41',
            user='user1',
            password='ervfe443',
            db='mydb',
            charset='utf8mb4')
        self.cur = self.connection.cursor()
    
    def connectionclose(self):
        self.cur.close()
        self.connection.close()                         

    def getrandomkey(self):
        self.connectionopen()
        sql = 'SELECT `code`,`keyword` FROM `keynumcount` WHERE `num` = 0'
        self.cur.execute(sql)
        keys = []
        rows = self.cur.fetchall()          
        key = rd.choice(rows)
        self.connectionclose()
        return key

    def updatemysql(self, keycode, count):
        self.connectionopen()
        sql = "UPDATE `keynumcount` SET `num`= %s WHERE `code`= %s" % (count, keycode)
        self.cur.execute(sql)        
        self.connection.commit()
        self.connectionclose()

def main():
    arsenkin = Arsenkin()
    arsenkin.killtask(False)
    limit = arsenkin.getlimits()
    if limit > 0:
        sql = Mysql()
        strkey = sql.getrandomkey()
        numofchar = arsenkin.getnumofchar(strkey[1])
        sql.updatemysql(strkey[0],numofchar) 
main()
print('Ok')