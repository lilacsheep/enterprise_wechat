#!/usr/bin/python3
# -*- coding: utf-8 -*-
import requests
from urllib.parse import urljoin
import logging
import json
import os
from wechat.chat_message import ChatMessage


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class IllegalUserParameters(Exception):
    pass


class WeChatInitError(Exception):
    pass


class WeChatApiError(Exception):
    pass


class WeChatApp:

    def __init__(self, corp_id, secret, agent_id):
        self.api_url = 'https://qyapi.weixin.qq.com'
        self.corp_id, self.secret, self.agent_id = corp_id, secret, agent_id
        self.chat = ChatMessage(self)
        logging.info('初始化企业微信App信息.......')

        statue_code, message = self.get_app_info()
        if statue_code == 200:
            self.name = message['name']
            logging.info('企业微信App名称: {}'.format(self.name))

            self.user_id_set = {obj['userid'] for obj in message['allow_userinfos']['user']}
            logging.info('企业微信App使用人: {}'.format(','.join(list(self.user_id_set))))

            self.party_id_list = [] if 'allow_partys' not in message else message['allow_partys']['partyid']
            if self.party_id_list:
                logging.info('企业微信App部门: {}'.format(','.join([str(i) for i in self.party_id_list])))

            self.tag_id_list = [] if 'allow_tags' not in message else message['allow_tags']['tagid']
            if self.tag_id_list:
                logging.info('企业微信App标签: {}'.format(','.join(self.tag_id_list)))

            self.redirect_domain = message['redirect_domain']
            logging.info('企业微信App绑定域名: {}'.format(self.redirect_domain))

            self.description = message['description']
            logging.info('企业微信App描述: {}'.format(message['description']))

        else:
            raise WeChatInitError(message)

    @property
    def access_token(self):
        path = '/cgi-bin/gettoken'
        url = urljoin(self.api_url, path)
        params = {
            'corpid': self.corp_id,
            'corpsecret': self.secret
        }

        s = requests.get(url, params=params)
        result = s.json()
        s.close()
        return result['access_token']

    def _post(self, path: str, data: str, params=None, **kwargs):
        """
        :param path: 路径
        :param data: post 请求参数，企业微信要求为Json字符串
        :param params: Get请求入参，默认None 传入类型dict
        :param kwargs: Request库请求参数
        :return: status_code, message 如果报错返回 -1， 错误信息
        """
        try:
            url = urljoin(self.api_url, path)
            r = requests.post(url, data, params=params, **kwargs)
            status_code = r.status_code
            message = r.json()
            r.close()
            if message["errcode"] != 0:
                raise WeChatApiError(message['errmsg'])
            return status_code, message
        except Exception as error:
            return -1, error

    def _get(self, path: str, params=None, **kwargs):
        """
        :param path: 路径
        :param params: Get请求入参，默认None 传入类型dict
        :param kwargs: Request库请求参数
        :return: status_code, message 如果报错返回 -1， 错误信息
        """
        try:
            url = urljoin(self.api_url, path)
            r = requests.get(url, params=params, **kwargs)
            status_code = r.status_code
            message = r.json()
            r.close()
            if message["errcode"] != 0:
                raise WeChatApiError(message['errmsg'])
            return status_code, message
        except Exception as error:
            return -1, error

    def _message_user(self, touser=None, toparty=None, totag=None):
        """
        具体帮助查询 https://work.weixin.qq.com/api/doc#90001/90143/90372/%E6%96%87%E6%9C%AC%E6%B6%88%E6%81%AF
        :param touser: 接受参数类型 字符串或数组，发送全员信息时候传入@all，消息接收者，多个接收者用‘|’分隔，最多支持1000个
        :param toparty: 部门ID列表，多个接收者用‘|’分隔，最多支持100个。当touser为@all时忽略本参数
        :param totag: 标签ID列表，多个接收者用‘|’分隔，最多支持100个。当touser为@all时忽略本参数
        :return:
        """
        data = {}

        if touser or toparty or totag:
            if isinstance(touser, list):
                if len(touser) > 100:
                    raise IllegalUserParameters('touser Must be less than 1000')
                data['touser'] = '|'.join(touser)
            elif isinstance(touser, str):
                if len(touser.split('|')) > 1000:
                    raise IllegalUserParameters('touser Must be less than 1000')
                data['touser'] = touser

            if isinstance(toparty, list):
                if len(toparty) > 100:
                    raise IllegalUserParameters('toparty Must be less than 100')
                data['toparty'] = '|'.join(toparty)
            elif isinstance(totag, str):
                if len(toparty.split('|')) > 100:
                    raise IllegalUserParameters('toparty Must be less than 100')
                data['toparty'] = toparty

            if isinstance(totag, list):
                if len(totag) > 100:
                    raise IllegalUserParameters('totag Must be less than 100')
                data['totag'] = '|'.join(totag)
            elif isinstance(totag, str):
                if len(totag.split('|')) > 100:
                    raise IllegalUserParameters('totag Must be less than 100')
                data['totag'] = totag
            return data
        else:
            raise IllegalUserParameters('touser, totag, toparty All empty')

    def _message_send(self, data: dict, **kwargs):
        """
        企业微信应用发送消息时使用的接口
        :param data: 需要序化的dict
        :param kwargs: Request库请求参数
        :return:
        """
        path = 'cgi-bin/message/send?access_token={}'.format(self.access_token)
        status_code, message = self._post(path, data=json.dumps(data))
        if status_code == -1:
            logger.error('发送信息失败！失败信息{}'.format(message))
        else:
            logger.debug('发送信息状态{}, 结果: {}'.format(status_code, message))

    def send_text_message(self, content, to_user=None, toparty=None, totag=None):
        """
        具体帮助查询 https://work.weixin.qq.com/api/doc#90001/90143/90372/%E6%96%87%E6%9C%AC%E6%B6%88%E6%81%AF
        :param to_user: 接受参数类型 字符串或数组，发送全员信息时候传入@all，消息接收者，多个接收者用‘|’分隔，最多支持1000个
        :param content: 发送信息内容
        :param toparty: 部门ID列表，多个接收者用‘|’分隔，最多支持100个。当touser为@all时忽略本参数
        :param totag: 标签ID列表，多个接收者用‘|’分隔，最多支持100个。当touser为@all时忽略本参数
        :return:
        """
        data = {'agentid': self.agent_id, 'msgtype': 'text', 'text': {'content': content}, "safe": 0}

        user_data = self._message_user(to_user, toparty, totag)
        data.update(**user_data)
        self._message_send(data)

    def send_card_message(self, title, description, url, btntxt=None, to_user=None, toparty=None, totag=None):
        """
        发送卡片消息
        具体帮助查询 https://work.weixin.qq.com/api/doc#90001/90143/90372/%E6%96%87%E6%9C%AC%E5%8D%A1%E7%89%87%E6%B6%88%E6%81%AF
        :param title: 卡片标题
        :param description: 描述，不超过512个字节，超过会自动截断
        :param url: 点击后跳转的链接
        :param btntxt: 按钮文字。 默认为“详情”， 不超过4个文字，超过自动截断。
        :param to_user: 同Text message
        :param toparty: 同Text message
        :param totag: 同Text message
        :return:
        """
        data = {
            'agentid': self.agent_id, 'msgtype': 'textcard',
            'textcard': {
                'title': title, 'description': description, 'url': url, 'btntxt': btntxt,
            }, "safe": 0}
        user_data = self._message_user(to_user, toparty, totag)
        data.update(**user_data)
        self._message_send(data)

    def send_file_message(self, media_id, to_user=None, toparty=None, totag=None):
        """
        发送文件消息
        具体帮助查看 https://work.weixin.qq.com/api/doc#90001/90143/90372/%E6%96%87%E4%BB%B6%E6%B6%88%E6%81%AF
        :param media_id: 文件id，可以调用上传临时素材接口获取
        :param to_user: 同Text message
        :param toparty: 同Text message
        :param totag: 同Text message
        :return:
        """
        data = {
            'agentid': self.agent_id,
            'msgtype': 'file',
            'file': {
                "media_id": media_id
            },
            "safe": 0}

        user_data = self._message_user(to_user, toparty, totag)
        data.update(**user_data)
        self._message_send(data)

    def get_app_info(self):
        """
        获取应用信息
        :return:
        """
        path = '/cgi-bin/agent/get'
        params = {
            'access_token': self.access_token,
            'agentid': self.agent_id
        }
        return self._get(path, params)

    def get_department(self, department_id=None):
        """
        :param department_id: 部门id。获取指定部门及其下的子部门。 如果不填，默认获取全量组织架构
        :return:
        """
        path = '/cgi-bin/department/list'
        params = {
            'access_token': self.access_token,
        }
        if department_id is not None:
            params['id'] = department_id
        return self._get(path, params)

    def get_department_user(self, department_id):
        """
        help: https://work.weixin.qq.com/api/doc#90000/90135/90200
        :param department_id:
        :return:
        """
        path = '/cgi-bin/user/list'
        params = {
            'access_token': self.access_token,
            'department_id': department_id
        }
        return self._get(path, params)

    def get_tags_user(self, tag_id):
        """
        help: https://work.weixin.qq.com/api/doc#90000/90135/90213
        :param tag_id:
        :return:
        """
        path = "/cgi-bin/tag/get"
        params = {
            'access_token': self.access_token,
            'tagid': tag_id
        }
        return self._get(path, params)

    def get_user(self, user_id):
        path = '/cgi-bin/user/get'
        params = {
            'access_token': self.access_token,
            'userid': user_id
        }
        return self._get(path, params)

    def upload_media_file(self, file_path):
        """
        上传临时文件
        具体帮助查询 https://work.weixin.qq.com/api/doc#90001/90143/90389
        :param file_path:
        :return:
        """
        path = "/cgi-bin/media/upload"
        params = {
            'access_token': self.access_token,
            'type': 'file'
        }
        if os.path.exists(file_path):
            try:
                url = urljoin(self.api_url, path)
                r = requests.post(url,
                                  params=params,
                                  files=[('files', (os.path.split(file_path)[-1], open(file_path, 'rb')))])
                status_code = r.status_code
                message = r.json()
                r.close()
                return status_code, message
            except Exception as error:
                return -1, error
        else:
            return -1, "文件未找到"

