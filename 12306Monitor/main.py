#!/usr/bin/python
# -*- coding: utf-8 -*-：
import requests
import json
import smtplib
import time
from random import randint
from email.mime.text import MIMEText
from email.header import Header
from wxpy import *
import re
import datetime
import xlwt
import pymysql

headers = {
    "Host": "kyfw.12306.cn",
    "If-Modified-Since": "0",
    "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.92 Safari/537.36"
}


class Monitor(object):
    def __init__(self):
        self.station_name_url = 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js'  # 起始站点信息表，根据起止站点获取站点编码code
        self.url = 'https://kyfw.12306.cn/otn/leftTicket/queryA?leftTicketDTO.train_date={0}&leftTicketDTO.from_station={1}&leftTicketDTO.to_station={2}&purpose_codes=ADULT'
        self.isFail = False

    '''获取输入信息'''
    def Input(self):
        # mysql数据库
        self.db_host = 'localhost'
        self.user_name = 'passenger'
        self.user_password = '000000'
        self.db_name = 'monitor'

        # return input('请输入查询日期【yyyy-MM-dd】：')
        self.fromStation = '北京'
        self.toStation = '武汉'
        self.departureDate = '2018-09-21'

        # e-mail
        self.mail_host = "smtp.qq.com"          # 设置服务器
        self.port = 25
        self.mail_user = "123456789@qq.com"     # 发送者邮箱
        self.mail_pass = 'yahzmxfsldfqcbdb'     # 口令 登录邮箱开启POP3/SMTP服务，输入授权码（非登录密码）
        self.sender = "123456789@qq.com"
        self.receivers = ['123456@qq.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱,可群发
        self.sender_nickname = '小助手'
        self.receiver_nickname = '龙傲天'
        return self.fromStation, self.toStation, self.departureDate



    '''根据起止站站点名去获取对应的站点编码'''
    def GetStationDic(self):
        stationDic = {}
        r = requests.get(url=self.station_name_url).text
        content = re.match('^var station_names =\'(.*?)\';$', r).group(1)
        list = content.split('@')[1:]       # 元素格式：bjb|北京北|VAP|beijingbei|bjb|0
        print('站点数：' + str(list.__len__()))
        for i in list:
            if stationDic.__contains__(i.split('|')[1]) == False:
               stationDic[i.split('|')[1]] = i.split('|')[2]    # 北京北:VAP
        return stationDic

    '''构造request请求url'''
    def GetUrl(self,stationDic):
        if stationDic.__contains__(self.fromStation):
            fromCode = stationDic[self.fromStation]
        if stationDic.__contains__(self.toStation):
            toCode = stationDic[self.toStation]
        if fromCode!='' and toCode!= '':
            self.url = self.url.format(self.departureDate, fromCode, toCode)
            return self.url
        else:
            return '无效站点'

    '''获取有座的车次信息'''
    def GetTicket(self):
        try:
            r = requests.get(self.url, headers=headers)
            tickets = []    # 所有的车次信息
            result = []     # 有票的车次信息
            print(r.text)
            if r.status_code != 200:
                print('获取车票失败!')
                self.isFail = True
                return []
            else:
                j = json.loads(r.text)
                print(j)
                if len(j['data']['result']) == 0:
                    print('未找到符合条件的列车')
                else:
                    for t in j['data']['result']:
                        dic = {}
                        temp = t.split('|')
                        dic['车次'] = temp[3]
                        dic['出发时间'] = temp[8]
                        dic['到达时间'] = temp[9]
                        dic['一等座'] = temp[-6]
                        dic['二等座'] = temp[-7]
                        dic['站票'] = temp[-11]
                        tickets.append(dic)
                    for item in tickets:
                        if (item['一等座'] != '无' and item['一等座'] != '') or\
                                (item['一等座'] != '无' and item['一等座'] != '') or\
                                (item['一等座'] != '无' and item['一等座'] != ''):
                            result.append(item)
            return result
        except Exception as e:
            print('获取车票失败!')
            self.isFail = True
            return []

    def SendMail(self, result = ''):
        # https://www.cnblogs.com/imyalost/p/7383901.html
        # 第三方SMTP服务
        now = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        if result != '':
            msg = self.departureDate + '  ' + self.fromStation + '-' + self.toStation + '   班次：' + str(len(result)) +\
                  '     当前时间：' + now + '\n\n'
            for item in result:
                msg += '车次：' + item['车次'] + '   出发时间：' + item['出发时间'] + \
                       '    到达时间：' + item['到达时间'] + '   一等座：' + item['一等座'] +\
                       '    二等座：' + item['二等座'] + '     站票：' + item['站票'] + '\n'
        else:
            msg = '查询失败，终止查询！' + '     当前时间：' + now
        print(msg)
        message = MIMEText(msg, 'plain', 'utf-8')  # 邮件文本内容
        message['Subject'] = Header(self.departureDate + '  ' + self.fromStation + '-' + self.toStation + ' （12306）', 'utf-8')  # 邮件标题
        message['From'] = Header(self.sender_nickname, 'utf-8')
        message['to'] = Header(self.receiver_nickname, 'utf-8')
        try:
            smtpobj = smtplib.SMTP()
            smtpobj.connect(self.mail_host, self.port)
            smtpobj.login(self.mail_user, self.mail_pass)
            smtpobj.sendmail(self.sender, self.receivers, message.as_string())
            print('邮件发送成功!')
            self.SendWechat(msg)
        except smtplib.SMTPException:
            print('Error: 无法发送邮件{}'.format(smtplib.SMTPException))

    # 发送消息到微信
    # https://blog.csdn.net/sm9sun/article/details/79725637
    # https://wxpy.readthedocs.io/zh/latest/index.html
    def SendWechat(self, msg):
        print('登录微信')
        bot = Bot(cache_path=True)  # 保留缓存自动登录
        bot.file_helper.send(msg)
        print('发送微信成功！')
        # my_friend = bot.friends().search(u'So')[0]           # 好友（微信名称或备注，不是微信帐号）
        # my_friend = bot.friends().search(u'刘')               # 含有刘字的人
        # my_group =bot.groups().search(u'1班')[0]        # 群组
        # file_helper = bot.file_helper.send('[奸笑][奸笑]')    # 传输助手
        # file_helper = bot.file_helper.send(msg.text)
        # file_helper = bot.file_helper.send_image('QR.png')      # 传输文件
        # my_friend.send('[奸笑][奸笑]')                        # 传输表情
        # s = bot.friends().stats_text()                          # 按性别、top省份、top城市统计好友

    def SaveToExcel(self,result):
        font = xlwt.Font()
        font.bold = True
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        alignment.vert = xlwt.Alignment.VERT_CENTER
        sty1 = xlwt.XFStyle()
        sty1.font = font
        sty1.alignment = alignment
        sty2 = xlwt.XFStyle()
        sty2.alignment = alignment
        row = 1
        column = 0
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('12306')
        worksheet.write(0, 0, '车次', sty1)
        worksheet.write(0, 1, label='出发时间', style=sty1)
        worksheet.write(0, 2, label='到达时间', style=sty1)
        worksheet.write(0, 3, label='一等座', style=sty1)
        worksheet.write(0, 4, label='二等座', style=sty1)
        worksheet.write(0, 5, label='站票', style=sty1)
        for dict in result:
            worksheet.write(row, column, dict["车次"], sty2)
            worksheet.write(row, column + 1, dict["出发时间"], sty2)
            worksheet.write(row, column + 2, dict["到达时间"], sty2)
            worksheet.write(row, column + 3, dict["一等座"], sty2)
            worksheet.write(row, column + 4, dict["二等座"], sty2)
            worksheet.write(row, column + 5, dict["站票"], sty2)
            row += 1
        workbook.save('{0} {1}-{2}.xls'.format(self.departureDate,self.fromStation,self.toStation))
        print('成功保存到Excel！')

    def SaveStationToMysql(self, stationDic):
        db = pymysql.connect(self.db_host , self.user_name, self.user_password, self.db_name, charset='utf8')     # 以用户的身份去连接，需要开启 apache和mysql服务
        cursor = db.cursor()
        sql = "TRUNCATE TABLE STATION"
        cursor.execute(sql)
        try:
            for k, v in stationDic.items():
                sql = "INSERT INTO STATION(STATION_ID,STATION_NAME) VALUES ( \'{0}\',\'{1}\')".format(v, k)
                cursor.execute(sql)
            db.commit()
            print('成功将站名信息写入数据库！')
        except Exception as err:
            print('写入数据库出错：' + err)
            db.rollback()
        finally:
            cursor.close()
            db.close()

    def SaveTicketToMysql(self,result):
        db = pymysql.connect(self.db_host, self.user_name, self.user_password, self.db_name,
                             charset='utf8')
        cursor = db.cursor()
        now = datetime.datetime.now()
        try:
            for dict in result:
                sql = """INSERT INTO MONITOR_TABLE(TRAIN_NUMBER,FROM_STATION,TO_STATION,DEPARTURE_TIME,arrival_time,first_class_seat,
                         second_class_seat,no_seat,oper_time) 
                         VALUES ( '{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}','{8}')""".format(dict["车次"],
                         self.fromStation,self.toStation, dict["出发时间"],dict["到达时间"],dict["一等座"],dict["二等座"], dict["站票"], now)
                cursor.execute(sql)
            db.commit()
            print('成功将车次信息写入数据库！')
        except Exception as err:
            print('写入数据库出错：' + err)
            db.rollback()
        finally:
            cursor.close()
            db.close()

if __name__ == '__main__':
    monitor = Monitor()
    inputMsg = monitor.Input()                  # 输入起止站、出发时间
    print(inputMsg)
    stationDic = monitor.GetStationDic()       # 起止站的信息
    monitor.SaveStationToMysql(stationDic)
    url = monitor.GetUrl(stationDic)
    print(url)
    while True:
        result = monitor.GetTicket()
        if monitor.isFail == False:
            if len(result) > 0:
                monitor.SaveToExcel(result)
                monitor.SaveTicketToMysql(result)
                monitor.SendMail(result)
                break
            else:
                print('没票')
                time.sleep(randint(5, 10))
        else:
            monitor.SendMail()
            break