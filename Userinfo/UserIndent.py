# coding=utf-8

'''
@author   兰威
@type     用户订单
'''
import json

from Activity.ACmodel import ACmodelHandler
from Appointment.APmodel import APmodelHandler
from BaseHandlerh import BaseHandler
from Database.tables import ActivityEntry, Activity, AppointEntry, Appointment, AppointmentInfo, ActivityImage
from Userinfo import Ufuncs

class UserIndent(BaseHandler):
    retjson ={'code':'', 'contents':''}
    def post(self):
        ret_contents = {}
        ret_activity = []
        ret_e_appointment=[]
        ret_my_appointment=[]
        ac = ACmodelHandler()
        ap = APmodelHandler()
        type = self.get_argument('type')
        u_id = self.get_argument('uid')
        auth_key = self.get_argument('authkey')
        ufuncs = Ufuncs.Ufuncs()
        if ufuncs.judge_user_valid(u_id, auth_key):
            if type == '10901':  # 查看我的已报名的约拍活动
                ret_activity =self.get_activity(u_id,0)
                ret_contents['activity'] = ret_activity
                ret_e_appointment =self.get_e_appointment(u_id,0)
                ret_contents['entryappointment'] = ret_e_appointment
                ret_my_appointment = self.get_my_appointment(u_id,0)
                ret_contents['myappointment'] = ret_my_appointment
                self.retjson['code'] = '10392'
                self.retjson['contents'] =ret_contents

            elif type == '10902':    # 查看我的正在进行的约拍活动
                ret_activity = self.get_activity(u_id,1)
                ret_contents['activity'] =ret_activity
                ret_e_appointment = self.get_e_appointment(u_id, 1)
                ret_contents['entryappointment'] = ret_e_appointment
                ret_my_appointment = self.get_my_appointment(u_id, 1)
                ret_contents['myappointment'] = ret_my_appointment
                self.retjson['code'] = '10393'
                self.retjson['contents'] = ret_contents

            elif type == '10903':    # 查看我的已经完成的但是没有评价约拍活动
                ret_activity = self.get_activity(u_id,2)
                ret_contents['activity'] =ret_activity
                ret_e_appointment = self.get_e_appointment_not_evaluate(u_id)
                ret_contents['entryappointment'] = ret_e_appointment
                ret_my_appointment = self.get_my_appointment_not_evaluate(u_id)
                ret_contents['myappointment'] = ret_my_appointment
                self.retjson['code'] = '10394'
                self.retjson['contents'] = ret_contents

            elif type == '10909':    # 查看我的已经完成评价的约拍 这里没有活动了，因为活动没有状态码4

                ret_e_appointment = self.get_e_appointment_evaluate(u_id)
                ret_contents['entryappointment'] = ret_e_appointment
                ret_my_appointment = self.get_my_appointment_evaluate(u_id)
                ret_contents['myappointment'] = ret_my_appointment
                self.retjson['code'] = '10395'
                self.retjson['contents'] = ret_contents

            elif type == '10904':  # 选择约拍对象
                apid = self.get_argument('apid')
                chooseuid = self.get_argument('chooseduid')
                try:
                    registEntry = self.db.query(AppointEntry).\
                        filter(AppointEntry.AEregisterID == chooseuid, AppointEntry.AEapid == apid).one()  # 查找报名项
                    if registEntry:
                        if registEntry.AEvalid == 1:  # 用户未取消报名
                            if registEntry.AEchoosed:
                                self.retjson['contents'] = u'之前已选择过该用户！'
                            else:  # 用户报名中且未被选择，添加新的约拍项
                                registEntry.AEchoosed = 1  # 该用户被选择
                                try:
                                    appointment = self.db.query(Appointment.APid, Appointment.APsponsorid, Appointment.APtype,
                                                                Appointment.APstatus).\
                                        filter(Appointment.APid == registEntry.AEapid).one()
                                    if appointment.APsponsorid == int(u_id):  # 该操作用户是发起者
                                        mid=pid=0
                                        if appointment.APtype == 1:  # 发起者是摄影师：
                                            mid = chooseuid
                                            pid = u_id
                                        elif appointment.APtype == 0:  # 发起者是模特：
                                            mid = u_id
                                            pid = chooseuid
                                        print 'before change'
                                        self.db.query(Appointment).filter(Appointment.APid == appointment.APid).\
                                        update({"APstatus": 1}, synchronize_session='evaluate') # 将该约拍项移到进行中
                                        print 'after change'
                                        newappinfo = AppointmentInfo(
                                            AImid=mid,
                                            AIpid=pid,
                                            AIappoid=apid
                                        )
                                        try:
                                            self.db.merge(newappinfo)
                                            self.db.commit()
                                            self.retjson['code'] = '10920'
                                            self.retjson['contents'] = u"选择约拍对象成功"
                                        except Exception, e:
                                            print e
                                            self.retjson['code'] = '10925'
                                            self.retjson['contents'] = u"数据库插入错误"
                                    else:
                                        self.retjson['code'] = '10921'
                                        self.retjson['contents'] = u"该用户没有选择权限！"
                                except Exception, e:
                                    print e
                                    self.retjson['code'] = '10924'
                                    self.retjson['contents'] = u'该约拍不存在或已过期'
                        else:
                            self.retjson['code'] = '10923'
                            self.retjson['contents'] = u'用户已取消报名！'
                except Exception,e:
                    print e
                    self.retjson['contents'] = u'选择用户未报名该约拍'


            elif type == '10906': #结束活动
                ac_id = self.get_argument("acid")
                self.finish_avtivity(u_id, ac_id)

            elif type == '10907': #结束活动报名
                ac_id = self.get_argument('acid')
                self.finnish_activity_register(u_id,ac_id)
            elif type == '10905':  # 将约拍移动到已完成
                ap_id = self.get_argument('apid')
                try:
                    appointment = self.db.query(Appointment).filter(Appointment.APid == ap_id).one()
                    appointmentinfo = self.db.query(AppointmentInfo).filter(AppointmentInfo.AIappoid == ap_id).one()
                    if appointment.APstatus == 0:  # 报名中
                        self.retjson['code'] = '10260'
                        self.retjson['contents'] = u'该约拍尚在报名中，无法结束！'

                    elif appointment.APstatus == 1:  # 进行中
                        if int(u_id) == appointmentinfo.AIpid:
                            appointment.APstatus = 2
                            self.db.commit()
                            self.retjson['code'] = '10258'
                            self.retjson['contents'] = u'成功结束约拍！'
                        elif int(u_id) == appointmentinfo.AImid:
                            appointment.APstatus = 2
                            self.db.commit()
                            self.retjson['code'] = '10258'
                            self.retjson['contents'] = u'成功结束约拍！'
                        else:
                            self.retjson['code'] = '10260'
                            self.retjson['contents'] = u'该用户无结束权限！！'

                    elif appointment.APstatus > 1:  # 已完成
                        self.retjson['code'] = '10260'
                        self.retjson['contents'] = u'该约拍已结束！'
                except Exception, e:
                    print e
                    self.retjson['code'] = '10261'
                    self.retjson['contents'] = u'未找到该约拍记录！'

            # 用户评价约拍
            elif type == '10908':
                score = self.get_argument('score')
                comment = self.get_argument('comment')
                ap_id = self.get_argument('apid')
                try:
                    appointment = self.db.query(Appointment).filter(Appointment.APid == ap_id).one()
                    appointmentinfo = self.db.query(AppointmentInfo).filter(AppointmentInfo.AIappoid == ap_id).one()
                    if appointment.APstatus > 1:
                        if int(u_id) == appointmentinfo.AImid:
                            self.evaluate_appointment(0,appointment,appointmentinfo,comment,score)
                        elif int(u_id) == appointmentinfo.AIpid:
                            self.evaluate_appointment(1, appointment,appointmentinfo, comment, score)
                        else:
                            self.retjson['code'] = '10982'
                            self.retjson['contents'] = '您没有对该约拍评价的权限'
                    else:
                        self.retjson['code'] = '10982'
                        self.retjson['contents'] = '您没有对该约拍评价的权限'
                except Exception,e:
                    print e
                    self.retjson['code'] = '10983'
                    self.retjson['contents'] = '未查询到该约拍'




        else :
            self.retjson['code'] = '10391'
            self.retjson['contents'] = '用户授权码不正确'

        self.write(json.dumps(self.retjson, ensure_ascii=False, indent=2))

    def get_activity(self,u_id,number):  #按照活动的状态和用户ID查看活动详情
        ret_activity=[]
        ac_enteys = self.db.query(ActivityEntry).filter(ActivityEntry.ACEregisterid == u_id,
                                                        ActivityEntry.ACEregisttvilid == True).all()
        if number == 2:
            for ac_entey in ac_enteys:
               ac_id = ac_entey.ACEacid
               ac_info = self.db.query(Activity).filter(Activity.ACid == ac_id,
                                                     Activity.ACstatus >= number,Activity.ACvalid == 1).all()
               url = self.db.query(ActivityImage).filter(ActivityImage.ACIacid == ac_id).limit(1).all()
               if ac_info:
                   if url :
                    ret_activity.append(ACmodelHandler.ac_Model_simply(ac_info[0],url[0].ACIurl))
            ac_mentrys = self.db.query(Activity).filter(Activity.ACsponsorid == u_id,Activity.ACvalid == 1,
                                                        Activity.ACstatus >= number).all()
            for ac_mentry in ac_mentrys:
                ac_id = ac_mentry.ACid
                url = self.db.query(ActivityImage).filter(ActivityImage.ACIacid == ac_id).limit(1).all()
                if url:
                    ret_activity.append(ACmodelHandler.ac_Model_simply(ac_mentry, url[0].ACIurl))
        else:
            for ac_entey in ac_enteys:
                ac_id = ac_entey.ACEacid
                ac_info = self.db.query(Activity).filter(Activity.ACid == ac_id,
                                                         Activity.ACstatus == number, Activity.ACvalid == 1).all()
                url = self.db.query(ActivityImage).filter(ActivityImage.ACIacid == ac_id).limit(1).all()
                if ac_info:
                    if url:
                        ret_activity.append(ACmodelHandler.ac_Model_simply(ac_info[0], url[0].ACIurl))
            ac_mentrys = self.db.query(Activity).filter(Activity.ACsponsorid == u_id, Activity.ACvalid == 1,
                                                        Activity.ACstatus == number).all()
            for ac_mentry in ac_mentrys:
                ac_id = ac_mentry.ACid
                url = self.db.query(ActivityImage).filter(ActivityImage.ACIacid == ac_id).limit(1).all()
                if url:
                    ret_activity.append(ACmodelHandler.ac_Model_simply(ac_mentry, url[0].ACIurl))
        return ret_activity


    def get_e_appointment(self,u_id,number):
        ret_e_appointment = []
        ap_e_info = []
        if number == 0:
           ap_e_entrys = self.db.query(AppointEntry).filter(AppointEntry.AEregisterID == u_id,
                                                         AppointEntry.AEvalid == True).all()
        else :

            ap_e_entrys = self.db.query(AppointEntry).filter(AppointEntry.AEregisterID == u_id,
                                                                 AppointEntry.AEvalid == True,
                                                                 AppointEntry.AEchoosed ==True).all()
        if number == 2:
            for ap_e_entry in ap_e_entrys:
                ap_id = ap_e_entry.AEapid
                try :
                   ap_e_info = self.db.query(Appointment).filter(Appointment.APid == ap_id,Appointment.APstatus >= number,Appointment.APstatus <= number+1).all()
                except Exception,e:
                    print e
                if ap_e_info:
                    ret_e_appointment.append(APmodelHandler.ap_Model_simply_one(ap_e_info[0],u_id))
        else:
            for ap_e_entry in ap_e_entrys:
                ap_id = ap_e_entry.AEapid
                try :
                   ap_e_info = self.db.query(Appointment).filter(Appointment.APid == ap_id,Appointment.APstatus == number).all()
                except Exception,e:
                    print e
                if ap_e_info:
                    ret_e_appointment.append(APmodelHandler.ap_Model_simply_one(ap_e_info[0],u_id))

        return ret_e_appointment

    def get_my_appointment(self,u_id,number):
        ap_my_entrys = []
        ret_my_appointment =[]
        if number == 2:
            try:
                ap_my_entrys = self.db.query(Appointment).filter(Appointment.APsponsorid == u_id,Appointment.APstatus >= number,Appointment.APstatus <= number+1).all()
            except Exception,e:
                print e
            ret_my_appointment = APmodelHandler.ap_Model_simply(ap_my_entrys, ret_my_appointment,u_id)
        else:
            try:
                ap_my_entrys = self.db.query(Appointment).filter(Appointment.APsponsorid == u_id,Appointment.APstatus == number).all()
            except Exception,e:
                print e
            ret_my_appointment = APmodelHandler.ap_Model_simply(ap_my_entrys, ret_my_appointment,u_id)
        return ret_my_appointment

    def finnish_activity_register(self,u_id,ac_id):     #结束活动报名
        try:
            exist =self.db.query(Activity).filter(Activity.ACid == ac_id, Activity.ACsponsorid == u_id).one()
            if exist.ACvalid  == 1:
                if exist.ACstatus == 0:
                    exist.ACstatus =1
                    self.db.commit()
                    self.retjson['code'] = '10972'
                    self.retjson['contents'] = '成功结束活动报名'
                else :
                    self.retjson['code'] = '10973'
                    self.retjson['contents'] = '此活动状态不可结束报名'
            else :
                self.retjson['code'] = '10974'
                self.retjson['contents'] = '此活动已被取消'
        except Exception,e:
            print e
            self.retjson['code'] = '10971'
            self.retjson['contents'] = '此活动不是你发起的，无法操作'

    def finish_avtivity(self,u_id,ac_id):     #结束活动
        try:
            exist = self.db.query(Activity).filter(Activity.ACid == ac_id, Activity.ACsponsorid == u_id).one()
            if exist.ACvalid == 1:
                if exist.ACstatus == 1:
                    exist.ACstatus = 2
                    self.db.commit()
                    self.retjson['code'] = '10962'
                    self.retjson['contents'] = '成功结束活动'
                else:
                    self.retjson['code'] = '10963'
                    self.retjson['contents'] = '此活动状态不可结束活动'
            else:
                self.retjson['code'] = '10964'
                self.retjson['contents'] = '此活动已被取消'
        except Exception, e:
            print e
            self.retjson['code'] = '10961'
            self.retjson['contents'] = '此活动不是你发起的，无法操作'

    def evaluate_appointment(self,type,appointment,appointmentinfo,comment,score): # 对约拍进行评价
        '''
        
        Args:
            type: 约拍的类型 
            appointmentinfo: 具体的某个约拍 
            comment: 评论
            score: 评分

        Returns:

        '''
        if type == 0:
            if appointmentinfo.AImcomment:
                self.retjson['code'] = '10981'
                self.retjson['contents'] = '您已经评价过该约拍，不可再次评价'
            else:
                appointmentinfo.AImcomment = comment
                appointmentinfo.AImscore = score
                appointment.APstatus+=1
                self.db.commit()
                self.retjson['code'] = '10908'
                self.retjson['contents'] = '评价成功'
        if type == 1:
            if appointmentinfo.AIpcomment:
                self.retjson['code'] = '10981'
                self.retjson['contents'] = '您已经评价过该约拍，不可再次评价'
            else:
                appointmentinfo.AIpcomment = comment
                appointmentinfo.AIpscore = score
                appointment.APstatus += 1
                self.db.commit()
                self.retjson['code'] = '10908'
                self.retjson['contents'] = '评价成功'

    def get_e_appointment_not_evaluate(self,u_id):     # 获取我的参与的未评价的约拍
        ret_e_appointment = []
        ap_e_info = []
        ap_e_entrys = self.db.query(AppointEntry).filter(AppointEntry.AEregisterID == u_id,
                                                         AppointEntry.AEvalid == True,
                                                         AppointEntry.AEchoosed == True).all()
        for ap_e_entry in ap_e_entrys:
            try:
                item = self.db.query(AppointmentInfo).filter(AppointmentInfo.AIappoid == ap_e_entry.AEapid).one()
                if item.AIpid == int(u_id):
                    if not AppointmentInfo.AIpcomment:
                        ap_e_info = self.db.query(Appointment).filter(Appointment.APid == ap_e_entry.AEapid,
                                                                     ).all()
                        ret_e_appointment.append(APmodelHandler.ap_Model_simply_one(ap_e_info[0], u_id))
                if item.AImid == int(u_id):
                    if not AppointmentInfo.AImcomment:
                        ap_e_info = self.db.query(Appointment).filter(Appointment.APid == ap_e_entry.AEapid,
                                                                     ).all()
                        ret_e_appointment.append(APmodelHandler.ap_Model_simply_one(ap_e_info[0], u_id))

            except Exception, e:
                print e
        return ret_e_appointment

    def get_my_appointment_not_evaluate(self,u_id):    # 获取我发布的未评价的约拍
        ap_my_entrys = []
        ret_my_appointment = []
        try:
            ap_my_entrys = self.db.query(Appointment).filter(Appointment.APsponsorid == u_id,
                                                             Appointment.APstatus >= 2,
                                                             Appointment.APstatus <= 3).all()
        except Exception, e:
            print e
        for ap_my_entry in ap_my_entrys:
            try:
                item = self.db.query(AppointmentInfo).filter(AppointmentInfo.AIappoid == ap_my_entry.APid).one()
                if item.AIpid == int(u_id):
                    if not item.AIpcomment:
                        ret_my_appointment.append(APmodelHandler.ap_Model_simply_one(ap_my_entry, u_id))
                if item.AImid == int(u_id):
                    if not item.AImcomment:
                        ret_my_appointment.append(APmodelHandler.ap_Model_simply_one(ap_my_entry, u_id))
            except Exception, e:
                print e

        return ret_my_appointment

    def get_e_appointment_evaluate(self, u_id):   #  获取我参加的的已评价了的约拍
        ret_e_appointment = []
        ap_e_info = []
        ap_e_entrys = self.db.query(AppointEntry).filter(AppointEntry.AEregisterID == u_id,
                                                         AppointEntry.AEvalid == True,
                                                         AppointEntry.AEchoosed == True).all()
        for ap_e_entry in ap_e_entrys:
            try:
                item = self.db.query(AppointmentInfo).filter(AppointmentInfo.AIappoid == ap_e_entry.AEapid).one()
                if item.AIpid == int(u_id):
                    if AppointmentInfo.AIpcomment:
                        ap_e_info = self.db.query(Appointment).filter(Appointment.APid == ap_e_entry.AEapid,
                                                                      ).all()
                        ret_e_appointment.append(APmodelHandler.ap_Model_simply_one(ap_e_info[0], u_id))
                if item.AImid == int(u_id):
                    if AppointmentInfo.AImcomment:
                        ap_e_info = self.db.query(Appointment).filter(Appointment.APid == ap_e_entry.AEapid,
                                                                      ).all()
                        ret_e_appointment.append(APmodelHandler.ap_Model_simply_one(ap_e_info[0], u_id))

            except Exception, e:
                print e
        return ret_e_appointment

    def get_my_appointment_evaluate(self,u_id):    # 获取我发布的已评价的约拍
        ap_my_entrys = []
        ret_my_appointment = []
        try:
            ap_my_entrys = self.db.query(Appointment).filter(Appointment.APsponsorid == u_id,
                                                             Appointment.APstatus >= 3,
                                                             Appointment.APstatus <= 4).all()
        except Exception, e:
            print e
        for ap_my_entry in ap_my_entrys:
            try:
                item = self.db.query(AppointmentInfo).filter(AppointmentInfo.AIappoid == ap_my_entry.APid).one()
                if item.AIpid == int(u_id):
                    if item.AIpcomment:
                        ret_my_appointment.append(APmodelHandler.ap_Model_simply_one(ap_my_entry, u_id))
                if item.AImid == int(u_id):
                    if item.AImcomment:
                        ret_my_appointment.append(APmodelHandler.ap_Model_simply_one(ap_my_entry, u_id))
            except Exception, e:
                print e

        return ret_my_appointment
