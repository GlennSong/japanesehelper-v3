import fugashi
import requests
import csv 
from datetime import datetime 

def extract_complete_words(text):
    tagger = fugashi.Tagger()
    words = []
    current_word = []
    current_pos = None

    for word in tagger(text):
        # Check if the current word is part of a verb or an auxiliary verb
        if word.feature.pos1 in {'動詞', '助動詞'}:
            current_word.append(word.surface)
            current_pos = word.feature.pos1
        else:
            if current_word:
                # Add the current compound word to the words list
                words.append(''.join(current_word))
                current_word = []
            # Add the current word to the words list
            words.append(word.surface)
            current_pos = None

    # Add any remaining compound word to the words list
    if current_word:
        words.append(''.join(current_word))

    return words


# helper function to test if the letter is a valid kanji unicode
def is_kanji(character):
    return '\u4E00' <= character <= '\u9FBF'

def is_hiragana(character):
    return '\u3040' <= character <= '\u309F'

def is_katakana(character): 
    return '\u30A0' <= character <= '\u30FF'

def get_english_meaning(word):
    #filter the words that are not kanji
    
    if(len(word) == 1 and not is_kanji(word[0])): 
        return False, word, "No definition found", "", ""
     
    # if(word == "" or is_hiragana(word) or is_katakana(word)):
    #     return False, "No definition found"

    url = f'https://jisho.org/api/v1/search/words?keyword={word}'
    response = requests.get(url)

    if response.status_code == 200:
        try: 
            data = response.json()

            if data['data']:
                english_meaning = data['data'][0]['senses'][0]['english_definitions']
                part_of_speech = data['data'][0]['senses'][0]['parts_of_speech']
                japanese_reading = data['data'][0]['japanese'][0]['reading']
                return True, word, ', '.join(english_meaning), ', '.join(part_of_speech), japanese_reading
            else:
                return False, word, 'No definition found', '', ''
        except:
            return False, word, 'No definition found', '', ''

    return False, word, 'No definition found', '', ''


def get_kanji_character_info(character):
    url = "https://kanjiapi.dev/v1/kanji/" + character
    response = requests.get(url)
    data = response.json()
    kun_reading = ""
    if data['kun_readings']:
        kun_reading = data['kun_readings'][0]

    on_reading = ""
    if data['on_readings']:
        on_reading = data['on_readings'][0]

    return [character, kun_reading, on_reading, data['grade'], data['meanings']]
   

def get_all_kanji(text):
    return list(dict.fromkeys(char for char in text if is_kanji(char)))

# text = "今日はいい天気ですね。肉を食べたい"
# text = "在外邦人向けサービス「NHKワールド・プレミアム」は、NHKが国内で放送するニュース・情報番組、ドラマ、音楽番組、子ども番組、スポーツ中継などから選んだ番組を24時間編成しています。"
text = "2017年のベストカバーを選ぶ祭典"
print("Input Text: " + text)

# get the kanji characters
kanji = get_all_kanji(text)
#print("Kanji: " + ', '.join(kanji))

# get the kanji characters and their meanings and store it in a list.
kanji_info = []
for char in kanji:
    # character, kun_reading, on_reading, grade_level, meaning = get_kanji_character_info(char)
    kanji_info.append(get_kanji_character_info(char))

# sort all of the kanji characters by grade level
kanji_info.sort(key=lambda x: x[3])

# create a filename with date stamp
now = datetime.now()
filename = 'kanji-' + now.strftime("%m-%d-%Y_%H-%M-%S") + '.csv'

with open(filename, mode='w', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Character', 'Kun Reading', 'On Reading', 'Grade Level', 'Meaning'])
    for row in kanji_info:
        # combine the meanings into a single string
        all_meanings = ', '.join(row[4])
            
        # write the row to the csv file
        writer.writerow([row[0], row[1], row[2], row[3], all_meanings])

        # print the row to the console
        character, kun_reading, on_reading, grade_level, meaning = row
        print(character + " (Grade " + str(grade_level) + "): (Kun: " + kun_reading + " On: " + on_reading + "), " + all_meanings)

#get the words and definitions
word_info = []
words = extract_complete_words(text)
for word in words:
    # check if the word is already in the list. If it is, skip it.
    if not any(jpn_word == word for jpn_word, _, _, _ in word_info):
        found_eng_meaning, jpn_word, english_meaning, part_of_speech, japanese_reading = get_english_meaning(word)
        if(found_eng_meaning):
            word_info.append([jpn_word, japanese_reading, part_of_speech, english_meaning])

# print(words)

words_filename = 'words-' + now.strftime("%m-%d-%Y_%H-%M-%S") + '.csv'
with open(words_filename, mode='w', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Word', 'Japanese Reading', 'Part of Speech', 'English Meaning'])
    for row in word_info:
        writer.writerow(row)

        # print the row to the console
        jpn_word, japanese_reading, part_of_speech, english_meaning = row
        print(jpn_word + " (" + japanese_reading + "): " + "(" + part_of_speech + ") " + english_meaning)


print("Output Kanji CSV File: " + filename)
print("Output Words CSV File: " + words_filename)