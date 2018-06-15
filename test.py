from NER_model import *

query = "아이유 직업 뭐야?"
# query = "이승철은 뭐하는 사람이야?"
# query = "융합대학원의 위치는 어디야?"
# query = "소녀시대의 멤버 알려줘"
# query = "아이유는 몇살이야?"
# query = "백다방 아메리카노 얼마지?"

ext = predict(sess, query)
print(ext)

answers = get_answer(ext)
print(answers)