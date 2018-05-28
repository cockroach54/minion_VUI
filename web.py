# all the imports
import sqlite3, json, jinja2, os, html
import datetime
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, send_from_directory
from flask_cors import CORS, cross_origin # http://flask-cors.readthedocs.io/en/latest/
# from flaskext.mysql import MySQL

from speech_recog import *

from myTextRank import *
import asyncio
import jpype
p = textRank()

app = Flask(__name__, static_url_path='',
            static_folder='static',)
            # template_folder='templates')
CORS(app, support_credentials=True)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'img/favicon.png')

@app.route("/")
def home():
    return render_template('index.html')  

@app.route("/api/speech2text", methods=['POST'])
def stt():
    if type(request.data) is bytes: body = json.loads(request.data.decode())
    else: body = json.loads(request.data)
    # print(body) # base64 code 보여줌
    audio = body['audio']

    webm_file = base2webm(audio, 'tmp.flac') #이건 파일 직접 인코딩시
    
    # webm_file = bytes(audio, encoding='utf-8') #이건 스트링->byte직접 인코딩
    flac_file = webm2flac(webm_file)
    texts = speech2text(flac_file, 16000)
    '''
    여기에 이제 딥러닝 코드
    NER
    KB search
    memory network
    seq2seq
    exception control
    '''

    '''
    여기가 text2speech
    결국 리턴은 오디오 파일이나 base64 
    '''
    return json.dumps(texts)

# ---------------------------------for textRank

# 뉴스주소 받기
@app.route("/news", methods=['POST'])
def news():
  # 다른 스레드 사용시엔 반드시 필요
    jpype.attachThreadToJVM()
    
    print(request.data)
    if type(request.data) is bytes: body = json.loads(request.data.decode())
    else: body = json.loads(request.data)
    # print(body)
    news_url = body['news_url']
    news_doc = body['news_doc']

    # 네이버 뉴스 제외하고 url대신 본문으로 보낸경우
    if news_url is '':
      print(news_doc)
      p.article_parsed = news_doc.split('. ')
      p.title = 'have no title'
    else:
      # # 비동기로 불러오기
      # # loop = asyncio.get_event_loop()
      # # loop.run_until_complete(p.getNews(news_url))
      # # 주피터에서 사용
      # article = p.getNews(news_url)
      article = requests.get(news_url)
      p.parse(article)
    # textrank
    p.setGraph()
    p.getSummary()
    news_summ = p.getSummary(num_summ=3)
    keywords = p.getKeyword(5)

    return json.dumps({
        'url': news_url,
        'news_title': p.title,
        'news_origin': p.article_parsed,
        'news_summ': news_summ,
        'keywords': keywords
      })
    # print(body['news_url'], p.title, '\n', p.article_parsed)
    # return json.dumps(body)

# question answring
@app.route("/query", methods=['POST'])
def query():
    jpype.attachThreadToJVM()
    
    if type(request.data) is bytes: body = json.loads(request.data.decode())
    else: body = json.loads(request.data)
    print(body)
    query = body['query']
    # 뉴스요약 먼저 하고 질문해야함
    try:
      res = {
        'answers': p.getAnswer(query)
      }
    except:
      res = {
        'answers': ['get news first!!']
      }

    return json.dumps(res)

    
# ---------------------------------- 아래는 그냥 참고용임
@app.route("/contents")
@app.route("/contents/<style>")
@app.route("/contents/<style>/<game>")
@app.route("/contents/<style>/<game>/<gameKind>")
def contents_style(style=None, game=None, gameKind=None):
    if game==None or gameKind==None: return 'please, Enter the correct URL like /contents/[news style]/[game]/[gameKind]'
    return send_from_directory(os.path.join(app.root_path, 'front/dist2'), 'news.html')      

'''
@app.route("/survey", methods=['POST'])
@cross_origin(supports_credentials=True)
def survey():
    # body = json.loads(request.data.decode('utf-8'))
    body = request.form
    print(body)
    
    # body dict는 immutable이라 변경불가
    q15 = body['q15']
    q16 = body['q16']
    q17 = body['q17']
    q18 = body['q18']
    s1 = html.unescape(body['s1'])

    # --- date check
    dt = datetime.datetime.now()

    # --- sqlite3
    conn_s = sqlite3.connect('tmp/survey.db')
    cursor_s = conn_s.cursor()
    sql = "insert into result(player, game, gameKind, newsKind, seq, q1,q2,q3,q4,q5,q6,q7,q8,q9,q10,q11,q12,q13,q14,q15,q16,q17,q18,s1,year,month,day,hour,minute) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    cursor_s.execute(sql, [player, game, gameKind, newsKind, seq, q1,q2,q3,q4,q5,q6,q7,q8,q9,q10,q11,q12,q13,q14,q15,q16,q17,q18,s1,
        dt.year, dt.month, dt.day, dt.hour, dt.minute])
    conn_s.commit()
    conn_s.close()
    # --- mongodb
    saveMongo(player, game, gameKind, newsKind, seq, q1,q2,q3,q4,q5,q6,q7,q8,q9,q10,q11,q12,q13,q14,q15,q16,q17,q18,s1,
        dt.year, dt.month, dt.day, dt.hour, dt.minute)
    saveMySQL(player, game, gameKind, newsKind, seq, q1,q2,q3,q4,q5,q6,q7,q8,q9,q10,q11,q12,q13,q14,q15,q16,q17,q18,s1,
        dt.year, dt.month, dt.day, dt.hour, dt.minute)

    print(json.dumps(body))
    return json.dumps(body)
    # return send_from_directory(os.path.join(app.root_path), 'thank.html')        

# --------------- api 
@app.route("/api/path")
def getPath():
    player = request.args.get('player')
    game = request.args.get('game')
    gameKind = request.args.get('gameKind')

    # --- mysql
    cursor = mysql.connect().cursor()
    query = "select * from path where player='%s' and sport='%s' and event_name='%s'"%(player, game, gameKind)
    # select component에서 목록 가져오기
    if player=='allList': query = "select player, nation, rank from path where sport='%s' and event_name='%s'"%(game, gameKind)
    cursor.execute(query) 
    # 문자 변수는 반드시 ' ' 로 감싸야함
    data = cursor.fetchall() # 튜플로 들어옴

    print(query, data)
    if data is None:
        return "query is wrong...."
    else:
        return json.dumps(data)

# 뉴스 자료용 스태틱파일 제공 
@app.route("/newsdata/<path:file_path>")
def sendNews(file_path):
    file_path = file_path.split('/')
    file_name = file_path[-1]
    pre_path = '/'.join(file_path[:-1])
    pre_path = '../../DropBox/olympic/'+pre_path # 실제 리눅스 서버에선 이부분 빠져야함
    # pre_path = 'C:\\Users\\LSW\\Dropbox\\olympic\\'+pre_path # 실제 리눅스 서버에선 이부분 빠져야함
    # pre_path = 'newsdata/'+pre_path # 실제 리눅스 서버에선 이부분 빠져야함
    print(pre_path, file_name)
    return send_from_directory(os.path.join(app.root_path, pre_path), file_name)      

# 패스에서 로컬 파일리스트 받아오기
@app.route("/api/filelist")
def getFileList():
    game = request.args.get('game')
    gameKind = request.args.get('gameKind')
    player = request.args.get('player')
    isCard = request.args.get('isCard')
    path = '../../DropBox/olympic/'+game+'/'+gameKind+'/'+player
    # path = 'C:\\Users\\LSW\\Dropbox\\olympic\\'+game+'\\'+gameKind+'\\'+player
    # path = 'newsdata/'+game+'/'+gameKind+'/'+player

    filelist = []
    extension = '.png' # 파일 확장자
    if isCard == 'movie':  extension='.mp4'
    for file in os.listdir(path):
        if file.endswith(extension):
            filelist.append(file)
    print(path, filelist)
    return json.dumps(filelist)


# ---------------여기부터는 테스트용
@app.route("/auth")
def auth():

    # print(type(data), data, data_s)
    if data is None:
        return "Name is wrong"

@app.route("/insert")
def insert():
    name = request.args.get('name')
    age = request.args.get('age')
    # age = int(age)    

    return 'Data well saved:'+name+', '+age

# ---------------가상주소 리다이렉션용
# @app.route("/contents/<style>")
# def contents_style(style):
#     print('contents loaded:', style)
#     return send_from_directory(os.path.join(app.root_path, 'front/dist2'), 'news.html')    


# SPA prge refresh문제 해결용
@app.errorhandler(404)
def page_not_found(e):
    # return send_from_directory(os.path.join(app.root_path, 'front/dist'), 'index.html')    
    return "죄송합니다. 요청하신 페이지를 찾을수 없습니다.(Error: 404)"
'''
if __name__ == '__main__':
    context = ('ssl/cert.pem', 'ssl/key.pem') # for https ssl
    app.run(debug=True, host='0.0.0.0', port=8000, ssl_context=context) # 이건 내부, 외부 한번에
    # app.run(debug=True, host='10.0.1.21', port=8000)
    # app.run(debug=True, host='127.0.0.1', port=8000)
    # app.run(debug=True)
