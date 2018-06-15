# all the imports
import sqlite3, json, jinja2, os, html
import datetime
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, send_from_directory
from flask_cors import CORS, cross_origin # http://flask-cors.readthedocs.io/en/latest/
# from flaskext.mysql import MySQL

# for NER tensorflow model
from NER_model import *

# for 3rd party api
from speech_recog import *
from speech_syn import *
from musicDownlader import *

from myTextRank import *
import operator, asyncio, jpype
p = textRank() # 네이버 뉴스용
p2 = textRank() # 나무위키용 // 네이버랑 저장하는 도큐먼트가 다르므로 따로 만들어여함

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
                music_file = download_audio_sub_process(v, music, ext='mp3')
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
# 뉴스주소 받아서 네이버 뉴스 찾기
@app.route("/news", methods=['POST'])
def news():
    if type(request.data) is bytes: body = json.loads(request.data.decode())
    else: body = json.loads(request.data)
    print(body)
    query = body['query']
    res = p.search_naver_news(query)
    p.url = res['link']

    # 나무위키도 이때 찾기
    n_doc = p2.nwiki(query.split()[0]) #무조건 첫단어만 검색
    if n_doc: 
        print('해당 나무위키 문서를 찾았습니다.')
        p2.article_parsed = n_doc

    return json.dumps(res)

# 뉴스 요약하기
@app.route("/summary", methods=['POST'])
def summary():
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
      # article = p.getNews(news_url)
      article = requests.get(news_url)
      p.parse(article)
    # article = requests.get(p.url)
    # p.parse(article)
    # textrank
    p.setGraph()
    p.getSummary()
    news_summ = p.getSummary(num_summ=3)
    keywords = p.getKeyword(5)

    # 나무위키 도큐먼트 찾은 경우만
    if p2.article_parsed:
        p2.setGraph()
        p2.getSummary()

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

    # KB에서 제일 먼저 검색
    # 적당한 답이 없으면 뉴스와 위키에서 검색
    ext = predict(sess, query)
    print(ext)

    answers = get_answer(ext)
    print(answers)

    if answers:
        res = {
            'answers': [answers],
        }
        return json.dumps(res)

    # 뉴스요약 먼저 하고 질문해야함
    # 뉴스 내 답변 검색
    res_ = []
    for i,e in enumerate(p.getAnswer(query)):
        res_.append(('뉴스에서 발췌한 답변입니다. '+e[0], e[1]))

    # 나무위키 내 답변 겁색
    # 나무위키 도큐먼트 찾은 경우만
    if p2.article_parsed:
        for i,e in enumerate(p2.getAnswer(query)):
            res_.append(('위키에서 발췌한 답변입니다. '+e[0], e[1]))

    res_.sort(key=lambda a:float(a[1]), reverse=True)

    # 최종 리턴
    print(res_[:5])
    try:
      res = {
        'answers': res_
      }
    except:
      res = {
        'answers': ['get news first!!']
      }
    

    return json.dumps(res)

# -------------------------for NER query
@app.route("/api/ner", methods=['POST'])
def ner():
    if type(request.data) is bytes: body = json.loads(request.data.decode())
    else: body = json.loads(request.data)
    query = body['query']

    ext = predict(sess, query)
    print(ext)

    answers = get_answer(ext)
    print(answers)

    res = {
        'answers': [answers],
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
    app.run(debug=True, host='0.0.0.0', port=8000, ssl_context=context) # 이건 내부, 외부 한번에
    # app.run(debug=True, host='10.0.1.21', port=8000)
    # app.run(debug=True, host='127.0.0.1', port=8000)
    # app.run(debug=True)
