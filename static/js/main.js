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
  console.log(base64data, typeof base64data);
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
  });
}


var audioPlayer = document.getElementById('audioPlayer');
function attachAudio(){
  audioPlayer.src = URL.createObjectURL(new Blob(recordedBlobs, { type : 'audio/webm'}));
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