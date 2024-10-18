import os
import re
import openai
import datetime
import constants

def ask_openai(mode, user_input, num):
    '''
    openAI API に答えの生成をリクエスト
    戻り値は辞書型
    '''
    openai.api_key = os.environ["OPENAI_API_KEY"]

    num = str(num)
    if mode == 'theme':
        prompt = ("お疲れ様です。\n私は以下のテーマについての初学者です。\n以下のテーマについて、特筆すべき専門用語や人物を" + num + "個抜き出し、\nそれぞれに簡潔な説明文を付けてください。\n"
                +"###Constraints###\n"
                +"・説明文の最初に「" + constants.STR_SPLIT_WORD_AND_DESCRIPTION + "」と記載してください"
                +"・説明文の最後に「" + constants.STR_SPLIT_TERMS + "」と記載してください"
                +"・用語の先頭には、例に倣って番号をつけてください"
                +"・間違った情報を記載した場合、あなたはペナルティを受けます"
                +"・一番下に、生成した用語に適したタイトルを20文字以内で記載してください"
                +"・タイトルは「" + constants.STR_SPLIT_TITLE + "」で挟んでください"
                +"###Example###\n"
                +"1. エステル" + constants.STR_SPLIT_WORD_AND_DESCRIPTION + "有機酸または無機酸のオキソ酸と、アルコールまたはフェノールのようなヒドロキシ基を含む化合物との縮合反応で得られる化合物。" + constants.STR_SPLIT_TERMS + "\n"
                +"2. ビタミン" + constants.STR_SPLIT_WORD_AND_DESCRIPTION + "生物の生存・生育に微量に必要な栄養素のうち、その生物の体内で十分な量を合成できない炭水化物・タンパク質・脂質以外の有機化合物の総称。" + constants.STR_SPLIT_TERMS + "\n"
                +"" + constants.STR_SPLIT_TITLE + "代表的な有機化合物" + constants.STR_SPLIT_TITLE
                +"###テーマ###\n" 
                + user_input)
    elif mode == 'article':
        prompt = ("お疲れ様です。次の文章から特筆すべき専門用語や人物を" + num + "個抜き出し、\nそれぞれに簡潔な説明文を付けてください。\n"
                +"###Constraints###\n"
                +"・説明文の最初に「" + constants.STR_SPLIT_WORD_AND_DESCRIPTION + "」と記載してください"
                +"・説明文の最後に「" + constants.STR_SPLIT_TERMS + "」と記載してください"
                +"・用語の先頭には、例に倣って番号をつけてください"
                +"・間違った情報を記載した場合、あなたはペナルティを受けます"
                +"・一番下に、生成した用語に適したタイトルを20文字以内で記載してください"
                +"・タイトルは「" + constants.STR_SPLIT_TITLE + "」で挟んでください"
                +"###Example###\n"
                +"1. エステル" + constants.STR_SPLIT_WORD_AND_DESCRIPTION + "有機酸または無機酸のオキソ酸と、アルコールまたはフェノールのようなヒドロキシ基を含む化合物との縮合反応で得られる化合物。" + constants.STR_SPLIT_TERMS + "\n"
                +"2. ビタミン" + constants.STR_SPLIT_WORD_AND_DESCRIPTION + "生物の生存・生育に微量に必要な栄養素のうち、その生物の体内で十分な量を合成できない炭水化物・タンパク質・脂質以外の有機化合物の総称。" + constants.STR_SPLIT_TERMS + "\n"
                +"" + constants.STR_SPLIT_TITLE + "代表的な有機化合物" + constants.STR_SPLIT_TITLE
                +"###テーマ###\n" 
                + user_input)
    
    try:
        response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt},
        ])
    except openai.OpenAIError as e:
        print(f"Error: {e}")
        result = {"error":constants.MESSAGE_CONNECTION_ERROR}
        return result

    # 料金の表示
    calc_price(response.usage)
    print("###RESPONSE###\n", response)

    # 生成された文章を区切り文字で区切り、用語・説明文の配列とタイトルが格納された辞書型に調整する
    string_by_gpt = response.choices[0].message.content
    result = transform_string_to_dictionary(string_by_gpt)

    return result


def transform_string_to_dictionary(message):
    '''
    文字列を区切り、辞書型に格納する
    戻り値：辞書型
    '''

    # 渡された文字列を用語ごとに区切り、[用語説明文, 用語説明文, ...]の状態の配列にする
    pairs = message.split(constants.STR_SPLIT_TERMS)

    if len(pairs) == 1:
        # 文字列に区切り文字が含まれていなかった場合
        result = {"error":constants.MESSAGE_GENERATION_ERROR}
        return result
    
    else:
        # 文字列を用語ごとに区切ることができた場合
        wordlist = []

        # 各要素をさらに用語と説明文に分割し、辞書型にして配列に格納する
        for i in range(0, len(pairs), 1):

            # [用語, 説明文]の形に分割
            pair = re.split(constants.STR_SPLIT_WORD_AND_DESCRIPTION, pairs[i])
            print(" pair", i, pair)

            if len(pair) == 2:
                # [用語, 説明文]の2要素に分割できた場合
                word = pair[0]
                description = pair[1]

                # 不要な文字列を削除
                mtc = re.match(r"(\n| |)\d+\.( |)", word) 
                if (mtc):
                    word = re.sub(mtc.group(), '', word)

                # 字数制限内のStr型であれば返却用の配列に格納
                if validate_string(word, constants.WORD_MAX_LENGTH) and validate_string(description, constants.DESCRIPTION_MAX_LENGTH):
                    wordlist.append({"word":word, "description":description})

            elif len(pair) == 1:
                # 分割できなかった場合
                title = pair[0]
                title = re.sub("\n", '', title)
                if re.match(r"(\n|)"+constants.STR_SPLIT_TITLE, title):
                    # タイトル用の区切り文字が含まれている場合タイトルとして設定
                    title = re.sub(constants.STR_SPLIT_TITLE, '', title)
        
        # 返却用配列が空の場合エラー
        if wordlist == []:
            result = {constants.MESSAGE_GENERATION_ERROR}
            return result

        # タイトルが字数制限内のStr型でなければ、１つ目の用語をタイトルに設定
        if not validate_string(title, constants.TITLE_MAX_LENGTH):
            title = wordlist[0]['word']
            
        result = {'wordlist':wordlist, 'title':title}

    return result


def calc_price(usage):
    '''
    総トークン数から１回の応答のコストを算出
    '''
    usage = str(usage)
    usage_num = re.findall(r'\d+', usage) #[completion_tokens, prompt_tokens, total_tokens]
    price = float(usage_num[0])*60.00/1000000.0 + float(usage_num[1])*30.00/1000000.0
    print("Price:{0}$ ≒ {1}yen".format(price, price*151.8))
    return


def now_time():
    '''
    現在時刻を取得
    '''
    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    now = datetime.datetime.now(JST)
    now = str(now)
    return now


def validate_string(input_string, length:int=None):
    '''
    input_stringが長さlength以下の空でない文字列である ⇒ True
    第1引数:any 第2引数:int,無指定で無制限
    '''
    if not isinstance(input_string, str):
        return False 
    elif input_string.strip() == '':
        return False
    elif length and len(input_string) > length:
        return False
    else:
        return True
    
def validate_id(input_id):
    '''
    input_idがint型または整数のstr型である ⇒ True
    '''
    if type(input_id) == str and str.isdigit(input_id):
        input_id = int(input_id)  
    if not type(input_id) == int:
        return False
    return input_id