# all the imports
import sqlite3, json, jinja2, os, html
import datetime
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, send_from_directory
from flask_cors import CORS, cross_origin # http://flask-cors.readthedocs.io/en/latest/
# from flaskext.mysql import MySQL

from speech_recog import *
from speech_syn import *
from musicDownlader import *

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

@app.route("/api/music", methods=['POST'])
def music():
    if type(request.data) is bytes: body = json.loads(request.data.decode())
    else: body = json.loads(request.data)
    # print(body) # base64 code 보여줌
    music = body['music']
    music = music.replace(' ', '_') # 띄어쓰기 있으면 subprocess 파라미터에서 에러
    res = {'findIt': 0, "music": ''}
    music_file = None

    vids = get_youtube_search(music)
    print(vids)
    if len(vids)>0:
        for v in vids:
            if compare_duration(v):
                # music_file = download_audio(v)
                music_file = download_audio_sub_process(v, music)
                break
        # 음악 길이 적당한거 못찾았을 때  
        if not music_file:
            res['music'] = "음악의 길이가 너무 길어요."
            print(res)
            return json.dumps(res)
        # 찾았을 때
        res['findIt'] = 1
        res['music'] = music_file
        print(res)
        return json.dumps(res)
    else: # 제목 서칭이 안될 때
        res['music'] = '찾는 음악이 없습니다.'
        return json.dumps(res)

@app.route("/api/text2speech", methods=['POST'])
def synthesis():
    if type(request.data) is bytes: body = json.loads(request.data.decode())
    else: body = json.loads(request.data)
    # print(body) # base64 code 보여줌
    text = body['text']
    res = {'success': 1, "path": 'static/audio/res.mp3'}
    res['success'] = text2speech(text)
    return json.dumps(res)


    


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

if __name__ == '__main__':
    context = ('ssl/cert.pem', 'ssl/key.pem') # for https ssl
    app.run(debug=True, host='0.0.0.0', port=5000, ssl_context=context) # 이건 내부, 외부 한번에
    # app.run(debug=True, host='10.0.1.21', port=8000)
    # app.run(debug=True, host='127.0.0.1', port=8000)
    # app.run(debug=True)
