from app.utils.chat_util import default_chat_info
from app.utils.post_util import default_post_info


def delete_sensitive_data(user_info: dict):
    del user_info['pw']
    del user_info['salt']
    del user_info['type']
    del user_info['token']


def default_user_info(user_info: dict):
    
    delete_sensitive_data(user_info)

    user_info['borrow_list'] = default_post_info(user_info['borrow_list'])
    user_info['lend_list'] = default_post_info(user_info['lend_list'])
    user_info['posts'] = default_post_info(user_info['posts'])

    user_info['borrow_count'] = len(user_info['borrow_list'])
    user_info['lend_count'] = len(user_info['lend_list'])

    user_info['chat_list'] = default_chat_info(user_info['chat_list'], user_info['_id'])

    user_info['female'] = bool(user_info['female'])

    return user_info