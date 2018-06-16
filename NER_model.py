import numpy as np
import pandas as pd
import re
# for word counter in vocabulary dictionary
from collections import Counter
from tqdm import tqdm

# for tensorflow
import tensorflow as tf
from tensorflow.python.ops import rnn
from tensorflow.contrib.layers.python.layers import linear
from tensorflow.python.ops import variable_scope
from tensorflow.contrib.seq2seq import sequence_loss

# for preprocessing
def build_vocab(sentences, is_char=False):
    # for word embedding
    if not is_char:
        temp= []
        for s in sentences:
            temp.extend(s)
#             temp.extend(tokenizer(s))
        sentences = temp
    else:
        temp = ' '.join(sentences)
        sentences = temp
#     print(sentences)
        
    cc = Counter()
    cc.update(sentences)

    vocab = dict()
    reverse_vocab = dict()
    vocab_idx = 3 # for '<GO>', '<PAD>', '<UNK>'

    # for vocab
    for key, value in tqdm(list(cc.most_common())):
        for i in range(3):
            vocab[['<GO>', '<PAD>', '<UNK>'][i]] = i
            reverse_vocab[i] = ['<GO>', '<PAD>', '<UNK>'][i]
        vocab[key] = vocab_idx
        reverse_vocab[vocab_idx] = key
        vocab_idx += 1
        
    assert len(vocab) == len(reverse_vocab)
    print("vocab length is:", len(vocab))
    return vocab, reverse_vocab, len(vocab)

def idx2token(idx, reverse_vocab):
    return reverse_vocab[idx]

def token2idx(word, vocab):
    try: return vocab[word]
    except: return vocab['<UNK>']

# ------------
# for tensorflow

# hyperparameter setting class
class HParams:
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            self.__dict__[k] = v
            print(k ,v)
            
    def update(self, **kwargs):
        for k,v in kwargs.items():
            self.__dict__[k] = v
            print(k ,v)

# NER Model
class NER():
    def __init__(self, hps):
        self.hps = hps
        self.x = tf.placeholder(tf.int32,   [None, hps.num_steps], name="pl_tokens")
        self.y = tf.placeholder(tf.int32,   [None, hps.num_steps], name="pl_target")
        self.w = tf.placeholder(tf.int32, [None,], name="pl_weight")
        self.keep_prob = tf.placeholder(tf.float32, [], name="pl_keep_prob")

        ### 4 blocks ###
        # 1) embedding
        # 2) dropout on input embedding
        # 3) sentence encoding using rnn
        # 4) bidirectional rnn's output to target classes
        # 5) loss calcaulation

    def _embedding(self, x):
        # character embedding 
        shape       = [self.hps.vocab_size, self.hps.emb_size]
        initializer = tf.initializers.variance_scaling(distribution="uniform", dtype=tf.float32)
        emb_mat     = tf.get_variable("emb", shape, initializer=initializer, dtype=tf.float32)
        input_emb   = tf.nn.embedding_lookup(emb_mat, x)   # [batch_size, sent_len, emb_dim]

        # split input_emb -> num_steps
        step_inputs = tf.unstack(input_emb, axis=1)
        return step_inputs

    def _sequence_dropout(self, step_inputs, keep_prob):
        # apply dropout to each input
        # input : a list of input tensor which shape is [None, input_dim]
        with tf.name_scope('sequence_dropout') as scope:
            step_outputs = []
            for t, input in enumerate(step_inputs):
                step_outputs.append( tf.nn.dropout(input, keep_prob) )
        return step_outputs

    def sequence_encoding_n2n(self, step_inputs, seq_length, cell_size):
        # birnn based N2N encoding and output
        f_rnn_cell = tf.contrib.rnn.GRUCell(cell_size, reuse=False)
        b_rnn_cell = tf.contrib.rnn.GRUCell(cell_size, reuse=False)
        _inputs    = tf.stack(step_inputs, axis=1)

        # step_inputs = a list of [batch_size, emb_dim]
        # input = [batch_size, num_step, emb_dim]
        # np.stack( [a,b,c,] )
        outputs, states, = tf.nn.bidirectional_dynamic_rnn( f_rnn_cell,
                                                            b_rnn_cell,
                                                            _inputs,
                                                            sequence_length=tf.cast(seq_length, tf.int64),
                                                            time_major=False,
                                                            dtype=tf.float32,
                                                            scope='birnn',
                                                        )
        output_fw, output_bw = outputs
        states_fw, states_bw = states 

        output       = tf.concat([output_fw, output_bw], 2)
        # [batch_size, max_time, output_size] -> [max_time, batch_size, output_size]
        step_outputs = tf.unstack(output, axis=1)

        final_state  = tf.concat([states_fw, states_bw], 1)
        return step_outputs # a list of [batch_size, enc_dim]

    def _to_class_n2n(self, step_inputs, num_class):
        T = len(step_inputs)
        step_output_logits = []
        for t in range(T):
            # encoder to linear(map)
            out = step_inputs[t]
            if t==0: out = linear(out, num_class, scope="Rnn2Target")
            else:    out = linear(out, num_class, scope="Rnn2Target", reuse=True)
            step_output_logits.append(out)
        return step_output_logits

    def _loss(self, step_outputs, step_refs, weights):
        # step_outputs : a list of [batch_size, num_class] float32 - unscaled logits
        # step_refs    : [batch_size, num_steps] int32
        # weights      : [batch_size, num_steps] float32
        # calculate sequence wise loss function using cross-entropy
        _batch_output_logits = tf.stack(step_outputs, axis=1)
        masks = tf.sequence_mask(weights, self.hps.num_steps, dtype=tf.float32, name='weight')
        loss = sequence_loss(
                                logits=_batch_output_logits,        
                                targets=step_refs,
                                weights=masks
                            )
        return loss
#         seq_length    = tf.reduce_sum(self.w, 1) # [batch_size]

    def build_model(self, mode="train"):
        seq_length = self.w

        step_inputs       = self._embedding(self.x)
        step_inputs       = self._sequence_dropout(step_inputs, self.keep_prob)
        step_enc_outputs  = self.sequence_encoding_n2n(step_inputs, seq_length, self.hps.enc_dim)
        step_outputs      = self._to_class_n2n(step_enc_outputs, self.hps.num_target_class)

        self.loss = self._loss(step_outputs, self.y, self.w)

        # step_preds and step_out_probs
        step_out_probs = []
        step_out_preds = []
        for _output in step_outputs:
            _out_probs  = tf.nn.softmax(_output)
            _out_pred   = tf.argmax(_out_probs, 1)

            step_out_probs.append(_out_probs)
            step_out_preds.append(_out_pred)

        # stack for interface
        self.step_out_probs = tf.stack(step_out_probs, axis=1, name="step_out_probs")
        self.step_out_preds = tf.stack(step_out_preds, axis=1, name="step_out_preds")

        self.global_step = tf.get_variable("global_step", [], tf.int32, initializer=tf.zeros_initializer, trainable=False)

        if mode == "train":
            optimizer       = tf.train.AdamOptimizer(self.hps.learning_rate)
            self.train_op   = optimizer.minimize(self.loss, global_step=self.global_step)
        else:
            self.train_op = tf.no_op()
        
#         optimizer       = tf.train.AdamOptimizer(self.hps.learning_rate)
#         self.train_op   = optimizer.minimize(self.loss, global_step=self.global_step)
            
        for v in tf.trainable_variables(): print(v.name)


    @staticmethod
    def get_default_hparams():
        return HParams(
            learning_rate     = 0.001,
            keep_prob         = 0.5,
        )
    
    def make_saver(self):
        # Create a saver.
        name_to_var_map = {var.op.name: var for var in tf.global_variables()}
        self.saver = tf.train.Saver(name_to_var_map, name='my_saver')

# inference
def predict(sess, query):
    """
    O -> B,O // 0 - 0,1,3,5
    B -> I,O // 1- 0,2,3,5 // 3-0,1,4,5 // 5-0,1,3,6
    I -> 0,자기자신, 다른 B // 2-0,2,3,5 // 4-0,4,1,5 // 6-0,6,1,3
    """
    r = [token2idx(c, all_vocab)for c in list(query)]
    r = r[:max_enc_len]
    BIO_reverse = {0:'O', 1:'B-subj', 2:'I-subj', 3:'B-pred', 4:'I-pred', 5:'B-q', 6:'I-q'}
    # BIO = {'O':0, 'B-subj':1, 'I-subj':2, 'B-pred':3, 'I-pred':4, 'B-q':5, 'I-q':6}

    # ex) r = [158, 67, 31, 2, 357, 311, 61, 64, 2, 341, 84, 64, 105, 2, 305, 48]
    ww = len(r)
    r = r+[0]*(max_enc_len-len(r))

    # print('query2token: \n',r)

    # get predict
    res = sess.run(model.step_out_probs, feed_dict={
        model.x: [r],
        model.w: [ww],
        model.keep_prob: 1,
    })
    # bio constraint
    pre_bio = 0 # default = Out
    pred = []
    for i in res[0]:
        # O-tag
        if pre_bio == 0:
            for idx in [2,4,6]: i[idx] = 0
        # B-tag
        if pre_bio == 1:
            for idx in [1,4,6]: i[idx] = 0
        if pre_bio == 3:
            for idx in [2,3,6]: i[idx] = 0
        if pre_bio == 5:
            for idx in [2,4,5]: i[idx] = 0
        # I-tag
        if pre_bio == 2:
            for idx in [1,4,6]: i[idx] = 0
        if pre_bio == 4:
            for idx in [2,3,6]: i[idx] = 0
        if pre_bio == 6:
            for idx in [2,4,5]: i[idx] = 0
        curr_bio = np.argmax(i, 0)
        pre_bio = curr_bio
        pred.append(curr_bio)
    
    #  return pred
    pred_res = [(query[i], BIO_reverse[el]) for i,el in enumerate(pred[:len(query)])]
    # print(pred_res)
    
    # extract bio word - {'pred': '멤버', 'q': '누구', 'subj': '소녀시대'}
    bio = str()
    ext = {
        'subj':'',
        'pred':'',
        'q':''
    }
    for w,b in pred_res:
        if b[0] in ['B', 'I']:
            bio = b[2:]
            ext[bio] += w
    # trim/strip
    for i in ext: ext[i] = ext[i].strip()
    return ext


"""
==================================
set default parameters/variables
==================================
"""

# loads KB
df = pd.read_csv('qa.csv')
# build vocab
all_vocab, all_reverse_vocab, all_vocab_size = build_vocab(
    df['question']+df['answer'], is_char=True)

BIO = {'O':0, 'B-subj':1, 'I-subj':2, 'B-pred':3, 'I-pred':4, 'B-q':5, 'I-q':6}
max_enc_len = 48

# model restore
tf.reset_default_graph()
sess = tf.Session()

ckpt_path = './NER_model/NER'
hps = NER.get_default_hparams()
hps.update(
                batch_size= 100,
                num_steps = max_enc_len,
                emb_size  = 50,
                enc_dim   = 100,
                vocab_size= all_vocab_size,
                num_target_class=len(BIO)
           )
model = NER(hps)

model.build_model("infer")
model.make_saver()
model.saver.restore(sess, ckpt_path+'-1001')

def get_answer(ext):
    # get answer from KB
    idx_candi = []
    obj_candi = []
    answers = []
    for i,e in enumerate(df['subj']):
        if e == ext['subj']: idx_candi.append(i)
        
    # print(idx_candi)

    for i in idx_candi:
        if df['pred'][i] == ext['pred']:
            # print(df['obj'][i] ,i)
            # print(df['answer'][i])
            # answers.append(df['answer'][i])

            # 답변 여러개짜리 합치기
            obj_candi.append(df['obj'][i])

    if obj_candi:
        reg = re.compile('\(.*\)') # 괄호 없애기
        objs = [reg.sub('', i).strip() for i in obj_candi]
        objs = ', '.join(objs)
        answer = '지식베이스에서 발췌한 답변입니다. {}의 {}(은)는 {}입니다.'.format(ext['subj'], ext['pred'], objs)
        answers.append(replace_josa(answer))
    
    return answers

#====================== 조사 선택위해서 임포트
JOSA_PAIRD = {
    u"(이)가" : (u"이", u"가"),
    u"(와)과" : (u"과", u"와"),
    u"(을)를" : (u"을", u"를"),
    u"(은)는" : (u"은", u"는"),
    u"(으)로" : (u"으로", u"로"),
    u"(이)야" : (u"이", u"야"),
    u"(이)여" : (u"이여", u"여"),
    u"(이)라" : (u"이라", u"라"),
}

JOSA_REGEX = re.compile(u"\(이\)가|\(와\)과|\(을\)를|\(은\)는|\(이\)야|\(이\)여|\(으\)로|\(이\)라")


def choose_josa(prev_char, josa_key, josa_pair):
    """
    조사 선택
    :param prev_char 앞 글자
    :param josa_key 조사 키
    :param josas 조사 리스트
    """
    char_code = ord(prev_char)

    # 한글 코드 영역(가 ~ 힣) 아닌 경우 
    if char_code < 0xac00 or char_code > 0xD7A3: 
        return josa_pair[1]

    local_code = char_code - 0xac00 # '가' 이후 로컬 코드
    jong_code = local_code % 28

    # 종성이 없는 경우
    if jong_code == 0: 
        return josa_pair[1]
        
    # 종성이 있는 경우
    if josa_key == u"(으)로":
        if jong_code == 8: # ㄹ 종성인 경우
            return josa_pair[1]

    return josa_pair[0]

def replace_josa(src):
    tokens = []
    base_index = 0
    for mo in JOSA_REGEX.finditer(src):
        prev_token = src[base_index:mo.start()]
        prev_char = prev_token[-1]
        tokens.append(prev_token)

        josa_key = mo.group()
        tokens.append(choose_josa(prev_char, josa_key, JOSA_PAIRD[josa_key]))

        base_index = mo.end()

    tokens.append(src[base_index:])
    return ''.join(tokens)