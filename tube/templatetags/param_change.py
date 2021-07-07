from django import template

register = template.Library()

def param(request, key, value):
    copied = request.GET.copy()
    copied[key] = value

    return "?" + copied.urlencode()


@register.inclusion_tag("tube/paginator.html")
def generate_pagelink(request, key, start, end, now):
    PAGE_RANGE = 3

    start = int(start)
    end = int(end)
    now = int(now)

    pages = []

    # ここで最初のページの生成、リンクは今のページと判定
    if now != start:
        pages.append({"name": "Prev", "link": param(request, key, start)})
    else:
        pages.append({"name": "Prev", "link": ""})

    for i in range(now - PAGE_RANGE, now + PAGE_RANGE + 1):

        # いまアクセスしているページはリンクなしでアペンド、次のループへ
        if i == now:
            pages.append({"name": str(i), "link": ""})
            continue

        # 範囲外なら次のループへ(アーリーリターン)
        if i <= start or end <= i:
            continue

        pages.append({"name": str(i), "link": param(request, key, i)})
        print(pages)

    # ここで最後のページの生成、リンクは今のページと判定
    if now != end:
        pages.append({"name": "Next", "link": param(request, key, end)})
    else:
        pages.append({"name": "End", "link": ""})

    return {"pages": pages}


@register.inclusion_tag("tube/paginator_comment.html")
def generate_pagelink_comment(request, key, start, end, now):
    PAGE_RANGE = 3

    start = int(start)
    end = int(end)
    now = int(now)

    pages = []

    # ここで最初のページの生成
    if now != start:
        pages.append({"name": "1"})
    else:
        pass


    for i in range(now - PAGE_RANGE, now + PAGE_RANGE + 1):

        if i == now:
            pages.append({"name": str(i), "now_flag":True})
            continue

        # 範囲外なら次のループへ(アーリーリターン)
        if i <= start or end <= i:
            continue

        pages.append({"name": str(i)})
        print(pages)

        # ここで最後のページの生成
    if now != end:
        pages.append({"name": str(end)})
    else:
        pass

    return {"pages": pages}

'''
def url_replace(request, field, value):
    dict_           = request.GET.copy()
    dict_[field]    = value
    return dict_.urlencode()
'''