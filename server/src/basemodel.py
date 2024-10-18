import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import common, logging

class BaseModel():

    def __init__(self, config):
        pass_json = config['pass_json']
        url_db = config['url_db']
        cred= credentials.Certificate(pass_json)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'databaseURL': url_db,
                'databaseAuthVariableOverride': {
                    'uid': 'my-service-worker'
                }
            })
        
        # ロガーの作成・取得
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
            
    def select_limit_data(self, table, column, num):
        ref = db.reference(table)
        records = ref.order_by_child(column).limit_to_last(num).get()
        data_list = []
        for value in records.values():
            data = {'id': value['id'], 'name':value['name']}
            data_list.append(data)
        return data_list
    
    def select_by_column_value(self, table, value, column):
        '''
        指定した条件に一致するレコードをすべて取得する。
        '''
        ref = db.reference(table)
        records = ref.order_by_child(column).equal_to(value).get()
        data_list=[]
        for data in records.values():
            data_list.append(data)
        return data_list
    
    def select_by_keyword(self, table, keyword, column):
        '''
        キーワードと完全一致または前方一致するレコードをすべて取得する。
        '''
        ref = db.reference(table)
        # 前方一致するレコードを取得　；firebase realtime database では後方一致の検索は不可
        prefix_match_records = ref.order_by_child(column).start_at(keyword).end_at(keyword + '\uf8ff').get()
        self.logger.info(f'keyword:{keyword}')
        self.logger.info(f'prefix_match_records:{prefix_match_records}')
        data_list=[]
        for data in prefix_match_records.values():
            data_list.append(data)
        return data_list

    
    def get_last_id(self, table):
        '''
        指定したテーブルで最後に追加されたレコードのidを返す。
        '''
        ref = db.reference(table)
        record = ref.order_by_child('lastdate').limit_to_last(1).get()
        values = record.values()
        last_record = next(iter(values))
        last_id = int(last_record["id"])
        return last_id
    
    
    def insert_data(self, table, data):
        '''
        各レコードに現在時刻、idを追加してDBに登録する。
        引数のdataには配列に辞書型を格納して渡すこと。
        '''
        ref = db.reference(table)
        start_id = self.get_last_id(table) + 1
        now = common.now_time()
        #setting_data = {}
        for i in range(0, len(data), 1):
            id = start_id + i
            data_default = {"lastdate":now, "id":id}
            data[i].update(data_default)
            ref.push(data[i])
        last_id = self.get_last_id(table)
        return last_id
    
    def delete_by_column_value(self, table, value, column):
        '''
        指定した条件に一致するレコードをすべて削除する。
        '''
        ref = db.reference(table)
        ref.order_by_child(column).equal_to(value).remove()
        return