/* global var reference
var audio = document.getElementById('audioPlayer');
var audio_sub = document.getElementById('audioPlayer_effct');
*/

// control input voice text
function Controller(){
  this.paused = true; // 현재 미니언 상태
  this.output = {
    thank: ['별말씀을요.', '당연히 그러시겠죠.', '당연한 건데요 뭘.'],
    bye: ['이제 안녕~', '다음에 또 봐요.'],
  }
}

// 인풋 의미 해석
Controller.prototype.interpret = function(text){
  if (!text) return // 아무말도 안했으면 그냥 리턴
  // wake up word 제거
  r_minion = new RegExp(/미니언|민현|민혁|미년/);
  text = text.replace(r_minion, '').trim();

  // 기능 구분
  r_stop = new RegExp(/잠시|잠깐|스톱|스탑|일시정지|일시중지|멈춰|노래꺼/);
  r_resume = new RegExp(/계속|재개|재가동|다시/);
  r_music = new RegExp(/노래켜|재생|들려줘|불러줘|들려줄래|불러줄래/);
  r_thank = new RegExp(/고마워|땡큐|고맙/);
  r_bye = new RegExp(/잘가|안녕|다음에/);  
  
  if(r_stop.test(text.replace(/\s/g, ''))){ // 일시정지
    console.log('미니언이 일시정지 되었습니다.');
    audio.pause();
    this.paused = true;

    audio_sub.src = 'audio/stop.mp3';
    audio_sub.play();
  }
  else if(this.paused && r_resume.test(text.replace(/\s/g, ''))){ // 일시정지 해제
    console.log('미니언이 재가동 되었습니다.');
    audio.play();
    this.paused = false;
  }
  else if(this.paused && r_music.test(text.replace(/\s/g, ''))){ // 노래 재생
    // if(!audio.src || audio.src=='') audio.src='audio/music.mp3'
    
    // refine query
    text = text.replace(/\s/g, '');
    text = text.replace(r_music, '');
    console.log('미니언에게 "'+text+'"를 요청합니다.');

    // 노래 찾는 시간 오래걸리니 효과음 필요
    this.say('노래를 찾고 있습니다. 잠시만 기다려 주세요');

    reqMusic(text).then(res =>{
      if(res['findIt']){
        audio_sub.src = 'audio/stop.mp3';
        audio_sub.play();

        console.log('미니언이 "'+text+'"를 재생합니다.');        
        audio.src='audio/'+res['music']    
        audio.play();
        this.paused = false;
      }
      else this.say(res['music'])
    });
  }
  else if(this.paused && r_thank.test(text.replace(/\s/g, ''))){ // '고마워' 응답
    console.log('미니언이 자유롭게 응답합니다.');
    var res = this.output['thank'];
    this.say(res[(Math.random()*res.length<<0)]);
  }
  else if(this.paused && r_bye.test(text.replace(/\s/g, ''))){ // '안녕' 응답
    console.log('미니언이 자유롭게 응답합니다.');
    var res = this.output['bye'];
    this.say(res[(Math.random()*res.length<<0)]);
  }
  else if(this.paused){ // 뉴스내 질문하기. 현재는 위에 아무것도 안걸렸을때
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
      document.getElementById('result').innerText = res['answers'][0][0];
      // 미니언 토스트
      this.say(res['answers'][0][0]); // 미니언 토스트
    });
  }
}

// 아웃풋 토스트 만들기
Controller.prototype.say = function(result){
  var toastHTML = `<span class="minion">Minion: </span><div>${result}</div>`;
  M.toast({html: toastHTML});

  reqText2speech(result).then(res =>{
    if(res['success']){
      var path = res['path'].replace('static/', '');
      // 캐시 리프레시 문제때문에 타임스탬프 필요
      var t = new Date();
      path = path+'?'+t.getTime();
      console.log(path);

      audio_sub.src = path; // audio/res.mp3?1020399845
      audio_sub.play();
    }
    else{
      console.log('음성합성 도중 오류가 발생했습니다.')
      audio_sub.src = 'audio/error.mp3';
      audio_sub.play();
    } 
  });
}