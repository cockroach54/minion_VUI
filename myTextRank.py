# import sys
# from pprint import pprint
import re
import math, random, csv, operator, networkx as nx
from nltk.collocations import BigramCollocationFinder
import json

# from gensim.summarization import summarize
# from gensim.summarization import keywords
# from gensim.summarization.textcleaner import split_sentences

import requests
from bs4 import BeautifulSoup

# pos tagging, tokenizing
from konlpy.tag import Twitter
tagger = Twitter()
from collections import Counter

import asyncio

"""
page rank class
"""

class textRank:
    def search_naver_news(self, query):
        assert type(query) is str

        # ----------------시연용 news 3개 사전등록
        if query.find('방탄')>-1:
            news = {
                'link': "http://entertain.naver.com/ranking/read?oid=119&aid=0002262798",
                'title': "방탄소년단 'DNA' 뮤비 유튜브 4억뷰, K팝 그룹 최초"
            }
            return news
        elif query.find('종원')>-1:
            news = {
                'link': "http://entertain.naver.com/ranking/read?oid=382&aid=0000652476",
                'title': "백종원의 골목식당’ 뚝섬 편 후폭풍 청와대 국민청원 게시물 등장"
            }
            return news
        elif query.find('시위')>-1:
            news = {
                'link': "http://news.naver.com/main/read.nhn?mode=LSD&mid=sec&sid1=102&oid=005&aid=0001104387",
                'title': "혜화역 두 번째 시위, 그들이 ‘빨간색’ 옷을 입고 거리로 나온 이유는?"
            }
            return news

        # ----------------original
        url = 'https://openapi.naver.com/v1/search/news?sort=sim&query='+query
        headers = {
                'Content-Type': 'plain/text',
                'X-Naver-Client-Id': '1cPKtmLC3sxexUaoPnQt',
                'X-Naver-Client-Secret': 'OdccSBHvbM',
            }
        res = requests.get(url, headers=headers)
        res = json.loads(res.text)

        for i in res['items']:
            if i['link'].find('http://news.naver.com')>-1:
                print(i['link'], '\n', i['title'])
                reg = re.compile('<[^<.]*>|&[^&.]*;')  # title에서 태그<p></p> 및 특수문자&quot; 제거
                
                news = {
                    'link': i['link'],
                    'title': reg.sub('', i['title'])
                }
                return news
        print('찾는 뉴스가 네이버에 없습니다.')
        news = {
            'link': False,
            'title': ''
        }
        return news

    def getNews(self, url):
        self.url = url
        text = requests.get(self.url)
        # print('&&&&&&&', len(text.text))
        soup = BeautifulSoup(text.text, 'html.parser')
        # save news title
        self.title = soup.find(id='articleTitle').get_text().strip()

        # 필요한 텍스트만 파싱
        self.article_parsed= []
        self.get_first = True # 뒤에서 리드문 포함        

        r = re.compile('.+@.+[.]\w+') # email 거르기
        for i in soup.find(id='articleBodyContents').children:
            try:
                i = i.strip() # 바로 자식노드의 텍스트만
                if len(i)>10 and not r.match(i): # 주석 거르기
                    self.article_parsed.extend(i.split('. '))
            except:
                pass
        
        return self.article_parsed

    # async def getNews(self, url):
    #     self.url = url
    #     loop = asyncio.get_event_loop()  
    #     asyncio.set_event_loop(loop)
    #     s = requests.Session()
    #     task = loop.run_in_executor(None, s.get, self.url)
    #     text = await task
    #     soup = BeautifulSoup(text.text, 'html.parser')


    def parse(self, article):
        soup = BeautifulSoup(article.text, 'html.parser')
        is_ent = False # entertain news인지 판별
        # save news title
        try: self.title = soup.find(id='articleTitle').get_text().strip() # original news
        except:
            self.title = soup.find(class_='end_tit').get_text().strip() # entertin news
            is_ent = True

        # 필요한 텍스트만 파싱
        self.article_parsed= []
        # 리드문 파싱 - 20글자 이상이고 '.'로 끝나는 문장 중 가장 먼저 나오는 문장
        self.lead_sentence = ''
        self.get_first = False # 뒤에서 리드문 포함 안함 

        r = re.compile('.+@.+[.]\w+') # email 거르기
        if is_ent: body_id = 'articeBody' # entertin news
        else: body_id = 'articleBodyContents' # original news

        for i in soup.find(id=body_id).children:
            try:
                i = i.strip() # 바로 자식노드의 텍스트만
                if len(i)>15 and not r.match(i): # 주석 거르기
                    if not i[-1] !='.': # 문단당 20글자 이상 조건으로 
                        self.article_parsed.extend(i.split('. '))
            except:
                pass
        
        self.lead_sentence = self.article_parsed[0]
        return self.article_parsed

    def _tokenize(self, doc):
        return ['/'.join(t) for t in tagger.pos(doc, norm=True, stem=True)]

    def setGraph(self):
        sentences = []
        for sentence in self.article_parsed:
            sentences.append(self._tokenize(sentence))
        
        # 'Noun','Verb','Adjective' 만 필터링
        self.pos_tagged = []
        self.pos_tagged_noun = [] # for keyword extraction
        for sentence in sentences:
            self.pos_tagged.append([w for w in sentence 
                            if w.split('/')[1] in ['Noun','Verb','Adjective']])
            # 이건 top keyword뽑기 위해서 
            self.pos_tagged_noun.append([w for w in sentence 
                            if w.split('/')[1] in ['Noun']])
        
        # count words
        self.word_count=[]
        for i in self.pos_tagged:
            self.word_count.append(Counter(i))
            
        # make network, calc jaccard similarity 
        self.net=[]
        for i, el in enumerate(self.word_count[:-1]):
            for i2 in range(i+1,len(self.word_count)):
                sim = sum((self.word_count[i] & self.word_count[i2]).values()) / (sum((self.word_count[i] | self.word_count[i2]).values()) + 0.001) # +0.0001은 division 0 방지용
                if sim>0: self.net.append([i, sim, i2])

    def _calcRank(self, network, num_iter):
        # make networkx graph
        graph = nx.Graph()
        
        nodes = set([row[0] for row in network])
        edges = [(row[0], row[2]) for row in network]
        num_nodes = len(nodes)
        rank = 1/float(num_nodes)
        graph.add_nodes_from(nodes, rank=rank)
        graph.add_edges_from(edges)

        V = float(len(graph))
        s = 0.85 # non random jump value
        ranks = dict()
        for key, node in graph.nodes(data=True):
            ranks[key] = node.get('rank')

        for _ in range(num_iter):
            for key, node in graph.nodes(data=True):
                rank_sum = 0.0
                neighbors = graph[key]
                for n in neighbors: # for each neighbors, gather its textRank
                    if ranks[n] is not None:
                        outlinks = len(list(graph.neighbors(n)))
                        rank_sum += (1 / float(outlinks)) * ranks[n]
                ranks[key] = ((1 - s) * (1/V)) + s*rank_sum
                
        # sorted rank index 
        sorted_ranks = sorted(ranks.items(), key=operator.itemgetter(1), reverse=True)
        return sorted_ranks
        
    def getSummary(self, num_summ=3, num_iter=10, get_first=False):
        # calculate only rank 
        self.sorted_summ_ranks = self._calcRank(self.net, num_iter)

        # summarty sentences
        self.summary = []
        # get lead sentence; first sentence
        try: get_first = self.get_first
        except: pass
        
        if get_first:
            self.summary.append(self.lead_sentence)

        # print after sorting
        for t in sorted(self.sorted_summ_ranks, key=lambda idx: idx[0]):
            if t[0]==0: continue # 앞에서 리드문 맨 앞에 넣었으므로 패스
            self.summary.append(self.article_parsed[t[0]])            

        return self.summary[:num_summ]
    
    def getKeyword(self, num_key=10, num_iter=10):
        # find bigram collocation
        for doc in self.pos_tagged_noun:
            f = BigramCollocationFinder.from_words(doc, window_size=5)
            if 'fd' in locals():
                fd += f.ngram_fd
            else: fd = f.ngram_fd

        self.net_keyword = []
        for i in fd:
            self.net_keyword.append([i[0], fd[i], i[1]])

        # calculate only rank 
        self.sorted_key_ranks = self._calcRank(self.net_keyword, num_iter)

        # return self.sorted_key_ranks[:num_key]
        return [i[0].split('/')[0] for i  in self.sorted_key_ranks[:num_key]]

    def getAnswer(self, query):
        qq =['/'.join(t) for t in tagger.pos(query, norm=True, stem=True) if t[1] in ['Noun','Verb','Adjective']]
        cc = Counter(qq)
        print(cc)
        # jaccard sim 계산
        ans = []
        for idx, c in enumerate(self.word_count):
            sim = sum((c & cc).values()) / sum((c | cc).values())
            if sim>0: ans.append([idx, sim])

        ans = sorted(ans, key=lambda i: i[1], reverse=True)

        answers = [(self.article_parsed[i[0]], i[1]) for i in ans]
        # print(answers[:5])
        return answers

    # 나무위키 파싱용
    def nwiki(self, query):
        req = requests.get('https://namu.wiki/w/' + query)
        html = req.text
        soup = BeautifulSoup(html, 'html.parser')
        
        reg = re.compile('\[\d*\]|[‘’]') # 주석 없애기 ex) [14], [2] 

        res = soup.findAll("div", {"class": "wiki-heading-content"})
        phrase = []
        for i in res:
            phrase.extend(i.findAll('p'))
            
        # 짧은 문장으로 재파싱
        tt = []
        for i in phrase:
            tmp = i.get_text()
            try:
                tmp = [reg.sub('', doc).strip() for doc in tmp.split('. ')
                    if len(doc)>20 and len(doc)<100]
                tt.extend(tmp)
            except: pass

        # textRank 시간때문에 최대 100문장만
        return tt[:100] 