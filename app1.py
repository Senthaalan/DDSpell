# _*_ encoding: utf-8 _*_
from flask import Flask, jsonify, request
from flask_cors import CORS
from pyjarowinkler import distance
import nltk
import re
import json
from nltk.util import ngrams
import tamil
import collections
import codecs
import os
import sys
# from flask_caching import Cache

app = Flask(__name__)

CORS(app)

with open('./data/dictionary_ta_pr_val.txt') as json_file_ta:
    hashtable_ta = json.load(json_file_ta)
json_file_ta.close()

with open('./data/dictionary_si.txt') as json_file_si:
    hashtable_si = json.load(json_file_si)
json_file_si.close()

with open('./data/lan_spl_letters.txt') as json_lan:
    lan_spl_letter = json.load(json_lan)
json_lan.close()

inp_file = open("all-tamil-nouns.txt", "r", encoding = 'UTF-8')
_DEBUG=False


checkLettersTamil = lan_spl_letter[0]
checkLettersSinhala = lan_spl_letter[3]
read_file = inp_file.read()
noun_list = nltk.word_tokenize(read_file)

@app.route('/api/checking', methods=['POST'])
def check_spell():
    text = request.get_json()['text']
    resultList = []
    originalPara = nltk.word_tokenize(text)
    words = clean_text2(text)
    cantiResult = []
    cantiMistake = []
    cantiCorrection = []

    for inpText in words:
        if find_language(inpText) == 'tamil':
            accKey = getAccKey(inpText, 0, checkLettersTamil, 'tamil')
            #suggest = suggest_list---------------------------
            if accKey in hashtable_ta:
                thisKeyList = [e['word'] for e in hashtable_ta[accKey]]
                if inpText in thisKeyList:
                    if words.index(inpText) != len(words)-1:
                        results = canti_check(inpText+" " + words[words.index(inpText)+1])
                        if results[0]!=inpText:
                            cantiMistake.append(inpText)
                            cantiCorrection.append(results[0])
                else:
                    resultList.append(inpText)
            else:
                resultList.append(inpText)
        elif find_language(inpText) == 'sinhala':
            accKey = getAccKey(inpText, 0, checkLettersSinhala, 'sinhala')
            if accKey in hashtable_si:
                thisKeyList = [e['word'] for e in hashtable_si[accKey]]
                if inpText in thisKeyList:
                    pass
                else:
                    resultList.append(inpText)
            else:
                resultList.append(inpText)
        else:
            pass
    cantiResult.append(cantiMistake)
    cantiResult.append(cantiCorrection)
    return jsonify({
        'resultList': resultList,
        'wordList': originalPara,
        'cantiResult': cantiResult
    })


@app.route('/api/suggestion', methods=['GET'])
def getSuggestion():
    sugg_final = []
    wordReq = request.args['word']
    suggest = []
    suggestFreq = []
    lis = []
    lisFreq = []
    key_list = []


    # if to check for key-----------------------------------
    if find_language(wordReq) == 'tamil':
        for x in range(-2, 3):
            inp_key = getAccKey(wordReq, x, checkLettersTamil, 'tamil')
            key_list.append(inp_key)
        for key in key_list:
            if key in hashtable_ta:
                thisKeyList = [e['word'] for e in hashtable_ta[key]]
                thisKeyListFreq = [f['freq'] for f in hashtable_ta[key]]
                for word in thisKeyList:
                    lis.append(word)
                    lisFreq.append(float(thisKeyListFreq[thisKeyList.index(word)]))
    elif find_language(wordReq) == 'sinhala':
        for x in range(-2, 3):
            inp_key = getAccKey(wordReq, x, checkLettersTamil, 'sinhala')
            key_list.append(inp_key)
        for key in key_list:
            if key in hashtable_si:
                thisKeyList = [e['word'] for e in hashtable_si[key]]
                thisKeyListFreq = [f['freq'] for f in hashtable_si[key]]
                for word in thisKeyList:
                    lis.append(word)
                    lisFreq.append(int(thisKeyListFreq[thisKeyList.index(word)]))
    else:
        pass

    for word in lis:
        ed = nltk.edit_distance(wordReq, word)
        if (ed <= 2):
            suggest.append(word)
            suggestFreq.append(lisFreq[lis.index(word)])
            ng_list = list(ngrams(wordReq, 2))

    sugg_dic = []

    for word in suggest:
        l = list(ngrams(word, 2))
        lis = set(l + ng_list)
        val = len(list(set(ng_list) & set(l)))
        value = val / (len(lis))
        sugg_dic.append((word, value, value * (suggestFreq[suggest.index(word)])))
    sugg_dic.sort(key=takeSecond)
    sorted_x = sugg_dic[-10:]
    sorted_x.sort(key=takeThird, reverse = True)
    for sugg in sorted_x:
        sugg_final.append(sugg[0])

    return jsonify({'suggestion': sugg_final})


def clean_text2(text):
    t1 = re.sub(r"[!@#$%^&*()-_=+{}\|:;?/.>,<''`~]", " ", text)
    t1 = t1.replace('"', ' ')
    words = nltk.word_tokenize(t1)
    wordList = list(words)
    return wordList
	
def takeSecond(elem):
    # take second element for sort
    return elem[1]


def takeThird(elem):
    # take third element for sort
    return elem[2]


def getAccKey(inpText, x, letterSet, language):
    if len(inpText) != 1:
        if language == 'sinhala' and len(inpText) >= 3 and inpText[2] == '\u200d':
            accKey = inpText[:4] + str(len(inpText) + x)
        elif inpText[1] in letterSet:
            accKey = inpText[:2] + str(len(inpText) + x)
        else:
            accKey = inpText[0] + str(len(inpText)+ x)
    else:
        accKey = inpText[0] + str(len(inpText)+ x)
    return accKey


def find_language(word):
    if 3071 >= ord(word[0]) >= 2944:
        return 'tamil'
    elif 3583 >= ord(word[0]) >= 3456:
        return 'sinhala'
    else:
        return 'noLang'


def canti__check(word, nextWord):
    cantiResult = []
    possible_consonant = lan_spl_letter[1]
    possible_chr = lan_spl_letter[2]
    if find_language(word) == 'tamil':
        if (word[-2:]) in possible_consonant:
            if word[-2] == nextWord[0]:
                pass
            elif nextWord[0] in possible_chr:
                cantiResult = [word, word[:-2] + nextWord[0] + "்"]
            else:
                cantiResult = [word, word[:-2]]
        else:
            pass
    return cantiResult
	
mei_letters = tamil.utf8.mei_letters
uyir_letters = tamil.utf8.uyir_letters
ayudha_letter = ['ஃ']
kuril_letters = tamil.utf8.kuril_letters
nedil_letters = tamil.utf8.nedil_letters
agaram_letters = tamil.utf8.agaram_letters
uyirmei_letters = tamil.utf8.uyirmei_letters
vallinam_letters = tamil.utf8.vallinam_letters
mellinam_letters = tamil.utf8.mellinam_letters
special_chars=[u'.',u';',u',',u':',u'?']
canti_letters = [u'க்',u'ப்',u'ச்',u'த்']
one_letter_words=[u'கை',u'தீ',u'தை',u'பூ',u'மை']
suttu_vina=[u'அ',u'ஆ',u'இ',u'ஈ',u'எ',u'யா']
numerals=[u'ஒன்று',u'இரண்டு',u'மூன்று',u'நான்கு',u'ஐந்து',u'ஆறு',u'நூறு',u'ஏழு',u'ஒன்பது',u'ஒரு',u'இரு',u'அறு',u'எழு']
viyankol=[u'கற்க',u'நில்',u'கவனி',u'செல்',u'செல்க',u'மன்னிய',u'வெல்க',u'செப்பும்',u'வினாவும்',u'வாழ்க',u'ஓம்பல்',u'அஞ்சாமை',u'வாழி',u'வீழ்க',u'ஒழிக',u'வருக',u'உண்க',u'அருள்க',u'கருணைபுரிக',u'வருக',u'வாழிய',
u'வாழியர்',u'வாரற்க',u'கூறற்க',u'செல்லற்க',u'வாரல்',u'செல்லல்',u'பகரேல்']
tamil_letters = tamil.utf8.tamil_letters
sanskrit_letters = tamil.utf8.sanskrit_letters 
sanskrit_mei_letters = tamil.utf8.sanskrit_mei_letters 
special_chars=[u'.',u'\'',u';',u',',u':',u'?',u'(',u')',u'_',u'-',u'"',u'%',u'±',u'#',u'@',u'!',u'!',u'$',u'%',u'^',u'&',u'*',u'+',u'/',u'–',u'\\',u'>',u'<',u'|',u'}',u'{',u']',u'[']
one_letter_words=[u'கை',u'த',u'தை',u'பூ',u'மை']
numbers=[u'0',u'1',u'2',u'3',u'4',u'5',u'6',u'7',u'8',u'9',u'½']
granda = [u"ஜ்",u"ஷ்", u"ஸ்",u"ஹ்"
,u"ஶ", 	u"ஶா", 	u"ஶி", 	u"ஶீ", u"ஶு", u"ஶூ", u"ஶெ", u"ஶே", u"ஶை", u"ஶொ", u"ஶோ", u"ஶௌ"
,u"ஜ"  ,u"ஜா"  ,u"ஜி"  ,u"ஜீ"  ,u"ஜு"  ,u"ஜூ"  ,u"ஜெ"  ,u"ஜே"  ,u"ஜை"  ,u"ஜொ"  ,u"ஜோ"  ,u"ஜௌ"
,u"ஷ"  ,u"ஷா"  ,u"ஷி"  ,u"ஷீ"  ,u"ஷு"  ,u"ஷூ"  ,u"ஷெ"  ,u"ஷே"  ,u"ஷை"  ,u"ஷொ"  ,u"ஷோ"  ,u"ஷௌ"
,u"ஸ"  ,u"ஸா"  ,u"ஸி"  ,u"ஸீ"  ,u"ஸு"  ,u"ஸூ"  ,u"ஸெ"  ,u"ஸே"  ,u"ஸை"  ,u"ஸொ"  ,u"ஸோ"  ,u"ஸௌ"
,u"ஹ"  ,u"ஹா"  ,u"ஹி"  ,u"ஹீ"  ,u"ஹு"  ,u"ஹூ"  ,u"ஹெ"  ,u"ஹே"  ,u"ஹை"  ,u"ஹொ"  ,u"ஹோ"  ,u"ஹௌ"
,u"க்ஷ" ,u"க்ஷா" ,u"க்ஷி" ,u"க்ஷீ" ,u"க்ஷு" ,u"க்ஷூ" ,u"க்ஷெ" ,u"க்ஷே" ,u"க்ஷை" ,u"க்ஷொ" ,u"க்ஷோ" ,u"க்ஷௌ" ]
english = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
assert( len(english) == 52 )
suttu_vina_not=[u'அ',u'இ',u'எ',u'யா',u'அந்த',u'இந்த',u'எந்த',u'அங்கு',u'இங்கு',u'எங்கு',u'ஆங்கு',u'ஈங்கு',u'யாங்கு',u'அப்படி',u'இப்படி',u'எப்படி',u'ஆண்டு',u'ஈண்டு',u'யாண்டு',u'அவ்வகை',u'இவ்வகை',u'எவ்வகை',u'அத்துணை',u'இத்துணை']
specific_words=[u'அது',u'இது',u'எது',u'யாது',u'அவை',u'இவை',u'எவை',u'அன்று',u'இன்று',u'என்று',u'அத்தனை',u'இத்தனை',u'எத்தனை',u'அவ்வளவு',u'இவ்வளவு',u'எவ்வளவு',u'அவ்வாறு',u'இவ்வாறு',u'எவ்வாறு',u'ஒன்று',u'இரண்டு',u'மூன்று',u'நான்கு',u'ஐந்து',u'ஆறு',u'நூறு',u'ஏழு',u'ஒன்பது',u'ஒரு',u'இரு',u'அறு',u'எழு',u'கற்க',u'நில்',u'கவனி',u'செல்',u'செல்க',u'மன்னிய',u'வெல்க',u'செப்பும்',u'வினாவும்',u'வாழ்க',u'ஓம்பல்',u'அஞ்சாமை',u'வாழி',u'வீழ்க',u'ஒழிக',u'வருக',u'உண்க',u'அருள்க',u'கருணைபுரிக',u'வருக',u'வாழிய',u'வாழியர்',u'வாரற்க',u'கூறற்க',u'செல்லற்க',u'வாரல்',u'செல்லல்',u'பகரேல்',u'கல', 'பல',u'சில',u'வா',u'எழு',u'போ',u'பார்', u'பிறகு', u'மற்ற']


	
def safe_splitMeiUyir(arg):
    try:
        # when uyir letters are passed to splitMeiUyir function it will throw an IndexError
        rval = tamil.utf8.splitMeiUyir(arg)
        if not isinstance(rval,tuple):
            if rval in uyir_letters:
                return (u'',rval)
            return (rval,u'')
        return rval
    except IndexError as idxerr:
        pass
    except ValueError as valerr:
        # non tamil letters cannot be split - e.g. '26வது'
        pass
    # could be english string etc. multiple-letter (word-like) input etc
    return (u'',u'')

class Results:
    # class contains results of 'canti_check' method
    ErrorLog = collections.namedtuple('ErrorLog',['rule','description','word']) #description of error
    def __init__(self):
        self.errors = [] #list of ErrorLog object

    def add(self,word,rule,descr):
        elog = Results.ErrorLog( rule, descr, word )
        self.errors.append(elog)

    @property
    def counter(self):
        return len(self.errors)

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        summary_list = [u"%s -> (%s, %s),\n"%(err.word,err.rule,err.description) for err in self.errors]
        return u"".join(summary_list)

def canti_check(words):
    if not isinstance(words,list):
        words = tamil.utf8.get_words(words)

    result = Results()
    fixed_list=[]
    prev_word_stack = [u'']

    for counter,word in enumerate(words):
        prev_word = prev_word_stack.pop()
        prev_word_stack.append(word)
        next_word = (counter+1) < len(words) and words[counter+1] or u' '
        
        next_letters = tamil.utf8.get_letters(next_word)
        if((safe_splitMeiUyir(next_letters[0])[0]) in canti_letters):
            letters = tamil.utf8.get_letters(word)
            # வல்லினம் மிகா இடங்கள்
            if tamil.utf8.get_letters(word)[-1] in special_chars:
                fixed_list.append(word)
                if _DEBUG: 
                    print(u"மிகா - விதி 1 - " + word)
                result.add(word,u'விதி 1',u'மிகா')
                continue

            # வல்லினம் மிகா சுட்டு, வினா அடியாகத் தோன்றிய சொற்கள் - எத்தனை பழங்கள்?
            # ‘அஃறிணைப் பன்மை’ - பல பசு
            if word in specific_words:
                fixed_list.append(word)
                if _DEBUG: 
                    print(u"மிகா - விதி 2 - " + word)
                result.add(word,u'விதி 2',u'மிகா')
                continue

            # வல்லினம் மிகா வந்த, கண்ட, சொன்ன, வரும் என்பன  போன்ற பெயரெச்சங்களோடு படி, ஆறு என்னும் சொற்கள்- கண்டவாறு சொன்னான்
            if (tamil.utf8.get_letters(word)[0]) in [u'வ',u'க',u'சொ']:
                if (tamil.utf8.get_letters(word)[-1]) in [u'டி',u'று']:
                    fixed_list.append(word)
                    if _DEBUG: print(u"மிகா - விதி 3 - " + word)
                    result.add(word,u'விதி 3',u'மிகா')
                    continue

            # வல்லினம் மிகா எண்ணுப்பெயர்கள் - ஐந்து சிறுவர்கள்
            if word in numerals:
                fixed_list.append(word)
                if _DEBUG: print(u"மிகா - விதி 4 - " + word)
                result.add(word,u'விதி 4',u'மிகா')
                continue

            # ஓர் எழுத்துச் சொற்கள் முன் வல்லினம் மிகல்
            # 6.1.2 - கை குழந்தை
            if len(tamil.utf8.get_letters(word)) == 1:
                if  word in one_letter_words:
                    first_char_of_next_word = (next_word[0])
                    mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                    fixed_list.append(word + mei_of_first_char_of_next_word)
                    if _DEBUG: print(u"மிகும் - விதி 1 - " + word + mei_of_first_char_of_next_word)
                    result.add(word,u'விதி 1',u'மிகும்')
                continue

            # வல்லினம் மிகா ஒடு & ஓடு என உயிர் ஈறு கொண்டவை - கத்தியோடு நின்றான்
            if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-2])[1]) in [u'ஒ',u'ஓ']:
                if (tamil.utf8.get_letters(word)[-1]) == u'டு':
                    fixed_list.append(word)
                    if _DEBUG: print(u"மிகா - விதி 5 - " + word)
                    result.add(word,u'விதி 5',u'மிகா')
                    continue

            # வல்லினம் மிகா ‘கொண்டு’ என்னும் சொல்லுருபு -கத்திகொண்டு குத்தினான்
            if u''.join(tamil.utf8.get_letters(word)[-3:]) ==  u'கொண்டு':
                fixed_list.append(word)
                if _DEBUG: print(u"மிகா - விதி 6 - " + word)
                result.add(word,u'விதி 6',u"மிகா")
                continue

            # வல்லினம் மிகா இல் என்பதோடு இருந்து என்னும்  சொல்லுருபு - வீட்டிலிருந்து சென்றான்
            if u''.join(tamil.utf8.get_letters(word)[-4:]) == u'லிருந்து':
                fixed_list.append(word)
                if _DEBUG: print(u"மிகா - விதி 7 - " + word)
                result.add(word,u'விதி 7',u"மிகா")
                continue

            # வல்லினம் மிகா இன் என்பதோடு நின்று என்னும் சொல்லுருபு - வீட்டினின்று வெளியேறினான்
            if u''.join(tamil.utf8.get_letters(word)[-3:]) == u'னின்று':
                fixed_list.append(word)
                if _DEBUG: print(u"மிகா - விதி 8 - " + word)
                result.add(word,u'விதி 8',u"மிகா")
                continue

            # வல்லினம் மிகா ஆறாம் வேற்றுமைக்கு உரிய அது - எனது புத்தகம்
            if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-2])[1]) == u'அ':
                if (tamil.utf8.get_letters(word)[-1]) == u'து':
                    fixed_list.append(word)
                    if _DEBUG: print(u"மிகா - விதி 9 - " + word)
                    result.add(word,u'விதி 9',u'மிகா')
                    continue

            # வல்லினம் மிகா ‘உடைய’ என்னும் சொல்லுருபு- என்னுடைய புத்தகம்
            if u''.join(tamil.utf8.get_letters(word)[-2:]) == u'டைய':
                if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-3])[1]) == u'உ':
                    fixed_list.append(word)
                    if _DEBUG: print(u"மிகா - விதி 10 - " + word)
                    result.add(word,u'விதி 10',u'மிகா')
                    continue
            # வல்லினம் மிகா மென்தொடர்க் குற்றியலுகர  வினையெச்சங்கள் - ண்டு, ந்து, ன்று என முடியும்
            # கண்டு பேசினார்
            if u''.join(tamil.utf8.get_letters(word)[-2:]) == u'ண்டு':
                fixed_list.append(word)
                if _DEBUG: print(u"மிகா - Rule11 - " + word)
                counter = counter+1
                result.add(word,u'விதி 11',u'மிகா')
                continue

            # வல்லினம் மிகா மென்தொடர்க் குற்றியலுகர  வினையெச்சங்கள் - ண்டு, ந்து, ன்று என முடியும் -கண்டு பேசினார்
            # இடைத்தொடர்க் குற்றியலுகர  வினையெச்சங்கள் - ய்து என முடியும் - செய்து தந்தான்
            if ''.join(tamil.utf8.get_letters(word)[-2:]) in [u'ண்டு',u'ந்து',u'ன்று',u'ய்து',u'ன்கு']:     
                fixed_list.append(word)
                if _DEBUG: print(u"மிகா - Rule12 - " + word)
                counter = counter+1
                result.add(word,u'விதி 12',u'மிகா')
                continue

            # கொன்று குவித்தான்
            if u''.join(tamil.utf8.get_letters(word)[-2:]) == u'ன்று':
                fixed_list.append(word)
                if _DEBUG: print(u"மிகா - Rule13 - " + word)
                counter = counter+1
                result.add(word,u'விதி 13',u'மிகா')
                continue

            # வல்லினம் மிகா இடைத்தொடர்க் குற்றியலுகர  வினையெச்சங்கள் - ய்து என முடியும்
            # செய்து தந்தான்
            if u''.join(tamil.utf8.get_letters(word)[-2:]) == u'ய்து':
                fixed_list.append(word)
                if _DEBUG: print(u"மிகா - Rule14 - " + word)
                result.add(word,u'விதி 14',u'மிகா')
                counter = counter+1
                continue

            # வல்லினம் மிகா மற்ற பெயரெச்சங்கள் - ஆத, இய, ஐய,ற்ற,ல்ல, ட்ட கின்ற, உம் ஆகிய விகுதிகள் பெற்று முடியும்
            # அழியாத கல்வி
            if u''.join(tamil.utf8.get_letters(word)[-1:]) == u'த':
                if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-2])[1]) == u'ஆ':
                    fixed_list.append(word)
                    if _DEBUG: print(u"மிகா - Rule15 - " + word)
                    result.add(word,u'விதி 15',u'மிகா')
                    counter = counter+1
                    continue

            # பெரிய பெண்
            if u''.join(tamil.utf8.get_letters(word)[-1:]) == u'ய':
                if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-2])[1]) == u'இ':
                    fixed_list.append(word)
                    if _DEBUG: print(u"மிகா - Rule16 - " + word)
                    counter = counter+1
                    result.add(word,u'விதி 16',u'மிகா')
                    continue

            # இன்றைய செய்தி
            if u''.join(tamil.utf8.get_letters(word)[-1:]) == u'ய':
                if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-2])[1]) == u'ஐ':
                    fixed_list.append(word)
                    if _DEBUG: print(u"மிகா - Rule17 - " + word)
                    result.add(word,u'விதி 17',u'மிகா')
                    counter = counter+1
                    continue

            #CHANGES REMOVED THIS
            # கற்ற சிறுவன் 
            if ''.join(tamil.utf8.get_letters(word)[-2:]) in [u'ற்ற',u'ல்ல',u'ட்ட',u'ன்ற',u'ந்த',u'த்து',u'இனி']:
                print(25)
                fixed_list.append(word)
                if _DEBUG: print(u"மிகா - Rule18 - " + word)
                result.add(word,u'விதி 18',u'மிகா')
                continue

            # வல்லினம் மிகா மற்ற வினையெச்சங்கள் - ஆக, அன, யுற,றகு,க்கு ஆகிய  விகுதிகள் பெற்று முடியும்  
            # அழியாத கல்வி 
            if len(tamil.utf8.get_letters(word)) > 1:  
                if ''.join(tamil.utf8.get_letters(word)[-1:]) == u'க':
                    if ''.join(tamil.utf8.get_letters(word)[-2]) not in (uyir_letters + numbers + ayudha_letter + granda + special_chars + english):             
                        if (tamil.utf8.splitMeiUyir(tamil.utf8.get_letters(word)[-2])[1]) == u'ஆ':
                            fixed_list.append(word)
                            if _DEBUG: print(u"மிகா - Rule19 - " + word)
                            result.add(word,u'விதி 19',u'மிகா')
                            continue
            if len(tamil.utf8.get_letters(word)) > 1:  
                if ''.join(tamil.utf8.get_letters(word)[-1]) == u'ன':  
                    if ''.join(tamil.utf8.get_letters(word)[-2]) not in (uyir_letters + numbers + ayudha_letter + granda + special_chars + english):               
                        if (tamil.utf8.splitMeiUyir(tamil.utf8.get_letters(word)[-2])[1]) == u'அ':
                            fixed_list.append(word)
                            if _DEBUG: print(u"மிகா - Rule20 - " + word)
                            result.add(word,u'விதி 20',u'மிகா')
                            continue

            if ''.join(tamil.utf8.get_letters(word)[-2:]) in [u'யுற',u'போது']:
                fixed_list.append(word)
                if _DEBUG: print(u"மிகா - Rule21 - " + word)
                result.add(word,u'விதி 21',u'மிகா')
                continue

            # வல்லினம் மிகா இரட்டைக் கிளவி, அடுக்குத்தொடர்கள் - கல கல
            if word == next_word:
                fixed_list.append(word)
                if _DEBUG: print(u"மிகா - Rule22 - " + word)
                result.add(word,u'விதி 22',u'மிகா')
                continue

            # வல்லினம் மிகா வியங்கோள் வினைமுற்று - வருக புலவரே
            if word in viyankol:
                fixed_list.append(word)
                if _DEBUG: print(u"மிகா - Rule23 - " + word)
                result.add(word,u'விதி 23',u'மிகா')
                continue

      #REMOVED      
            # வல்லினம் மிகா பொதுப்பெயர்கள் - மகளிர் கல்லூரி 
           # if word in noun_list :
           #     fixed_list.append(word)
           #     if _DEBUG: print(u"மிகா - Rule24 - " + word)
           #     result.add(word,u'விதி 24',u'மிகா')
           #     continue 

            # 6.1.1 சுட்டு, வினா அடியாகத் தோன்றிய சொற்கள் முன் வல்லினம் மிகல் - அந்த பையன்          
             # வல்லினம் மிகா கள், தல் விகுதிகள் - வாக்கு கள்
            if next_word in ['கள்','தல்']:
                fixed_list.append(word)
                if _DEBUG: print(u"மிகா - Rule25 - " + word)
                counter = counter+1
                continue

            # வல்லினம் மிகா பல, சில, ஏவல் வினை - வா கலையரசி
            if word in [u'கல',u'பல',u'சில',u'வா',u'எழு',u'போ',u'பார்'] :
                fixed_list.append(word)
                if _DEBUG: print(u"மிகா - Rule26 - " + word)
                counter = counter+1
                result.add(word,u'விதி 26',u'மிகா')
                continue

       #REMOVED     
            # வல்லினம் மிகா பொதுப்பெயர்கள்,உயர்திணைப் பெயர்கள்,வடமொழி சொற்கள்  - மகளிர் கல்லூரி
           # if word in noun_list :
           #     fixed_list.append(word)
           #     if _DEBUG: print(u"மிகா - விதி 28 - " + word)
           #     counter = counter+1
           #     result.add(word,u'விதி 28',u'மிகா')
           #     continue

            # 6.1.1 சுட்டு, வினா அடியாகத் தோன்றிய சொற்கள் முன் வல்லினம் மிகல் - அந்த பையன்
            print(tamil.utf8.get_letters(word))
            if (tamil.utf8.get_letters(word)) in suttu_vina:
                if (tamil.utf8.get_letters(word)[-1]) not in mei_letters:
                    if ''.join(tamil.utf8.get_letters(word)[1:3]) == u'வ்வா':
                        fixed_list.append(word)
                        if _DEBUG: print(u"மிகா - Rule25 - " + word)
                        result.add(word,u'விதி 25',u'மிகா')
                        continue  
                    if ''.join(tamil.utf8.get_letters(word)[-2:]) != u'டைய':
                        first_char_of_next_word = (next_word[0])
                        if _DEBUG: print(u"மிகா - Rule29 - " + word)
                        result.add(word,u'விதி 29',u'மிகா')
                        counter = counter+1
                        continue
                    print(u''.join(tamil.utf8.get_letters(word)[-2:]))
                    if u''.join(tamil.utf8.get_letters(word)[-2:]) != u'டைய':
                        first_char_of_next_word = (next_word[0])
                        if first_char_of_next_word not in (uyir_letters + numbers + ayudha_letter + granda + special_chars + english):
                            mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                            if mei_of_first_char_of_next_word in vallinam_letters:
                                fixed_list.append(word + mei_of_first_char_of_next_word)
                                if _DEBUG: print(u"மிகும் - Rule2 - " + word + mei_of_first_char_of_next_word)
                                result.add(word,u'விதி 2',u'மிகும்')
                                continue  

            # 6.1.3 - 1 வன்தொடர்க் குற்றியலுகரம் முன் வல்லினம் மிகல் - கற்று கொடுத்தான் 
            if len(tamil.utf8.get_letters(word)) > 1:        
                if (tamil.utf8.get_letters(word)[-2]) in vallinam_letters:
                    uyir_of_last_char = safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])[1]
                    if uyir_of_last_char == u'உ':                
                        first_char_of_next_word = (next_word[0])
                        if first_char_of_next_word not in (uyir_letters + numbers + ayudha_letter + granda + special_chars + english):
                            mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                            if mei_of_first_char_of_next_word in vallinam_letters:                    
                                fixed_list.append(word + mei_of_first_char_of_next_word)   
                                if _DEBUG: print(u"மிகும் - Rule3 - " + word + mei_of_first_char_of_next_word)
                                result.add(word,u'விதி 3',u'மிகும்')
                                continue

            # வன்தொடர்க் குற்றியலுகரம் முன் வல்லினம் மிகல் - கற்று கொடுத்தான்
            # 6.1.3 - 1

            if (tamil.utf8.get_letters(word)[-2]) in vallinam_letters:
                uyir_of_last_char = safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])[1]
                if uyir_of_last_char == u'உ':
                    first_char_of_next_word = (next_word[0])
                    mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                    fixed_list.append(word + mei_of_first_char_of_next_word)
                    if _DEBUG: print(u"மிகும் - விதி 3 - " + word + mei_of_first_char_of_next_word)
                    result.add(word,u'விதி 3',u'மிகும்')
                    continue

            # மென்தொடர்க் குற்றியலுகரம் முன் வல்லினம் மிகல் - குரங்கு குட்டி
            # 6.1.3 - 2
            if (tamil.utf8.get_letters(word)[-2]) in mellinam_letters:
                uyir_of_last_char = safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])[1]

                if uyir_of_last_char == u'உ':
                    if not ( u''.join(tamil.utf8.get_letters(word)[-3:]).endswith( u'கொண்டு') ):
                        first_char_of_next_word = (next_word[0])
                        mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                        fixed_list.append(word + mei_of_first_char_of_next_word)
                        if _DEBUG: print(u"மிகும் - விதி 4 - " + word + mei_of_first_char_of_next_word)
                        result.add(word,u'விதி 4',u'மிகா')
                        continue

            # முற்றியலுகரச் சொற்கள் முன் வல்லினம் மிகல்
            # 6.1.4 - 1 - தனிக் குறில் அடுத்து வரும் உகரம்  - பொது பணி
            if len(tamil.utf8.get_letters(word)) == 2:
                if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-2])[1]) in kuril_letters:
                    uyir_of_last_char = safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])[1]
                    if uyir_of_last_char == u'உ':
                        first_char_of_next_word = (next_word[0])
                        mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                        fixed_list.append(word + mei_of_first_char_of_next_word)
                        if _DEBUG: print(u"மிகும் - விதி 5 - " + word + mei_of_first_char_of_next_word)
                        result.add(word,u'விதி 5',u'மிகும்')
                        continue

            # உயிர்த்தொடர்க் குற்றியலுகரம் முன் வல்லினம் மிகல் - விறகு கடை
            # 6.1.3 - 3
            print(" kakak")
            if safe_splitMeiUyir(tamil.utf8.get_letters(word)[-2])[1] in uyir_letters:
                uyir_of_last_char = safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])[1]

                if uyir_of_last_char == u'உ':
                    first_char_of_next_word = (next_word[0])
                    mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                    fixed_list.append(word + mei_of_first_char_of_next_word)
                    if _DEBUG: print(u"மிகும் - விதி 6 - " + word + mei_of_first_char_of_next_word)
                    result.add(word,u'விதி 6',u'மிகா')
                    continue

            # 6.1.4 - 1 - வல்லினமெய் அல்லாத பிற மெய்களின் மேல் ஏறி வருகின்ற உகரம் - தேர்வு கட்டணம்
            if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])[0]) not in [u'க்',u'ச்',u'ட்',u'த்',u'ப்',u'ற்']:
                if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])[1]) == u'உ':
                    first_char_of_next_word = (next_word[0])
                    mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                    fixed_list.append(word + mei_of_first_char_of_next_word)
                    if _DEBUG: print(u"மிகும் - விதி 7 - " + word + mei_of_first_char_of_next_word)
                    result.add(word,u'விதி 7',u'மிகும்')
                    continue

            # 6.1.5 - 1 - இரண்டாம் வேற்றுமை விரி - கனியை  தின்றான்

            if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])[1]) == u'ஐ':
                first_char_of_next_word = (next_word[0])
                mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                fixed_list.append(word + mei_of_first_char_of_next_word)
                if _DEBUG: print(u"மிகும் - விதி 8 - " + word + mei_of_first_char_of_next_word)
                result.add(word,u'விதி 8',u'மிகும்')
                continue

            # 6.1.5 - 2 -  நான்காம் வேற்றுமை விரி - எனக்கு  கொடு
            print(tamil.utf8.get_letters(word)[-1])
            if tamil.utf8.get_letters(word)[-1] == u'கு':
                first_char_of_next_word = (next_word[0])
                mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                fixed_list.append(word + mei_of_first_char_of_next_word)
                if _DEBUG: print(u"மிகும் - விதி 9 - " + word + mei_of_first_char_of_next_word)
                result.add(word,u'விதி 9',u'மிகும்')
                continue

            # 6.1.6 - 1 - அ இ ய் ர் - அகர, இகர, யகர மெய் ஈற்று வினையெச்சம்; ஈறுகெட்ட எதிர்மறைப் பெயரெச்சம் ்
            # வர சொன்னான் குறிஞ்சி தலைவன்  தேங்காய் சட்னி  தயிர் குடம் தீரா சிக்கல்
            #print((safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])[1]))
            if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])[1]) == u'அ':
                if not u''.join(tamil.utf8.get_letters(word)[-2:]).endswith(u'டைய'):
                    first_char_of_next_word = (next_word[0])
                    mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                    fixed_list.append(word + mei_of_first_char_of_next_word)
                    if _DEBUG: print(u"மிகும் - விதி 10 - " + word + mei_of_first_char_of_next_word)
                    result.add(word,u'விதி 10',u'மிகும்')
                    continue

            if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])[1]) == u'இ':
                first_char_of_next_word = (next_word[0])
                mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                fixed_list.append(word + mei_of_first_char_of_next_word)
                if _DEBUG: print(u"மிகும் - விதி 11 - " + word + mei_of_first_char_of_next_word)
                result.add(word,u'விதி 11',u'மிகும்')
                continue


            print(safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])[0])
            if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])[0]) == u'ய்':
                first_char_of_next_word = (next_word[0])
                mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                fixed_list.append(word + mei_of_first_char_of_next_word)
                if _DEBUG: print(u"மிகும் - விதி 12 - " + word + mei_of_first_char_of_next_word)
                result.add(word,u'விதி 12',u'மிகும்')
                continue

            if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])[0]) == u'ர்':
                first_char_of_next_word = (next_word[0])
                mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                fixed_list.append(word + mei_of_first_char_of_next_word)
                if _DEBUG: print(u"மிகும் - விதி 13 - " + word + mei_of_first_char_of_next_word)
                result.add(word,u'விதி 13',u'மிகும்')
                continue

            if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])[1]) == u'ஆ':
                first_char_of_next_word = (next_word[0])
                mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                fixed_list.append(word + mei_of_first_char_of_next_word)
                if _DEBUG: print(u"மிகும் - விதி 14 - " + word + mei_of_first_char_of_next_word)
                result.add(word,u'விதி 14',u'மிகும்')
                continue

            rule15_letter = safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])
            # 6.1.7 - மகர இறுதி கெட்டு உயிர் ஈறாய் நிற்கும் சொற்கள் - மரம் கிளை
            # But this logic tot working for - உலகப்படம்  பார்த்து,  எடுப்பதெல்லாம் பெரிய
            # if len(tamil.utf8.get_letters(word)) > 1:
                # if (safe_splitMeiUyir(tamil.utf8.get_letters(word)[-1])) == u'ம்':
                #     if ''.join(tamil.utf8.get_letters(word)[-2]) not in (uyir_letters + numbers + ayudha_letter + granda + special_chars + english):
                #         if safe_splitMeiUyir(tamil.utf8.get_letters(word)[-2])[1] in uyir_letters:
                #             first_char_of_next_word = (next_word[0])
                #             if first_char_of_next_word not in (uyir_letters + numbers + ayudha_letter + granda):
                #                 if first_char_of_next_word not in ayudha_letter:
                #                     mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                #                     if mei_of_first_char_of_next_word in vallinam_letters:                    
                #                         fixed_list.append(word[:-2] + mei_of_first_char_of_next_word)            
                #                         print(u"மிகும் - Rule16 - " + word[:-2] + mei_of_first_char_of_next_word)
                #                         result.add(word,u'விதி 16',u'மிகும்')
                #                         continue   

            if (rule15_letter == u'ம்'):
                if safe_splitMeiUyir(tamil.utf8.get_letters(word)[-2])[1] in uyir_letters:
                    first_char_of_next_word = (next_word[0])
                    mei_of_first_char_of_next_word = safe_splitMeiUyir(first_char_of_next_word)[0]
                    fixed_list.append(word[:-2] + mei_of_first_char_of_next_word)
                    if _DEBUG: print(u"மிகும் - விதி 15 - " + word[:-2] + mei_of_first_char_of_next_word)
                    result.add(word,u'விதி 15',u'மிகும்')
                    continue

            fixed_list.append(word)
        fixed_list.append(word)
        if _DEBUG: print(u"விதி " + word)
    return fixed_list


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
