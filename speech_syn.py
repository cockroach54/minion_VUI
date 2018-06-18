# 네이버 음성합성 Open API 예제
import os
import sys
import urllib.request

def text2speech(text):
  client_id = "클로바 개인 계정"
  client_secret = "클로바 개인 계정"

  data = "speaker=mijin&speed=0&text=" + text
  url = "https://naveropenapi.apigw.ntruss.com/voice/v1/tts"
  request = urllib.request.Request(url)
  request.add_header("X-NCP-APIGW-API-KEY-ID",client_id)
  request.add_header("X-NCP-APIGW-API-KEY",client_secret)
  response = urllib.request.urlopen(request, data=data.encode('utf-8'))
  rescode = response.getcode()

  if(rescode==200):
      print("TTS mp3 저장")
      response_body = response.read()
      with open('static/audio/res.mp3', 'wb') as f:
          f.write(response_body)
      return 1
  else:
      print("Error Code:" + rescode)
      return 0

