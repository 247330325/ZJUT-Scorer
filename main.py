import socket
import requests
import json
import time
import smtplib
import copy
from email.mime.text import MIMEText
from email.header import Header


def sendmail(message, config):
    mail_host = config[4]
    mail_user = config[5]
    mail_pass = config[6]
    sender = config[5]
    receivers = config[7]
    message['From'] = Header('S-Server<score@zjut.edu.cn>', 'utf-8')
    message['To'] = Header(config[7] + '<' + config[7] + '>', 'utf-8')
    message['Subject'] = Header('出成绩了！', 'utf-8')
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


def get_HTML(msg):
    rows = []
    for score in msg:
        row = "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6}</td></tr>".format(
            score[0], score[1], score[2], score[3], score[4], score[5], score[6])
        rows.append(row)
    html = """
     <html lang="zh-cn">
    <head>
        <style>
            tr, td, th, table {
                border: 1px solid black;
            }
        </style>
    </head>
    <body>
    <table>
    """
    for row in rows:
        html = html + row
    html = html + """
</table>
</body>
</html>
    """
    print(html)
    text_html = MIMEText(html, 'html', 'utf-8')
    text_html["Content-Disposition"] = 'attachment; filename="scores.html"'
    return text_html


def error(msg):
    print(msg)


def get_score_detail(cfg):  # 返回成绩信息的res

    headers = {
        "Host": "api.jh.zjut.edu.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/79.0.3945.88 Safari/537.36 Edg/79.0.309.54 "
    }

    url = "http://api.jh.zjut.edu.cn/student/scoresDetailZf.php?ip=164&username={0}&password={1}&year={2}&term={3}". \
        format(cfg[0], cfg[1], cfg[2], cfg[3])
    content = requests.get(url, headers=headers).content.decode().encode("GBK")
    decodedJSON = json.loads(content)
    while decodedJSON["status"] != "success":
        error('查询错误')
        time.sleep(30)
        content = requests.get(url, headers=headers).content.decode().encode("GBK")
        decodedJSON = json.loads(content)
    score_summary = {}
    value = {}
    for each in decodedJSON["msg"]:
        if not (score_summary.__contains__(each['kcmc'])):
            value.clear()
        value[each['xmblmc']] = each['xmcj']
        score_summary[each['kcmc']] = copy.deepcopy(value)
    score_list = []
    for k in score_summary.items():
        score_item = [0, 0, 0, 0, 0, 0, 0]  # 课程名称，平时成绩，期末成绩，总评，学分，学分绩点，是否计入
        score_item[0] = k[0]
        for score in k[1].items():
            if "平时" in score[0]:
                score_item[1] = score[1]
            if "期末" in score[0]:
                score_item[2] = score[1]
            if "总评" in score[0]:
                score_item[3] = score[1]
        score_list.append(score_item)
    return score_list


def get_gpa_info(cfg, res):  # 为res添加GPA信息

    return res  # TODO 实现功能


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
    sendmail(get_HTML(scores), config)
    size = len(score_list)  # 获取初始数据
    while True:
        try:
            new_score_list = get_score_detail(config)
            if len(new_score_list) != size:  # 出新成绩了
                scores = get_gpa_info(config, new_score_list)  # 加上GPA信息
                sendmail(get_HTML(scores), config)
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
# '''
# for each in decodedJSON["msg"]:
#     if each['kcxzmc'] != '任选课':
#         credit = credit + eval(each['xf'])
#         GP = GP + eval(each['xf']) * eval(each['jd'])
#     msg = msg + each['kcmc'] + '\t' + each['classscore'] + '\n'
# GPA = GP / credit
# msg = msg + "当前GPA：\t" + str(GPA) + '\n'
# print("yes")
# #sendmail(msg, config)
# size = len(decodedJSON["msg"])
# '''

# except requests.exceptions.ConnectionError as e:
#     error('Network Error')
# except KeyError as e:
#     error('KeyError')
# except json.decoder.JSONDecodeError as e:
#     error('JsonDecodeError')
# # except Exception as e:
# #     error('error')
# finally:
#     time.sleep(60)
