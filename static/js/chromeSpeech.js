// 이건 크롬에 내장된건데 지금은 안씀

var recognition;
try{
  recognition = new webkitSpeechRecognition();
}
catch{
  alert('not supported');
}

var isRecognizing = false;
var ignoreOnend = false;
var finalTranscript = '';
recognition.continuous = true;
recognition.interimResults = true;

var resNode = document.getElementById('result'); 
function start(event) {
    resNode.innerHTML = 'started';
    if (isRecognizing) {
      recognition.stop();
      return;
    }
    recognition.lang = 'ko-KR';
    recognition.start();
    ignoreOnend = false;

    finalTranscript = '';
  }

recognition.onstart = function() {
    console.log('onstart', arguments);
    isRecognizing = true;

  };

  recognition.onend = function() {
    console.log('onend', arguments);
    isRecognizing = false;

    if (ignoreOnend) {
      return false;
    }

    // DO end process
    if (!finalTranscript) {
      console.log('empty finalTranscript');
      return false;
    }
  };

  recognition.onresult = function(event) {
    console.log('onresult', event);

    var interimTranscript = '';
    if (typeof(event.results) == 'undefined') {
      recognition.onend = null;
      recognition.stop();
      return;
    }

    for (var i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript;
      } else {
        interimTranscript += event.results[i][0].transcript;
      }
    }

    finalTranscript = capitalize(finalTranscript);
    resNode.innerHTML = interimTranscript    
    console.log('finalTranscript', finalTranscript);
    console.log('interimTranscript', interimTranscript);
  };

  var first_char = /\S/;
  
  function capitalize(s) {
    return s.replace(first_char, function(m) {
      return m.toUpperCase();
    });
  }