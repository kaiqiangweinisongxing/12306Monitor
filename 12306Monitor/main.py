import requests
import json
import smtplib
import time
from random import randint  # 随机函数

from email.mime.text import MIMEText
from email.header import Header
from wxpy import *

headers = {
    "Host": "kyfw.12306.cn",
    "If-Modified-Since": "0",
    "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.92 Safari/537.36"
}


class tl12306(object):
    def __init__(self):
        self.num = 1
        # 按需停止查询
        self.finded_tiket = False  # 标识是否有票，有票则停止查询，避免对12306无效访问，造成带宽拥堵而且由ip封杀的风险【不给12306添堵了，反正咱要的信息已经有了】
        self.station_name_url = 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js'  # 起始站点信息表，根据起止站点获取站点编码code
        # 灵活修改为模拟输入【日期，起止站点由用户输入】
        self.url = 'https://kyfw.12306.cn/otn/leftTicket/queryA?leftTicketDTO.train_date={}&leftTicketDTO.from_station={}&leftTicketDTO.to_station={}&purpose_codes=ADULT'

    def get_station_code(self, from_station, to_statian):
        '''根据起止站站点名去获取对应的站点编码'''
        result = {}
        result['from_code'] = ''
        result['to_code'] = ''
        r = requests.get(url=self.station_name_url, verify=False).text
        for i in r.split('@'):
            # i 的格式为  bjb|北京北|VAP|beijingbei|bjb|0
            if len(i.split('|')) >= 3:  # 是否大于3个成员，排除返回起始无效字段ar station_names ='
                stationText = i.split('|')[1]
                stationCode = i.split('|')[2]
                if stationText == from_station:
                    result['from_code'] = stationCode
                elif stationText == to_statian:
                    result['to_code'] = stationCode
                if result['from_code'] != '' and result['to_code'] != '':  # 找到起止code 后直接退出,避免无效等待
                    return result

    def getlist(self, data, fromStaion, toStation):
        '''根据传入的日期，起点站，终点站去查询余票信息'''
        try:
            r = requests.get(self.url.format(data, fromStaion, toStation), headers=headers)
            if r.status_code == 200:
                j = json.loads(r.text)
                k = j['data']
                print(str(k['map']))  # 站点信息（含同城异站站点） 如：{'KMM': '昆明', 'KOM': '昆明南', 'NNZ': '南宁'}
                last_result = []  # 所有车次所有余票信息列表
                for r in k['result']:
                    strarray = r.split('|')
                    train_num = str(strarray[3])  # 车次
                    seat1 = str(strarray[-6])  # 一等座
                    seat2 = str(strarray[-7])  # 二等座
                    seat3 = str(strarray[-11])  # 站票
                    result = ''
                    if seat1 != '无' and seat1 != '':
                        result += ' 一等座有票!{}；'.format(
                            '' if seat1 == '有' else '余票：{}'.format(seat1))  # pyrhon的三目运算，如果返回实际剩余票数，则显示余票数
                    if seat2 != '无' and seat2 != '':
                        result += ' 二等座有票!{}；'.format('' if seat2 == '有' else '余票：{}'.format(seat2))
                    if seat3 != '无' and seat3 != '':
                        result += ' 站票有票!{};'.format('' if seat3 == '有' else '余票：{}'.format(seat3))
                    if result != '':
                        self.finded_tiket = True  # 查到票就标记已有票，不再刷新页面，如果不是自己想要的车次，可以注释此行代码，或者修改判断逻辑
                        result = '{},有票啦~~;{}\n'.format(train_num, result)
                        last_result.append(result)
                        print(result)
                self.send_mail(str(k['map']) + '\n' + '  '.join(last_result))
                print('已查询%d次' % self.num)
                self.num += 1
                return last_result
            else:
                print('获取车票失败！')
                self.send_mail('获取车票失败')
        except Exception as e:
            print(e)

    def send_mail(self, str):
        # 第三方SMTP服务
        mail_host = "smtp.qq.com"  # 设置服务器
        mail_user = "xxxxxx@qq.com"  # 发送者邮箱
        mail_pass = 'gsvwqbXXXXXtwjclwjbddcdfddjb'  # 口令 登录邮箱开启POP3/SMTP服务，输入授权码
        sender = "XXXX@qq.com"
        receivers = ['XXXX@qq.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
        message = MIMEText(str, 'plain', 'utf-8')  # 邮件文本内容
        message['From'] = Header('Lemon', 'utf-8')
        message['to'] = Header('Lemon_too', 'utf-8')
        message['Subject'] = Header('余票查询结果', 'utf-8')  # 邮件标题
        try:
            smtpobj = smtplib.SMTP()
            smtpobj.connect(mail_host, 25)  # 25为端口号
            smtpobj.login(mail_user, mail_pass)
            smtpobj.sendmail(sender, receivers, message.as_string())
            print('邮件发送成功')
        except smtplib.SMTPException:
            print('Error: 无法发送邮件{}'.format(smtplib.SMTPException))

    # 发送消息到微信
    def send_msg_to_wachat(self, data):
        bot = Bot()
        my_friend = bot.friends().search(u'Lemon')[0]  # 你朋友/自己的微信名称，不是备注，也不是微信帐号。。
        my_friend.send(data)

    def input_date(self):
        return input('请输入查询日期【yyyy-MM-dd】：')

    def input_from(self):
        return input('请输入起点站站名：')

    def input_to(self):
        return input('请输入到站站名：')


if __name__ == '__main__':
    c = tl12306()
    print('程序开始运行')
    while c.finded_tiket == False:  # 如果找到票了，停止查询
        # 输入日期，制定格式为 2018-10-01
        date = c.input_date()
        # 输入起点站 站名
        fromStaion = c.input_from()
        # 输入终点站 站名
        toStation = c.input_to()
        # 由起止站站名去匹配对应编码，用于生成实际访问url
        stationCode_Info = c.get_station_code(fromStaion, toStation)
        print(stationCode_Info)
        last_result = c.getlist(date, stationCode_Info['from_code'], stationCode_Info['to_code'])
        c.send_msg_to_wachat(last_result)
        # 随机等待，避免访问过快而被禁ip等受限访问结果
        time.sleep(randint(5, 10))
    print('程序运行结束')