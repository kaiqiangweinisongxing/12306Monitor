import requests
import json
import smtplib
import sys
import time
from email.mime.text import MIMEText
from email.header import Header
class tl12306:
    def __init__(self):
        self.num = 1
        # 替换为你要查询的url地址
        self.url = 'https://kyfw.12306.cn/otn/leftTicket/queryA?leftTicketDTO.train_date=2018-09-19&leftTicketDTO.from_station=GZQ&leftTicketDTO.to_station=BJP&purpose_codes=ADULT'

    def getlist(self):
        try:
            r = requests.get(self.url)
            if r.status_code == 200:
                j = json.loads(r.text)
                k = j['data']
                for r in k['result']:
                    # 以下共查询了5个车次信息，如需更多请自行添加
                    if "|D6577|" in r: # 获取D6577车次信息
                        # 查询站票、二等票是否还有票，不为无则视为有票发送邮件通知，如需监控一等票请自行添加
                        if r.split('|')[-7] != '无' or r.split('|')[-11] != '无':
                            str1 = 'D6577,有票啦~~'
                            print(str1)
                            self.send_mail(str1)
                    elif "|D6435|" in r:
                        if r.split('|')[-7] != '无' or r.split('|')[-11] != '无':
                            str2 = 'D6435,有票啦~~'
                            print(str2)
                            self.send_mail(str2)
                    elif "|D6437|" in r:
                        if r.split('|')[-7] != '无' or r.split('|')[-11] != '无':
                            str3 = 'D6437,有票啦~~'
                            print(str3)
                            self.send_mail(str3)
                    elif "|D6439|" in r:
                        if r.split('|')[-7] != '无' or r.split('|')[-11] != '无':
                            str4 = 'D6439,有票啦~~'
                            print(str4)
                            self.send_mail(str4)
                    elif "|D6441|" in r:
                        if r.split('|')[-7] != '无' or r.split('|')[-11] != '无':
                            str5 = 'D6441,有票啦~~'
                            print(str5)
                            self.send_mail(str5)
                sys.stdout.write('\r')
                sys.stdout.write('已查询%d次~' % self.num)
                sys.stdout.flush()
                self.num+=1
            else:
                msg = '获取车票信息失败~~'
                print(msg)
                self.send_mail(msg)
        except Exception as e:
            print(e)
    def send_mail(self,str):
        # 第三方 SMTP 服务
        mail_host = "smtp.qq.com"  # 设置服务器
        mail_user = "xxxxxx@qq.com"  # 用户名 发送者的邮箱
        mail_pass = "xxxxxxxxxxxxxxxxx"  # 口令 登录邮箱开启POP3/SMTP服务，输入授权码
        sender = 'xxxxxxx@qq.com' #  发送者的邮箱
        receivers = ['111111111@qq.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
        message = MIMEText(str, 'plain', 'utf-8')
        message['From'] = Header("发送者的名字", 'utf-8')
        message['To'] = Header("接收者的名字", 'utf-8')
        subject = str
        message['Subject'] = Header(subject, 'utf-8')
        try:
            smtpObj = smtplib.SMTP()
            smtpObj.connect(mail_host, 25)  # 25 为 SMTP 端口号
            smtpObj.login(mail_user, mail_pass)
            smtpObj.sendmail(sender, receivers, message.as_string())
            print("邮件发送成功")
        except smtplib.SMTPException:
            print("Error: 无法发送邮件")
    def input_second(self):
        second = input("请输入查询间隔（单位/秒）: ")
        try:
            return int(second)
        except Exception:
            print('您输入的不是数字，请重新输入~~')
            return self.input_second()


if __name__ == '__main__':
    c = tl12306()
    print('程序正在运行~~关闭窗口即退出监控~')
    second = c.input_second()
    while True:
        c.getlist()
        time.sleep(second)