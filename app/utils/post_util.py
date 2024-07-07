from app.models.post_models import find_post
from app.models.users_models import find_user_by_id
from app.schemas.users_schema import UserGetInfo


def default_post_info(post_list: list):

    result = []

    for post_id in post_list:
        item_info = find_post(post_id)
        result.append(item_info)

    for post in result:
        if(post['borrow'] == True):
            writer_id = post['borrower_uuid']
        else:
            writer_id = post['lender_uuid']
        writer_info, message = find_user_by_id(UserGetInfo(id=writer_id))
        post['nickname'] = writer_info['nickname']
        post['profile_image'] = writer_info['profile_image']
        post['writer_id'] = writer_id
        post['post_id'] = post['_id']
        del post['_id']
        
    return result