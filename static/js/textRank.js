console.log('main.js has loaded...');
var news;

// 뉴스 요약하기 이벤트
var summ_news = document.getElementById('summ_news');
summ_news.addEventListener('click', function () {
  var url = document.getElementById('url').value || controller.newsUrl;
  console.log(url);
  // iframe 변경
  // document.getElementById('iframe').setAttribute('src', url);
  // news 요청
  reqSummary(url).then(res => {
    console.log(res);
    news = res;

    // view에 표시하기
    document.getElementById('news_title').innerHTML = news['news_title'];
    document.getElementById('news_keywords').innerHTML = news['keywords'].join(' ');
    document.getElementById('news_origin').innerHTML = news['news_origin'].join('\n\n');
    document.getElementById('news_summ').innerHTML = news['news_summ'].join('\n\n');
    
    // keywords css 입히기
    for (k of news['keywords']) findKeyword(k);
    
    controller.newsSummary = document.getElementById('news_summ').innerText;
    controller.newsKeyword = news['keywords'].join(', ');

    controller.say(controller.newsSummary); // 뉴스요약 말하기
    // controller.say("이 뉴스의 키워드는 '" + news['keywords'].join(', ') + "' 입니다."); // 미니언 토스트
  }).catch(()=>{
    controller.say('죄송해요. 뉴스를 요약하는데 실패했어요');
  });
});
// enter keyup binding
document.getElementById('url').addEventListener('keyup', function(e){
  if(e.keyCode == 13){
    var mouseEvent = document.createEvent("MouseEvents");
    mouseEvent.initEvent("click", false, true);
    summ_news.dispatchEvent(mouseEvent);
  }
});


// 뉴스 질문하기 이벤트
var query_news = document.getElementById('query_news');
query_news.addEventListener('click', function(){
  var query = document.getElementById('query').value;

  reqAns(query).then(res => {
    console.log(res);
    // show top3 
    document.getElementById('news_answers').innerHTML = res['answers'].slice(0,3).join('\n\n');
    controller.say(res['answers'][0][0]); // 미니언 토스트
  });
});
// enter key up binding
document.getElementById('query').addEventListener('keyup', function(e){
  if(e.keyCode == 13){
    var mouseEvent = document.createEvent("MouseEvents");
    mouseEvent.initEvent("click", false, true);
    query_news.dispatchEvent(mouseEvent);
  }
});


function findKeyword(keyword){
  // keyword = '\\b' + keyword +  '\\b';
  var re = new RegExp(keyword, 'g');
  var randRGB = 'rgb('+(Math.random()*128<<0)+','+(Math.random()*128<<0)+','+(Math.random()*128<<0)+')';
  // 뉴스 원본에서 키워드 찾기
  var dom = document.getElementById('news_origin');
  var doc = dom.innerHTML;
  doc = doc.replace(re, '<span class="keywords" style="color:'+randRGB+'">'+keyword+'</span>');
  dom.innerHTML = doc;
  // 뉴스 요약에서 키워드 찾기
  var dom2 = document.getElementById('news_summ');
  var doc2 = dom2.innerHTML;
  doc2 = doc2.replace(re, '<span class="keywords" style="color:'+randRGB+'">'+keyword+'</span>');
  dom2.innerHTML = doc2;
  // 주요 키워드 표시
  var dom3 = document.getElementById('news_keywords');
  var doc3 = dom3.innerHTML;
  doc3 = doc3.replace(re, '<span class="keywords" style="color:'+randRGB+'">'+keyword+'</span>');
  dom3.innerHTML = doc3;
}

//-----------------------------api request
function reqNews(query) {
  var httpRequest;
  if (window.XMLHttpRequest) httpRequest = new XMLHttpRequest();
  else if (window.ActiveXObject) httpRequest = new ActiveXObject("Microsoft.XMLHTTP");
  var url = window.location.origin;
  url += '/news';
  var headers = {  //key 요구가 없네...
    // 'Content-Type': 'application/json'
  };
  var payloads = {
    'query': query,
  }
  
  return new Promise((resolve, reject) => {
    httpRequest.open('POST', url, true);
    for (key in headers){
        httpRequest.setRequestHeader(key, headers[key]);            
      }
    httpRequest.send(JSON.stringify(payloads));

    httpRequest.onreadystatechange = function () {
      if (httpRequest.readyState == 4) {
        if (httpRequest.status == 200) { //이건 클라이언트꺼 서버것 아님
          var res = httpRequest.responseText;
          var res = JSON.parse(res);
          resolve(res);
        }
        else {
          console.error('server has errors.');
          reject();
        }
      }
    };
  });
}

function reqSummary(news_url) {
  var httpRequest;
  if (window.XMLHttpRequest) httpRequest = new XMLHttpRequest();
  else if (window.ActiveXObject) httpRequest = new ActiveXObject("Microsoft.XMLHTTP");
  var url = window.location.origin;
  url += '/summary';
  var headers = {  //key 요구가 없네...
    // 'Content-Type': 'application/json'
  };
  var payloads = {
    'news_url': news_url,
    'news_doc': document.getElementById('doc').value,
  }
  
  return new Promise((resolve, reject) => {
    httpRequest.open('POST', url, true);
    for (key in headers){
        httpRequest.setRequestHeader(key, headers[key]);            
      }
    httpRequest.send(JSON.stringify(payloads));

    httpRequest.onreadystatechange = function () {
      if (httpRequest.readyState == 4) {
        if (httpRequest.status == 200) { //이건 클라이언트꺼 서버것 아님
          var res = httpRequest.responseText;
          var res = JSON.parse(res);
          resolve(res);
        }
        else {
          console.error('server has errors.');
          reject();
        }
      }
    };
  });
}

function reqAns(query) {
  var httpRequest;
  if (window.XMLHttpRequest) httpRequest = new XMLHttpRequest();
  else if (window.ActiveXObject) httpRequest = new ActiveXObject("Microsoft.XMLHTTP");
  var url = window.location.origin;
  url += '/query';
  var headers = {  //key 요구가 없네...
    // 'Accept': 'application/json'
  };
  var payloads = {
    'query': query,
  }
  
  return new Promise((resolve, reject) => {
    httpRequest.open('POST', url, true);
    for (key in headers){
        httpRequest.setRequestHeader(key, headers[key]);            
      }
    httpRequest.send(JSON.stringify(payloads));

    httpRequest.onreadystatechange = function () {
      if (httpRequest.readyState == 4) {
        if (httpRequest.status == 200) { //이건 클라이언트꺼 서버것 아님
          var res = httpRequest.responseText;
          var res = JSON.parse(res);
          resolve(res);
        }
        else {
          console.error('server has errors.');
          reject();
        }
      }
    };
  });
}

function reqAnsNER(query) {
  var httpRequest;
  if (window.XMLHttpRequest) httpRequest = new XMLHttpRequest();
  else if (window.ActiveXObject) httpRequest = new ActiveXObject("Microsoft.XMLHTTP");
  var url = window.location.origin;
  url += '/api/ner';
  var headers = {  //key 요구가 없네...
    // 'Accept': 'application/json'
  };
  var payloads = {
    'query': query,
  }
  
  return new Promise((resolve, reject) => {
    httpRequest.open('POST', url, true);
    for (key in headers){
        httpRequest.setRequestHeader(key, headers[key]);            
      }
    httpRequest.send(JSON.stringify(payloads));

    httpRequest.onreadystatechange = function () {
      if (httpRequest.readyState == 4) {
        if (httpRequest.status == 200) { //이건 클라이언트꺼 서버것 아님
          var res = httpRequest.responseText;
          var res = JSON.parse(res);
          resolve(res);
        }
        else {
          console.error('server has errors.');
          reject();
        }
      }
    };
  });
}