from basemodel import BaseModel
import common, constants

class MFlashcardGroup(BaseModel):
    def __init__(self, config, table):
        super().__init__(config)
        self.table = table

    def insert_flashcard_group(self, name, user_id):
        '''
        作成したflashcardのgroup情報をDBに登録
        name:Str
        '''

        #バリデーション
        if not common.validate_string(name, constants.TITLE_MAX_LENGTH) :
            return 'error'
        
        data = [{'name':name, 'user_id':user_id}]
        group_id = self.insert_data(self.table, data)
        self.logger.info('新規単語帳が正常に保存されました')
        return group_id

    
    def select_latest_flashcard_group(self):
        '''
        TOP表示する最新5件の単語帳グループを取得
        '''
        ref = self.select_limit_data(self.table, 'lastdate', constants.LATEST_WORDLISTS_NUM)
        ref.reverse()
        return ref
    
    def select_flashcard_group_by_id(self, group_id):
        ref = self.select_by_column_value(self.table, group_id, 'id')
        self.logger.info(f'select_flashcard_group_by_id:{ref}')
        return ref
    
    def select_flashcard_group_by_keyword(self, keyword):
        ref = self.select_by_keyword(self.table, keyword, 'name')
        self.logger.info('検索結果')
        self.logger.info(ref)
        return ref
    
    def select_flashcard_group_by_userid(self, user_id):
        '''
        user_idから単語帳グループを取得
        '''
        ref = self.select_by_column_value(self.table, user_id, 'user_id')
        ref.reverse()
        return ref
    
    def delete_flashcard_group(self, group_id):
        '''
        group_idを指定して削除
        '''
        return self.delete_by_column_value(self.table, group_id, 'id')