from pytube import YouTube
import requests
import json
import re
import subprocess

# youube data api v3
def get_youtube_search(query):
    assert type(query) is str
    url = 'https://www.googleapis.com/youtube/v3/search?part=id&maxResults=10&q='+query+'&relevanceLanguage=ko&key=AIzaSyALf1tdgaDLvyplfblk-q6lQQvuT6DIoXE'
    res = requests.get(url)
    r = json.loads(res.text)
    
    if res.status_code != 200:
        print('Error, status:', res.status_code)
        return []

    video_ids = []
    for i in r['items']:
        try:
            video_ids.append(i['id']['videoId'])
        except: pass
    
    if len(video_ids)>0:
        return video_ids
    else: return []

def compare_duration(vid):
    assert type(vid) is str
    url = 'https://www.googleapis.com/youtube/v3/videos?key=AIzaSyALf1tdgaDLvyplfblk-q6lQQvuT6DIoXE'
    url += '&part=contentDetails&id='+vid
    res = requests.get(url)
    r = json.loads(res.text)
    
    dur = r['items'][0]['contentDetails']['duration']
    try:
        dur.index('H')
        print('too long')
        return False # 1시간 이상은 무조건 자름
    except: pass
    dur_ = dur[2:]
    m = int(dur_[:dur_.index('M')])
    s = int(dur_[dur_.index('M')+1:dur_.index('S')])
    dur = m*60 + s
    print('vid:', vid, ', duration:', dur)
    
    dur_min = 180
    dur_max = 300
    if res.status_code == 200 and dur>dur_min and dur<dur_max:
        return True
    else:
        print('too long')
        return False

# DOWNLOAD AUDIO FILE
# https://python-pytube.readthedocs.io/en/latest/user/quickstart.html
def download_audio(video_id):
    assert type(video_id) is str
    url = 'https://www.youtube.com/watch?v='+video_id
    yt = YouTube(url)
    
    print(yt.title)
    
    # itag 249,250,251만 시용
    r = yt.streams.get_by_itag(249)
    if not r: # 249 itag 없음
        r = yt.streams.get_by_itag(250)
        if not r: # 250 itag 없음
            r = yt.streams.get_by_itag(251)
            if not r: # 251 itag 없음
                r = yt.streams.get_by_itag(140) #.mp4
                if not r: return 'Sorry, no audio stream'
            
    r.download('./static/audio')
    reg = re.compile('[\/:*?"<>|,.\'"]') # 저장시에 파일이름에 못들어가는 특수문자 보정 
    title = reg.sub('', yt.title)
    return title+'.webm'

# use youtube-dl
# subprocess로 작동하나 이게 훨씬 빠름
def download_audio_sub_process(video_id, file_name, ext='mp3'):
    assert type(video_id) is str and type(file_name) is str
    assert file_name.find(' ')==-1, 'file_name should have no spacebar(" ")'

    command = 'youtube-dl https://www.youtube.com/watch?v={} -x --audio-format {} --output ./static/audio/{}.%(ext)s'.format(video_id, ext, file_name)
    print(command)
    subprocess.call(command, shell=True)
    return file_name+'.'+ext