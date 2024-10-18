
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_session import Session
import model, constants, os, common, logging

# モデルのインスタンス化
db_config = {'pass_json':os.environ['PASS_JSON'], 'url_db':os.environ['URL_DB']}
m_flashcard_group_model = model.MFlashcardGroup(db_config, '3/data')
m_flashcard_model = model.MFlashcard(db_config, '2/data')
m_user_model = model.MUser(db_config, '4/data')

# ロガーの作成・取得
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('app')

# Flaskアプリのインスタンス作成
app = Flask(__name__, static_folder='../../static')

# session, CORS, bcryptの設定
CORS(app, supports_credentials=True)
app.config['SECRET_KEY'] = os.environ['SESSION_SECRET_KEY']  # セッション用のシークレットキーを設定
app.config['SESSION_TYPE'] = 'filesystem'  # セッションの保存タイプを設定
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
bcrypt = Bcrypt(app)
Session(app)

#####################################################################
# ログイン・ログアウト・新規登録
#####################################################################
@app.route('/api/login', methods=['POST'])
def login():
    '''
    ログインAPI
    '''
    rqs = request.get_json()
    user_name = rqs.get('name')
    password = rqs.get('password')
    user = m_user_model.select_user_by_username(user_name)[0]
    if user and bcrypt.check_password_hash(user['password'], password):
        user_name = user['name']
        user_id = user['id']
        session['user_name'] = user_name
        session['user_id'] = user_id
        users_flashcard_group_list = m_flashcard_group_model.select_flashcard_group_by_userid(user_id)
        return jsonify({'status':'success', 'logged_in':{'user_name': user_name, 'user_id': user_id}, 'list_users':users_flashcard_group_list})
    else:
        return jsonify({'status':'failure', 'logged_in':False, 'error':constants.MESSAGE_CERTIFICATION_ERROR})

@app.route('/api/logout', methods=['POST'])
def logout():
    '''
    ログアウトAPI
    '''
    session.pop('user_name',None)
    session.pop('user_id',None)
    return jsonify({'status':'success', 'logged_in':False})

@app.route('/api/register', methods=['POST'])
def register():
    '''
    新規登録API
    '''
    rqs = request.get_json()
    user_name = rqs.get('name')
    password = bcrypt.generate_password_hash(rqs.get('password')).decode('utf-8')
    if m_user_model.select_user_by_username(user_name):
        return jsonify({'status':'failure', 'logged_in':False, 'error':constants.MESSAGE_UNIQUENESS_ERROR})
    else:
        user_id = m_user_model.insert_user(user_name, password)
        session['user_name'] = user_name
        session['user_id'] = user_id
        return jsonify({'status':'success', 'logged_in':{'user_name': user_name, 'user_id': user_id}})
    

#####################################################################
# 単語帳生成
#####################################################################
@app.route('/api/generate_wordlist', methods=['POST'])
def generate_wordlist():
    '''
    テーマのリクエストに対し、レスポンスとしてワードリストを返却するAPI
    '''
    
    # リクエストから、入力のモード、ユーザーの入力、生成する単語数を取得
    rqs = request.get_json()
    logger.info("/api/generate_wordlist\nRequest from vue : ", rqs)
    mode = rqs.get('mode')
    user_input = rqs.get('input')
    num = rqs.get('num')

    # ユーザー入力値のバリデーション
    if common.validate_string(user_input, -1):
        return jsonify({'error':constants.MESSAGE_GENERATION_ERROR})
    if not (type(num) == int and constants.VARID_TERMS_NUMBER_RANGE['MIN'] <= num <= constants.VARID_TERMS_NUMBER_RANGE['MAX']):
        return jsonify({'error':constants.MESSAGE_GENERATION_ERROR})
   
    # OpenAI API の生成文の取得
    result = common.ask_openai(mode, user_input, num)

    if 'error' in result :
        # エラーを受け取ったらそのまま返却
        rsp = result
    else:
        # ChatGPTでの単語の生成に成功した場合
        wordlist = result['wordlist']
        title = result['title']

        # DBに保存
        group_id = m_flashcard_group_model.insert_flashcard_group(title, session['user_id'])
        state = m_flashcard_model.insert_flashcard(group_id, wordlist)

        if state == 'error':
            return jsonify({'error':constants.MESSAGE_CONNECTION_ERROR})

        rsp = {'wordlist':wordlist}

    # TOP画面に表示する単語帳を更新
    flashcard_group_list = m_flashcard_group_model.select_latest_flashcard_group()
    users_flashcard_group_list = m_flashcard_group_model.select_flashcard_group_by_userid(session['user_id'])
    rsp.update({'flashcard_group_list':flashcard_group_list, 'list_users':users_flashcard_group_list})
    return jsonify(rsp)

#####################################################################
# 単語帳情報取得
#####################################################################
@app.route('/api/get_saved_wordlist', methods=['POST'])
def get_saved_wordlist():
    '''
    DBに保存済みの単語帳情報を返却するAPI
    '''
    rqs = request.get_json()
    group_id= rqs.get('group_id')

    # リクエストで指定されたgroup_idの単語帳を取得
    rsp = m_flashcard_model.select_flashcard(group_id)
    return jsonify(rsp)

#####################################################################
# 単語帳削除
#####################################################################
@app.route('/api/delete_flashcard', methods=['POST'])
def delete_flashcard():
    '''
    DBに保存済みの単語帳情報を削除するAPI
    '''
    rqs = request.get_json()
    group_id= rqs.get('group_id')

    # ユーザーが作成した単語帳でない場合返却
    target_id = m_flashcard_group_model.select_flashcard_group_by_id(group_id).values()['id']
    if target_id != session['user_id']:
        return jsonify({'error':'不正な値です'})

    # DBから削除
    result = m_flashcard_model.delete_flashcard_by_group_id(group_id)
    result = m_flashcard_group_model.delete_flashcard_group(group_id)

    # TOP画面に表示する単語帳を更新
    flashcard_group_list = m_flashcard_group_model.select_latest_flashcard_group()
    users_flashcard_group_list = m_flashcard_group_model.select_flashcard_group_by_userid(session['user_id'])

    rsp = {'result':result, 'flashcard_group_list':flashcard_group_list, 'list_users':users_flashcard_group_list}
    return jsonify(rsp)


#####################################################################
# 検索
#####################################################################
@app.route('/api/search_wordlist', methods=['POST'])
def search_wordlist():
    '''
    キーワードを含む既存のwordlistを返却するAPI
    '''
    rqs = request.get_json()
    keyword = rqs.get('keyword')

    # キーワードが前方一致する単語帳グループを取得
    group_id_list = m_flashcard_group_model.select_flashcard_group_by_keyword(keyword)

    # キーワードが前方一致する単語を取得
    group_id_list_by_flashcard = m_flashcard_model.select_flashcard_by_keyword(keyword)
    id_list = []
    for value in group_id_list_by_flashcard:
        group_id = value['group_id']
        if group_id not in id_list:
            id_list.append(group_id)
    
    for group_id in id_list:
        group = m_flashcard_group_model.select_flashcard_group_by_id(group_id)[0]
        group_id_list.append(group)
    
    logger.info(f'group_id_list:{group_id_list}')

    if len(group_id_list) == 0:
        return jsonify({'result':'該当する単語帳は見つかりませんでした。'})

    count = len(group_id_list)
    result = str(count) + '件ヒットしました。'
    return jsonify({'flashcard_group_list':group_id_list, 'result':result})

#####################################################################
# TOP画面のレンダリング
#####################################################################
@app.route('/')
def index():
    '''
    最初にTOP画面を表示する
    '''
    # TOP画面に表示する単語帳を取得
    flashcard_group_list = m_flashcard_group_model.select_latest_flashcard_group()
    if session:
        user_name = session['user_name']
        user_id = session['user_id']
        logged_in = {'user_name': user_name, 'user_id': user_id}
        users_flashcard_group_list = m_flashcard_group_model.select_flashcard_group_by_userid(user_id)
    else:
        logged_in = False
        users_flashcard_group_list = {}
    logger.info("trough index")
    return render_template('index.html', list_flask=flashcard_group_list, list_users=users_flashcard_group_list, logged_in=logged_in)

if __name__=='__main__':
    app.run(debug=True, host=os.environ['HOST_DEFAULT'], port=int(os.environ['PORT_DEFAULT']))