import socket
import requests
import json
import time
import smtplib
import copy
from email.mime.text import MIMEText
from email.header import Header


def sendmail(subject, message, config):
    mail_host = config[4]
    mail_user = config[5]
    mail_pass = config[6]
    sender = config[5]
    receivers = config[7]
    message['From'] = Header('S-Server<score@zjut.edu.cn>', 'utf-8')
    message['To'] = Header(config[7] + '<' + config[7] + '>', 'utf-8')
    message['Subject'] = Header(subject, 'utf-8')
    try:
        SMTPObj = smtplib.SMTP_SSL(mail_host, 465)
        SMTPObj.ehlo()
        SMTPObj.login(mail_user, mail_pass)
        SMTPObj.sendmail(sender, receivers, message.as_string())
        print("邮件发送成功")
    except smtplib.SMTPAuthenticationError:
        print("邮箱账号或密码错误")
    except socket.gaierror:
        print("网络连接错误，请检查SMTP服务器配置")


def get_gpa(msg):
    gp = 0
    credit = 0
    for item in msg:
        if item[6] != "任选课":
            gp = gp + item[4] * item[5]
            credit = credit + item[4]
    if credit != 0:
        return round(gp / credit, 4)
    else:
        return 0


def beautify_msg(msg):
    for item in msg:
        item[1] = "{0}({1}%)".format(item[1], 100 - item[7])
        item[2] = "{0}({1}%)".format(item[2], item[7])
    return msg


def get_HTML(msg):
    rows = []
    for score in beautify_msg(msg):
        row = "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</tr>".format(score[0], score[1], score[2], score[3])
        rows.append(row)
    gpa = get_gpa(msg)
    html = """<html lang="zh-cn">
<head>
    <title>成绩明细</title>
    <style>
        tr, td, th, table {
            border: 1px solid black;
        }
    </style>
</head>
<body>
<table style='text-align: center'>
    <tr>
        <td>课程名称</td>
        <td>平时成绩</td>
        <td>期末成绩</td>
        <td>总评</td>
    </tr>
    """
    for row in rows:
        html = html + row
    html = html + """<tr>
    <td>GPA</td>
    <td colspan='3'>{0}</td>
    </table>
    </body>
    </html>
    """.format(gpa)
    print(html)
    text_html = MIMEText(html, 'html', 'utf-8')
    text_html["Content-Disposition"] = 'attachment; filename="scores.html"'
    return text_html


def error(msg):
    print(msg)


def get_json(url):
    headers = {
        "Host": "api.jh.zjut.edu.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/79.0.3945.88 Safari/537.36 Edg/79.0.309.54 "
    }

    content = requests.get(url, headers=headers).content.decode().encode("GBK")
    result = json.loads(content)
    while result["status"] != "success":
        error('查询错误')
        time.sleep(30)
        content = requests.get(url, headers=headers).content.decode().encode("GBK")
        result = json.loads(content)
    return result


def get_score_detail(cfg):  # 返回成绩信息的res
    url = "http://api.jh.zjut.edu.cn/student/scoresDetailZf.php?ip=164&username={0}&password={1}&year={2}&term={3}". \
        format(cfg[0], cfg[1], cfg[2], cfg[3])
    score_detail = get_json(url)
    score_summary = {}
    value = {}
    for each in score_detail["msg"]:
        if not (score_summary.__contains__(each['kcmc'])):
            value.clear()
        value[each['xmblmc']] = each['xmcj']
        score_summary[each['kcmc']] = copy.deepcopy(value)
    score_list = []
    for k in score_summary.items():
        score_item = [0, 0, 0, 0, 0, 0, 0, 0]  # 课程名称，平时成绩，期末成绩，总评，学分，学分绩点，是否计入,期末考占比
        score_item[0] = k[0]
        for score in k[1].items():
            if "平时" in score[0]:
                score_item[1] = score[1]
            if "期末" in score[0]:
                score_item[2] = score[1]
                score_item[7] = eval(score[0].split("(")[1].split("%")[0])
            if "总评" in score[0]:
                score_item[3] = score[1]
        score_list.append(score_item)
    return score_list


def get_gpa_info(cfg, res):  # 为res添加GPA信息
    url = "http://api.jh.zjut.edu.cn/student/scoresZf.php?ip=164&username={0}&password={1}&year={2}&term={3}". \
        format(cfg[0], cfg[1], cfg[2], cfg[3])
    score_detail = get_json(url)
    for score in score_detail["msg"]:
        for item in res:
            if item[0] == score["kcmc"]:
                item[4] = eval(score["xf"])
                item[5] = eval(score["jd"])
                item[6] = score["kcxzmc"]
    return res


def check_password(cfg):  # 判断密码是否正确，正确返回True
    return True  # TODO 实现功能


def get_config():
    config_file = open('config.ini', mode='r', encoding='utf-8')
    return config_file.read().split('\n')


if __name__ == '__main__':
    config = get_config()
    if not check_password(config):
        error("密码错误")
        exit(0)
    score_list = get_score_detail(config)
    scores = get_gpa_info(config, score_list)  # 加上GPA信息
    sendmail("服务启动成功", get_HTML(scores), config)
    size = len(score_list)  # 获取初始数据
    while True:
        try:
            new_score_list = get_score_detail(config)
            if len(new_score_list) != size:  # 出新成绩了
                scores = get_gpa_info(config, new_score_list)  # 加上GPA信息
                html = get_HTML(scores)
                sendmail("出成绩了！", html, config)
        except requests.exceptions.ConnectionError as e:
            error('Network Error')
        except KeyError as e:
            error('KeyError')
        except json.decoder.JSONDecodeError as e:
            error('JsonDecodeError')
        except Exception as e:
            error('error')
        finally:
            time.sleep(60)
