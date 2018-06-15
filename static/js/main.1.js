/*
 *  Copyright (c) 2015 The WebRTC project authors. All Rights Reserved.
 *
 *  Use of this source code is governed by a BSD-style license
 *  that can be found in the LICENSE file in the root of the source
 *  tree.
 */

'use strict';

// Put variables in global scope to make them available to the browser console.
var audio = document.getElementById('audioPlayer');
var audio_sub = document.getElementById('audioPlayer_effect');
var loader = document.getElementById('loader'); // loading icon
var controller = new Controller();
var startTime;
var endTime;

var constraints = window.constraints = {
  audio: true,
  video: false
};

// audio, controller 연동
audio.addEventListener('pause', () => {
  controller.paused = true;
  audio_sub.src = 'audio/stop.mp3';
  audio_sub.play();
});
audio.addEventListener('ended', () => controller.paused = true);
audio.addEventListener('play', () => controller.paused = false);
audio.addEventListener('error', () => {
  console.log('req ".m4a" error. change src and request again.');
  controller.say('노래를 불러오는 중 오류가 발생했어요. 다른 노래를 검색해 주세요.');
  // audio.src = audio.src.replace(/\.\w*$/, '.temp.m4a'); // .mp3, .opus -> .temp.m4a
  // audio.play();
});
// 텍스트로 직접 입력해서 명령하기
document.getElementById('interpret').addEventListener('click', function(){
  var order = document.getElementById('order');
  var text = order.value;
  controller.interpret(text.trim());
  order.value = '';
})
// enter keyup binding
document.getElementById('order').addEventListener('keyup', function(e){
  if(e.keyCode == 13){
    var mouseEvent = document.createEvent("MouseEvents");
    mouseEvent.initEvent("click", false, true);
    document.getElementById('interpret').dispatchEvent(mouseEvent);
  }
});

function handleSuccess(stream) {
  var audioTracks = stream.getAudioTracks();
  console.log('Got stream with constraints:', constraints);
  console.log('Using audio device: ' + audioTracks[0].label);
  stream.onactive = function() {
    console.log('Stream start');
  };
  stream.oninactive = function() {
    console.log('Stream ended');
  };
  window.stream = stream; // make variable available to browser console
  audio.srcObject = stream;
}

function handleError(error) {
  console.log('navigator.getUserMedia error: ', error);
}

navigator.mediaDevices.getUserMedia(constraints).
    then(handleSuccess).catch(handleError);

  
// ---------------sw

var mediaSource = new MediaSource();
// mediaSource.addEventListener('sourceopen', handleSourceOpen, false);
var mediaRecorder;
var recordedBlobs;
var sourceBuffer;

function startRecording() {
  startTime = new Date();
  recordedBlobs = [];
  var options = {mimeType: 'audio/webm', audioBitsPerSecond: 16000};
  // if (!MediaRecorder.isTypeSupported(options.mimeType)) {
  //   console.log('######', options.mimeType + ' is not Supported');
  //   options = {mimeType: 'audio/webm'};
  // }
  // 레코딩 시작 시청각적으로 알리기
  document.getElementById('rec').style.color = 'red';
  audio_sub.src= 'audio/stop.mp3'
  audio_sub.play();

  try {
    mediaRecorder = new MediaRecorder(window.stream);
  } catch (e) {
    console.error('Exception while creating MediaRecorder: ' + e);
    return;
  }
  console.log('Created MediaRecorder', mediaRecorder);
  mediaRecorder.onstop = handleStop;
  mediaRecorder.ondataavailable = handleDataAvailable;
  mediaRecorder.start(10); // collect 10ms of data
  console.log('MediaRecorder started', mediaRecorder);
}

function handleDataAvailable(event) {
  if (event.data && event.data.size > 0) {
    recordedBlobs.push(event.data);
  }
}

function handleStop(event) {
  document.getElementById('rec').style.color = 'transparent';  
  console.log('Recorder stopped: ', event);
}

function stopRecording() {
  mediaRecorder.stop();
  console.log('Recorded Blobs: ', recordedBlobs);
  blob2base64();
}

var reader = new FileReader();
var base64data; // request 보낼 오디오 데이터

function blob2base64() {
  var superBuffer = new Blob(recordedBlobs, {type: 'audio/webm'});
  reader.readAsDataURL(superBuffer); 
}

// 이 이벤트가 api 호출하는 직접 부분
reader.onloadend = function() {
  base64data = reader.result;                
  // console.log(base64data, typeof base64data);
  base64data = base64data.replace(/data:audio\/webm;base64,/, '');

  loader.style.display = 'initial'; // show the loader icon 
  
  reqSpeech2text(base64data).then(query => {
    query = query[query.length-1] // 배열로 값이 들어옴, 마지막 문자 사용
    console.log(query);
    endTime = new Date();
    var STT_dur = endTime - startTime;
    console.log('STT Response Time:', STT_dur/1000, 'sec');
    
    // 컨트롤러에 입력 전달
    document.getElementById('query').value = query
    controller.interpret(query);
    if(loader.style.display=='initial') loader.style.display = 'none'; // show the loader icon     
  }).catch(()=>{
    controller.say('말씀을 알아듣지 못했어요. 다시 천천히 말해줄래요?');
  });
}


function attachAudio(){
  audio_sub.src = URL.createObjectURL(new Blob(recordedBlobs, { type : 'audio/webm'}));
}

//-----------file download
var downloadLink = document.getElementById('download');
function download(){
  downloadLink.href = URL.createObjectURL(new Blob(recordedBlobs, { type : 'audio/webm'}));
  downloadLink.download = 'down2.webm';
}

//-----------api request
function reqSpeech2text(base64){
  var httpRequest;
  if(window.XMLHttpRequest) httpRequest = new XMLHttpRequest();
  else if(window.ActiveXObject) httpRequest = new ActiveXObject("Microsoft.XMLHTTP");
  var url= window.location.origin;
  url += '/api/speech2text';
  console.log(url);
  var headers ={
    // 'Accept': 'application/json'
  };
  var payloads = {
    'audio': base64,
  };

  return new Promise((resolve, reject)=>{
    httpRequest.open('POST', url, true);
    for (key in headers){
      httpRequest.setRequestHeader(key, headers[key]);            
    }
    httpRequest.send(JSON.stringify(payloads));
    
    httpRequest.onreadystatechange = function(){
        if(httpRequest.readyState==4){
            if(httpRequest.status==200){ //이건 클라이언트꺼 서버것 아님
                var res = httpRequest.responseText;
                res = JSON.parse(res);
                resolve(res);
            }
            else{
              console.error('server has errors.');
              reject();
            }
        }
    };
  });
}

function reqMusic(query){
  var httpRequest;
  if(window.XMLHttpRequest) httpRequest = new XMLHttpRequest();
  else if(window.ActiveXObject) httpRequest = new ActiveXObject("Microsoft.XMLHTTP");
  var url= window.location.origin;
  url += '/api/music';
  console.log(url);
  var headers ={
    // 'Accept': 'application/json'
  };
  var payloads = {
    'music': query,
  };

  return new Promise((resolve, reject)=>{
    httpRequest.open('POST', url, true);
    for (key in headers){
      httpRequest.setRequestHeader(key, headers[key]);            
    }
    httpRequest.send(JSON.stringify(payloads));
    
    httpRequest.onreadystatechange = function(){
        if(httpRequest.readyState==4){
            if(httpRequest.status==200){ //이건 클라이언트꺼 서버것 아님
                var res = httpRequest.responseText;
                res = JSON.parse(res);
                resolve(res);
            }
            else{
              console.error('server has errors.');
              reject();
            }
        }
    };
  });
}

function reqText2speech(text){
  var httpRequest;
  if(window.XMLHttpRequest) httpRequest = new XMLHttpRequest();
  else if(window.ActiveXObject) httpRequest = new ActiveXObject("Microsoft.XMLHTTP");
  var url= window.location.origin;
  url += '/api/text2speech';
  console.log(url);
  var headers ={
    // 'Accept': 'application/json'
  };
  var payloads = {
    'text': text,
  };

  return new Promise((resolve, reject)=>{
    httpRequest.open('POST', url, true);
    for (key in headers){
      httpRequest.setRequestHeader(key, headers[key]);            
    }
    httpRequest.send(JSON.stringify(payloads));
    
    httpRequest.onreadystatechange = function(){
        if(httpRequest.readyState==4){
            if(httpRequest.status==200){ //이건 클라이언트꺼 서버것 아님
                var res = httpRequest.responseText;
                res = JSON.parse(res);
                resolve(res);
            }
            else{
              console.error('server has errors.');
              reject();
            }
        }
    };
  });
}



function tts(text){
  var payloads = {
    'speaker': 'mijin',
    'speed': 0,
    'text': text,
  };

  $.ajax({
             
    type : "POST",
    url : 'https://naveropenapi.apigw.ntruss.com/voice/v1/tts',
    dataType : "json",
    data: JSON.stringify(payloads),
    // jsonpCallback: "myCallback",
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'X-NCP-APIGW-API-KEY-ID': 'kwjiwaqr0b',
      'X-NCP-APIGW-API-KEY': 'PU5Ewecvdnch7gUHg6x38zILYXkjvPssCGOVwJuz',
    },
    error : function(){
      console.log('fail');
    },
    success : function(data){
      console.log('success', data);
    }
     
  });
}