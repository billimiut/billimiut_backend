from app.utils.chat_util import default_chat_info
from app.utils.post_util import default_post_info

from app.models.post_models import get_borrow_or_lend_list,get_posts_by_user_id
from app.models.chat_models import get_chat_by_user_id

def delete_sensitive_data(user_info: dict):
    if 'pw' in user_info:
        del user_info['pw']
    if 'salt' in user_info:
        del user_info['salt']
    del user_info['type']
    if 'token' in user_info:
        del user_info['token']

    if 'borrow_list' in user_info:
        del user_info['borrow_list']
    if 'lend_list' in user_info:
        del user_info['lend_list']
    if 'posts' in user_info:
        del user_info['posts']
    if 'chat_list' in user_info:
        del user_info['chat_list']


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


def default_user_info(user_info: dict):
    if user_info is None:
        return None

    delete_sensitive_data(user_info)

    # 1. lend_list를 불러온다
    user_info['lend_list'] = get_borrow_or_lend_list(user_info['_id'], False)
    user_info['lend_list'] = default_post_info(user_info['lend_list'])
    # 2. borrow_list를 불러온다
    user_info['borrow_list'] = get_borrow_or_lend_list(user_info['_id'], True)
    user_info['borrow_list'] = default_post_info(user_info['borrow_list'])    
    # 3. chat_list를 불러온다
    user_info['chat_list'] = get_chat_by_user_id(user_info['_id'])
    user_info['chat_list'] = default_chat_info(user_info['chat_list'], user_info['_id'])
    # 4. posts를 불러온다
    user_info['posts'] = get_posts_by_user_id(user_info['_id'])
    user_info['posts'] = default_post_info(user_info['posts'])    
    # 5. 기타 기존에 사용했던 설정 추가
    user_info['borrow_count'] = len(user_info['borrow_list'])
    user_info['lend_count'] = len(user_info['lend_list'])
    user_info['female'] = bool(user_info['female'])    
    # 일단 기존 default_@@_info를 사용하려고 list를 불러오는 과정에서 id만 받아오게 했음. 이거는 추후에 수정해야함

    return user_info