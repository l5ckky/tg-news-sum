import telethon.types
from pymystem3 import Mystem
import string

stem = Mystem()


def word_filter(words, t):
    if not t:
        return False
    stext = t[:]
    text = t.lower()
    # text = ''.join([i for i in text if i.isalpha() or i in string.punctuation or i == ' '])
    lem_text = stem.lemmatize(text)
    text_array = [j for j in [i for i in lem_text] if j.isalpha()]
    for word in words:
        if word.lower() in text_array:
            # index = stext.index(word)
            # print(f'Совпадение слова {word} со списком на индексе {index}')
            return word, lem_text
    return False


def words_separator(word, text, lem_text):
    texta = [i for i in text.split() if i.strip()]
    dtext = dict(enumerate(texta))
    text_array = lem_text
    text_array = "".join(text_array).split()
    # print(text_array)
    text_array = [i for i in text_array if i.strip()]
    text_array = dict(enumerate(["".join([j for j in i if j.isalpha()]) for i in text_array]))
    index_word = list(text_array.values()).index(word.lower())
    # print(dtext, text_array, sep="\n\n")
    # print(index_word)

    r = list(range(-5, 5 + 1))
    rwords = []
    for i in r:
        if 0 <= index_word + i <= len(texta) - 1:
            if i == 0:
                rwords.append(f"<strong>{texta[index_word + i]}</strong>")
            else:
                rwords.append(texta[index_word + i])

    return f"<blockquote>{' '.join(rwords)}</blockquote>"


def text_msg(message: telethon.types.Message):
    text = message.message
    ftext = text[:(15 if len(text) >= 15 else None)] + ("…" if len(text) >= 15 else "")
    return f"\"{ftext}\"(msgID={message.id})"


async def text_ch(client, channel_id, add_id=True):
    return f"{(await client.get_entity(channel_id)).title}{f'(chID={channel_id})' if add_id else ''}"
