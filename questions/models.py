# coding: utf-8
from __future__ import unicode_literals

from django.db import models
from persol_users.models import PersolUser
from collections import OrderedDict

class Question(models.Model):
    questionnaire_title = models.CharField(max_length=200)
    question_text = models.TextField(max_length=500)
    
    def get_users(self):
        persol_user_ids = Answer.objects.values("persol_user").filter(question = self).distinct()
        return PersolUser.objects.filter(id__in = persol_user_ids)

    def get_sorted_choices(self):
        return self.choice_set.all().order_by('choice_index')

    def get_answer(self,u_id,c_id):
        answerCount = Answer.objects.filter(question = self,persol_user = u_id,choice = c_id).count()
        if answerCount == 0:
            return "-"
        return Answer.objects.filter(question = self,persol_user = u_id,choice = c_id)[0].answer_text
        
    def get_user_answers(self):
        user_answers_dict = {}
        choice_answer_dict = {}
        choices = self.get_sorted_choices()
        for persol_user in self.get_users():
            print "models"
            print choices
            for i,choice in enumerate(choices):
                print choice.choice_text
                choice_answer_dict[i] = self.get_answer(persol_user,choice) 
            user_answers_dict[persol_user] = OrderedDict(sorted(choice_answer_dict.items(), key=lambda x: x[0]))
            print sorted(choice_answer_dict.items(), key=lambda x: x[0])
        print user_answers_dict
        return user_answers_dict
    
    # 
    def get_choices_text(self):
        return '\n'.join(self.get_sorted_choices().values_list('choice_text', flat=True))
        
    # 選択肢を設定
    def set_choices(self, choices_text):
        # 今回の文字列にない選択肢は削除
        for ch in self.choice_set.all():
            if ch.choice_text not in choices_text.splitlines():
                ch.delete()
        # 今回の文字列にある選択肢は回答を保存、choiceに紐付くレコードを削除、再登録を行う
        # 選択肢に入力順序を持たせ、その順序でソートする
        # 今回の文字列で選択し追加･更新
        cnt = 0
        for text in choices_text.splitlines():
            print text
            print cnt
            c = self.choice_set.filter(choice_text=text).first()
            if c is None:
                self.choice_set.create(choice_text=text,choice_index = cnt)
            else:
                c.choice_text = text
                c.choice_index = cnt;
                c.save()
            cnt+=1
    
    
    # イベントのviewから使う、作成と変更のメソッド
    def update_from_posted_params(self, type, posted_params):
        self.questionnaire_title = posted_params['questionnaire_title_'+type]
        self.question_text = posted_params['question_text_'+type]
        self.save()
        self.set_choices(posted_params['question_choices_'+type])
        
    # 紐づいているイベント
    def event(self):
        return self.event_date if hasattr(self, 'event_date') else self.event_location
    
    
    # 指定のユーザーの回答を削除する
    def delete_answer_of(self, user):
        for ans in self.answer_set.filter(persol_user=user):
            ans.delete()
        
        return
    
    # タイプ別のデフォルトテキストをセットしたオブジェクトを作成
    @classmethod
    def get_default_question(cls, type):
        if type == 'd':
            title = '日時アンケート'
            text = 'いつがいいですか？'
        elif type == 'l':
            title = '場所アンケート'
            text = 'どこがいいですか？'
        
        return cls(questionnaire_title=title, question_text=text)

        
                
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    choice_index = models.IntegerField()

    def get_answer(self,u_id):
        answerCount = Answer.objects.filter(choice = self,persol_user = u_id).count()
        if answerCount == 0:
            return "-"
        return Answer.objects.filter(choice = self,persol_user = u_id)[0].answer_text

class Answer(models.Model):
    ANSWER_OPTIONS =['○','△','×']
    
    persol_user = models.ForeignKey(PersolUser, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    answer_text = models.CharField(max_length=200)
    
    class Meta:
        unique_together=(("persol_user","question","choice"))