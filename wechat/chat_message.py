#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import json

logger = logging.getLogger(__name__)


class ChatMessage:
    """
    只允许企业自建应用调用，且应用的可见范围必须是根部门；
    chatid 所代表的群必须是该应用所创建；
    每企业消息发送量不可超过2万人次/分，不可超过20万人次/小时（若群有100人，每发一次消息算100人次）；
    每个成员在群中收到的应用消息不可超过200条/分，1万条/天，超过会被丢弃（接口不会报错）；
    具体帮助查询 https://work.weixin.qq.com/api/doc/#90000/90135/90248
    """

    def __init__(self, app):
        self.app = app

    def create_chat(self, name, owner, userlist: list, chatid=None) -> str:
        """
        帮助链接: https://work.weixin.qq.com/api/doc/#90000/90135/90245
        :param name: 群聊名，最多50个utf8字符，超过将截断
        :param owner: 指定群主的id
        :param userlist: 群成员id列表。至少2人，至多500人
        :param chatid: 群聊的唯一标志，不能与已有的群重复；字符串类型，最长32个字符。只允许字符0-9及字母a-zA-Z。如果不填，系统会随机生成群id
        :return:
        """
        data = {
            "name": name,
            "owner": owner,
            "userlist": userlist,
        }
        if isinstance(chatid, str):
            data["chatid"] = chatid

        path = "/cgi-bin/appchat/create?access_token={}".format(self.app.access_token)
        status_code, message = self.app._post(path, data=json.dumps(data))
        if status_code == -1:
            logger.error('创建群聊失败！失败信息{}'.format(message))
        else:
            logger.warning('创建群聊状态{}, 结果: {}'.format(status_code, message))
            if message['errcode'] == 0:
                return message['chatid']

    def modify_chat(self, chatid, name=None, owner=None, add_user_list=None, del_user_list=None):
        """
        帮助链接： https://work.weixin.qq.com/api/doc/#90000/90135/90246
        :param chatid: 群聊id
        :param name: 新的群聊名。若不需更新，请忽略此参数。最多50个utf8字符，超过将截断
        :param owner: 新群主的id。若不需更新，请忽略此参数
        :param add_user_list: 添加成员的id列表
        :param del_user_list: 踢出成员的id列表
        :return:
        """
        data = {
            "chatid": chatid,
            "name": "NAME",
            "owner": "userid2",
            "add_user_list": ["userid1", "userid2", "userid3"],
            "del_user_list": ["userid3", "userid4"]
        }
        if isinstance(name, str):
            data['name'] = name
        if isinstance(owner, str):
            data['owner'] = owner
        if isinstance(add_user_list, list):
            data['add_user_list'] = add_user_list
        if isinstance(del_user_list, list):
            data['del_user_list'] = del_user_list
        path = "/cgi-bin/appchat/update?access_token={}".format(self.app.access_token)
        status_code, message = self.app._post(path, data=json.dumps(data))
        if status_code == -1:
            logger.error('修改群聊失败！失败信息{}'.format(message))
        else:
            logger.warning('修改群聊状态{}, 结果: {}'.format(status_code, message))

    def _message_send(self, data: dict, **kwargs):
        """
        企业微信应用发送消息时使用的接口
        :param data: 需要序化的dict
        :param kwargs: Request库请求参数
        :return:
        """
        path = 'cgi-bin/appchat/send?access_token={}'.format(self.app.access_token)
        status_code, message = self.app._post(path, data=json.dumps(data))
        if status_code == -1:
            logger.error('发送信息失败！失败信息{}'.format(message))
        else:
            logger.debug('发送信息状态{}, 结果: {}'.format(status_code, message))

    def send_text_message(self, chatid, content):
        """
        :param chatid: 	群聊id
        :param content: 发送信息内容
        :return:
        """
        data = {'chatid': chatid, 'msgtype': 'text', 'text': {'content': content}, "safe": 0}
        self._message_send(data)

    def send_card_message(self, chatid, title, description, url, btntxt=None):
        """
        发送卡片消息
        :param chatid: 群聊id
        :param title: 卡片标题
        :param description: 描述，不超过512个字节，超过会自动截断
        :param url: 点击后跳转的链接
        :param btntxt: 按钮文字。 默认为“详情”， 不超过4个文字，超过自动截断。
        :return:
        """
        data = {
            'chatid': chatid, 'msgtype': 'textcard',
            'textcard': {
                'title': title, 'description': description, 'url': url, 'btntxt': btntxt,
            }, "safe": 0}
        self._message_send(data)

    def send_file_message(self, chatid, media_id):
        """
        发送文件消息
        :param chatid: 群聊id
        :param media_id: 文件id，可以调用上传临时素材接口获取
        :return:
        """
        data = {
            'chatid': chatid,
            'msgtype': 'file',
            'file': {
                "media_id": media_id
            },
            "safe": 0}
        self._message_send(data)

    def send_markdown(self, chatid, content):
        data = {
            "chatid": chatid,
            "msgtype": "markdown",
            "markdown": {"content": content}
        }
        self._message_send(data)


