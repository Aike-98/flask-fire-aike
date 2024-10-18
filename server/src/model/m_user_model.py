from basemodel import BaseModel
import common

class MUser(BaseModel):
    def __init__(self, config, table):
        super().__init__(config)
        self.table = table
    
    def insert_user(self, user_name, password):
        '''
        ユーザー情報をDBに保存
        '''

        #バリデーション
        if not common.validate_string(user_name) :
            return 'error'
        
        data = [{'name':user_name, 'password':password}]
        user_id = self.insert_data(self.table, data)
        self.logger.info('新規ユーザーが正常に保存されました')
        return user_id
    
    def select_user_by_username(self, user_name):
        '''
        ユーザー名からユーザー情報を取得
        '''
        ref = self.select_by_column_value(self.table, user_name, 'name')
        return ref