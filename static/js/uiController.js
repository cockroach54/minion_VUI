/* global var reference
var audio = document.getElementById('audioPlayer');
var audio_sub = document.getElementById('audioPlayer_effct');
*/

// control input voice text
function Controller(){
  this.paused = true; // 현재 미니언 상태
}

// 인풋 의미 해석
Controller.prototype.interpret = function(text){
  if (!text) return // 아무말도 안했으면 그냥 리턴
  // wake up word 제거
  text = text.replace('미니언', '').trim();

  // 기능 구분
  r_stop = new RegExp(/잠시|잠깐|스톱|스탑|일시정지|일시중지|멈춰/);
  r_resume = new RegExp(/계속|재개|재가동|다시/);
  r_music = new RegExp(/노래켜|재생/);
  
  if(r_stop.test(text.replace(/\s/g, ''))){ // 일시정지
    console.log('미니언이 일시정지 되었습니다.')
    audio.pause();
    this.paused = true;

    audio_sub.src = 'audio/stop.mp3';
    audio_sub.play();
  }
  else if(this.paused && r_resume.test(text.replace(/\s/g, ''))){ // 일시정지 해제
    console.log('미니언이 재가동 되었습니다.')
    audio.play();
    this.paused = false;
  }
  else if(this.paused && r_music.test(text.replace(/\s/g, ''))){ // 노래 재생
    console.log('미니언이 노래를 켰습니다.')
    if(!audio.src || audio.src=='') audio.src='audio/music.mp3'
    audio.play();
    this.paused = false;
  }
  else if(this.paused){ // 뉴스내 질문하기
    console.log('미니언에게 질문을 했습니다.')    
    startTime = new Date();
    reqAns(text).then(res => {
      endTime = new Date();
      var QUERY_dur = endTime - startTime;
      console.log('QUERY Response Time:', QUERY_dur/1000, 'sec');
      console.log(res);
      // show top3 
      document.getElementById('news_answers').innerHTML = res['answers'].slice(0,3).join('\n\n');
      // 여기는 미니언 답변이 한마디로 들어가는 자리
      document.getElementById('result').innerText = res['answers'][0];
    });
  }
}