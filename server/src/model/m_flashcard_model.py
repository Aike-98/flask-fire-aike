from basemodel import BaseModel
import common, constants

class MFlashcard(BaseModel):
    def __init__(self, config, table):
        super().__init__(config)
        self.table = table

    def insert_flashcard(self, group_id, wordlist):
        '''
        作成したワードリストをDBに保存
        '''
        #バリデーション
        if not type(group_id) == int:
            return 'error'

        group_id_dict = {"group_id":group_id}
        for i in range(0, len(wordlist), 1):
            word = wordlist[i]['word']
            description = wordlist[i]['description']

            #要素ごとのバリデーション
            if not common.validate_string(word, constants.WORD_MAX_LENGTH):
                return 'error'
            if not common.validate_string(description, constants.DESCRIPTION_MAX_LENGTH):
                return 'error'
            
            wordlist[i].update(group_id_dict)
        self.insert_data(self.table,  wordlist)
        self.logger.info('新規単語が正常に保存されました')
        return
    
    def select_flashcard(self, group_id):
        '''
        指定のグループidのワードリスト情報を取得
        '''
        # バリデーション
        if not group_id:
            return 'error'
        
        ref = self.select_by_column_value(self.table, group_id, 'group_id')
        data_list = []
        for i in range(0, len(ref), 1):
            data = {'word': ref[i]['word'], 'description':ref[i]['description']}
            data_list.append(data)
        
        self.logger.info(f'select_flashcard {group_id} :{data_list}')
        return data_list
    
    def select_flashcard_by_keyword(self, keyword):
        ref = self.select_by_keyword(self.table, keyword, 'word')
        self.logger.info('検索結果')
        self.logger.info(ref)

        
        return ref
    
    def delete_flashcard_by_group_id(self, group_id):
        '''
        削除
        '''
        return self.delete_by_column_value(self.table, group_id, 'group_id')