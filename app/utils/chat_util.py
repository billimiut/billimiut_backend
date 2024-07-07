from app.models.chat_models import find_chat
from app.models.users_models import find_user_by_id
from app.schemas.users_schema import UserGetInfo

import datetime

def default_chat_info(chat_list: list, user_id: str):

    result = []

    for chat_id in chat_list:
        chat_info = find_chat(chat_id)
        user = chat_info['user']
        post_id = chat_id.split('-')[0]
        
        if user[0] == user_id:
            neighbor_id = user[1]
        else:
            neighbor_id = user[0]

        neighbor_info, find_message = find_user_by_id(UserGetInfo(id = neighbor_id))
        neighbor_nickname = neighbor_info['nickname']
        neighbor_profile = neighbor_info['profile_image']

        message = sorted(chat_info['message'], key=lambda x: datetime.datetime.fromisoformat(x['time']))
        last_message = message[-1]['message']
        last_message_time = message[-1]['time']

        default_data = {
            "neighbor_id": neighbor_id,
            "post_id": post_id,
            "neighbor_nickname": neighbor_nickname,
            "neighbor_profile": neighbor_profile,
            "last_message": last_message,
            "last_message_time": last_message_time
        }

        result.append(default_data)

    return result
