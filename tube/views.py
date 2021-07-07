from rest_framework import status,views,response

from django.shortcuts import render, redirect

from django.db.models import Q,Count

from django.http.response import JsonResponse

from django.template.loader import render_to_string

from django.core.paginator import Paginator

from django.conf import settings

#TIPS:ログイン状態かチェックする。ビュークラスに継承元として指定する(多重継承なので順番に注意)。未ログインであればログインページへリダイレクト。
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from .models import Video,Category,VideoComment,MyList,History,GoodVideo,BadVideo

from users.models import CustomUser,FollowUser,BlockUser


from .serializer import VideoSerializer,VideoEditSerializer,VideoCommentSerializer,MyListSerializer,HistorySerializer,RateSerializer,GoodSerializer,BadSerializer,IconSerializer,FollowUserSerializer,BlockUserSerializer,UserInformationSerializer

DEFAULT_VIDEO_AMOUNT = 10
COMMENTS_AMOUNT_PAGE = 10

#python-magicで受け取ったファイルのMIMEをチェックする。
#MIMEについては https://developer.mozilla.org/ja/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types を参照。

from PIL import Image
import qrcode
from io import BytesIO
import base64

import magic
ALLOWED_MIME   = ["video/mp4"]

# アップロードの上限
LIMIT_SIZE     = 200 * 1000 * 1000

SEARCH_AMOUNT_PAGE  = 20

#トップページ
class IndexView(views.APIView):

    def get(self, request,*args, **kwargs):

        #新着順
        latests = Video.objects.all().order_by("-dt")[:DEFAULT_VIDEO_AMOUNT]

        if request.user.is_authenticated:

            #最近見た動画
            histories       = History.objects.filter(user=request.user.id).exclude(target__user__blocked=request.user.id).order_by("-dt")[:DEFAULT_VIDEO_AMOUNT]

            #フォローユーザーの動画
            follows         = Video.objects.filter(user__followed=request.user.id).order_by("-dt")[:DEFAULT_VIDEO_AMOUNT]

            #ブロックしたユーザー(これはいらない)
            #blockusers      = Video.objects.filter(user__blocked=request.user.id).order_by("-dt")[:DEFAULT_VIDEO_AMOUNT]
            #ブロックしていないユーザーの新着動画(TODO:ここは新着順のlatestsを上書き)
            #not_blockusers  = Video.objects.exclude(user__blocked=request.user.id).order_by("-dt")[:DEFAULT_VIDEO_AMOUNT]


            #新着順(ブロックしたユーザーは除外)
            latests         = Video.objects.exclude(user__blocked=request.user.id).order_by("-dt")[:DEFAULT_VIDEO_AMOUNT]




            #=============以下マイリス数、コメント数の属性値を付与する===========================


            #1対多で繋がっているモデルからコメント数、マイリスト数を表示することができる。
            #参照元: https://docs.djangoproject.com/ja/3.2/topics/db/aggregation/

            #複数の1対多をカウントする場合、distinct=Trueをセットしないとカウントがおかしくなる
            #https://stackoverflow.com/questions/6795202/django-count-in-multiple-annotations

            latests         = Video.objects.annotate(num_comments=Count("videocomment",distinct=True),num_mylists=Count("mylist",distinct=True)).exclude(user__blocked=request.user.id).order_by("-dt")[:DEFAULT_VIDEO_AMOUNT]

            for latest in latests:
                print("=============")
                print("コメント数", latest.num_comments)
                print("マイリス数", latest.num_mylists)
                print("=============")
            
            #これで動画一覧表示時に、マイリス数とコメント数をセットで表示できる。

        else:
            histories       = False
            follows         = False
            #blockusers      = False
            #not_blockusers  = False

        context = {"latests": latests,
                   "histories":histories,
                   "follows":follows,
                   #"blockusers":blockusers,
                   #"not_blockusers": not_blockusers,
                   }

        return render(request, "tube/index.html", context)

index = IndexView.as_view()

#アップロードページ
class UploadView(LoginRequiredMixin,views.APIView):

    def get(self,request, *args, **kwargs):

        categories = Category.objects.all()
        context = {"categories": categories}

        return render(request, "tube/upload.html", context)


    def post(self, request, *args, **kwargs):

        print(request.data)

        request.data["user"]    = request.user.id
        serializer              = VideoSerializer(data=request.data)
        mime_type               = magic.from_buffer(request.FILES["movie"].read(1024), mime=True)

        print(request.data["movie"].size)
        print(type(request.data["movie"].size))

        if request.FILES["movie"].size >= LIMIT_SIZE:
            mb = str(LIMIT_SIZE / 1000000)

            json = {"error": True,
                    "message": "The maximum file size is " + mb + "MB"}

            return JsonResponse(json)

        if mime_type not in ALLOWED_MIME:
            mime = str(ALLOWED_MIME)
            json = {"error": True,
                    "message": "The file you can post is " + mime + "."}

            return JsonResponse(json)

        if serializer.is_valid():
            serializer.save()
        else:
            json    = { "error":True,
                        "message":"入力内容に誤りがあります。" }
            return JsonResponse(json)

        json    = { "error":False,
                    "message":"アップロード完了しました。" }

        return JsonResponse(json)


upload = UploadView.as_view()



#検索結果表示ページ
class SearchView(views.APIView):

    def get(self, request, *args, **kwargs):

        query   = Q()
        page    = 1

        if "word" in request.GET:

            word_list = request.GET["word"].replace("　", " ").split(" ")
            for w in word_list:
                query &= Q(Q(title__icontains=w) | Q(description__icontains=w))

        if "page" in request.GET:
            page = request.GET["page"]

        
        #TODO:ここでログインしていれば、ブロックユーザーを除外した検索をする。
        if request.user.is_authenticated:
            videos = Video.objects.filter(query).exclude(user__blocked=request.user.id).order_by("-dt")
        else:
            videos = Video.objects.filter(query).order_by("-dt")
            
        amount = len(videos)

        videos_paginator = Paginator(videos, SEARCH_AMOUNT_PAGE)
        videos           = videos_paginator.get_page(page)

        context = {"videos": videos,
                   "amount": amount}

        return render(request, "tube/search.html", context)

search = SearchView.as_view()


#動画個別ページ
class SingleView(views.APIView):

    def get(self,request, video_pk, *args, **kwargs):

        video = Video.objects.filter(id=video_pk).first()

        #Todo:F5で再生回数水増し可能。
        video.views = video.views + 1
        video.save()

        if request.user.is_authenticated:
            print("認証済みユーザーです")

            history = History.objects.filter(user=request.user.id, target=video_pk).first()

            if history:
                print("存在する場合の処理")
                history.views   = history.views + 1
                history.dt      = timezone.now()
                history.save()
            else:
                print("履歴に存在しない場合の処理")
                data        = { "target":video_pk,
                                "user":request.user.id,}
                serializer  = HistorySerializer(data=data)

                if serializer.is_valid():
                    serializer.save()


        img   = qrcode.make(request.build_absolute_uri()) #動画のQRコード
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr = base64.b64encode(buffer.getvalue()).decode().replace("'", "")


        comments    = VideoComment.objects.filter(target=video_pk).order_by("-dt")
        good        = GoodVideo.objects.filter(target=video_pk)
        bad         = BadVideo.objects.filter(target=video_pk)

        already_good    = GoodVideo.objects.filter(target=video_pk, user=request.user.id)
        already_bad     = BadVideo.objects.filter(target=video_pk, user=request.user.id)
        relates         = Video.objects.filter(category=video.category).order_by("-dt")
        categories      = Category.objects.all()


        paginator = Paginator(comments, 10)

        comments = paginator.get_page(1)

        context = {"video": video,
                   "comments": comments,
                   "good": good,
                   "bad": bad,
                   "already_good": already_good,
                   "already_bad": already_bad,
                   "relates": relates,
                   "categories": categories,
                   "qr":qr,
                   }

        return render(request, "tube/single.html", context)

    def post(self,request,video_pk,*args,**kwargs):

        return JsonResponse(json)

        # return redirect("tube:videos",video_pk=video_pk)

single = SingleView.as_view()


class SingleModView(LoginRequiredMixin,views.APIView):

    #ここでコメントのページネーション↑ のクラス名変えるべきでは？
    def get(self,request,video_pk,*args,**kwargs):

        page        = 1
        if "page" in request.GET:
            page    = request.GET["page"]

        video               = Video.objects.filter(id=video_pk).first()
        comments            = VideoComment.objects.filter(target=video_pk).order_by("-dt")
        comments_paginator  = Paginator(comments,COMMENTS_AMOUNT_PAGE)
        comments            = comments_paginator.get_page(page)

        #コメントをrender_to_stringテンプレートを文字列化、json化させ返却
        context     = { "comments":comments,
                        "video":video,
                        }
        content     = render_to_string('tube/comments.html', context ,request)

        json        = { "error":False,
                        "content":content,
                        }

        return JsonResponse(json)


    def post(self, request, video_pk, *args, **kwargs):

        copied   = request.POST.copy()

        copied["target"]  = video_pk
        copied["user"]    = request.user.id

        serializer  = VideoCommentSerializer(data=copied)
        json        = {}

        if serializer.is_valid():
            print("コメントバリデーションOK")
            serializer.save()

            comments    = VideoComment.objects.filter(target=video_pk).order_by("-dt")
            comments_paginator  = Paginator(comments,COMMENTS_AMOUNT_PAGE)
            comments            = comments_paginator.get_page(1)
            video               = Video.objects.filter(id=video_pk).first()

            context     = { "comments":comments,
                            "video":video,
                            }

            content     = render_to_string('tube/comments.html', context, request)

            json        = { "error":False,
                            "message":"投稿完了",
                            "content":content,
                            }

        else:
            print("コメントバリデーションNG")
            json        = {"error":True,
                           "message":"入力内容に誤りがあります。",
                           "content":"",
                           }


        return JsonResponse(json)

    def patch(self,request,video_pk,*args,**kwargs):

        serializer  = RateSerializer(data=request.data)

        if not serializer.is_valid():

            json = {"error": True,
                    "message": "入力内容に誤りがあります。",
                    "content": "",
                    }

            return JsonResponse(json)

        validated_data  = serializer.validated_data

        if validated_data["flag"]:

            data    = GoodVideo.objects.filter(user=request.user.id, target=video_pk).first()
            if data:
                data.delete()
                print("削除")
            else:
                data    = { "user":request.user.id,
                            "target":video_pk,
                            }
                serializer  = GoodSerializer(data=data)

                if serializer.is_valid():
                    print("セーブ")
                    serializer.save()
                else:
                    print("バリデーションエラー")
        else:
            data    = BadVideo.objects.filter(user=request.user.id, target=video_pk).first()
            if data:
                data.delete()
                print("削除")
            else:
                data = {"user": request.user.id,
                        "target": video_pk,
                        }
                serializer = BadSerializer(data=data)

                if serializer.is_valid():
                    print("セーブ")
                    serializer.save()
                else:
                    print("バリデーションエラー")

        good         = GoodVideo.objects.filter(target=video_pk)
        bad          = BadVideo.objects.filter(target=video_pk)
        already_good = GoodVideo.objects.filter(target=video_pk, user=request.user.id)
        already_bad  = BadVideo.objects.filter(target=video_pk, user=request.user.id)
        video        = Video.objects.filter(id=video_pk).first()

        context = {"good": good,
                   "bad": bad,
                   "already_good": already_good,
                   "already_bad": already_bad,
                   "video": video,
                   }

        content = render_to_string('tube/rate.html', context, request)

        json = {"error": False,
                "message": "投稿完了",
                "content": content,
                }

        return JsonResponse(json)

    #動画に対する編集処理（リクエストユーザーが動画投稿者であることを確認して実行）
    def put(self,request,video_pk,*args,**kwargs):

        json = {"error":True }

        # 編集対象の動画を特定する。
        instance = Video.objects.filter(id=video_pk).first()

        # 無い場合はそのまま返す
        if not instance:
            return JsonResponse(json)

        # TIPS:get_object_or_404を使う方法もある、いずれにせよレコード単体のオブジェクトをシリアライザの第一引数に指定して、編集対象を指定する必要がある点で同じ。こちらは存在しない場合404をリターンするためif文で分岐させる必要はない。
        # instance    = get_object_or_404(Video.objects.all(), pk=video_pk)

        # 受け取ったリクエストのdataにAjaxの送信内容が含まれているのでこれをバリデーション。編集対象は先ほどvideo_pkで特定したレコード単体
        serializer = VideoEditSerializer(instance, data=request.data)

        if serializer.is_valid():
            serializer.save()
            json = {"error": False}
            Video.objects.filter(id=video_pk).update(edited=True)

        return JsonResponse(json)

    #動画に対する削除処理
    def delete(self,request,video_pk,*args,**kwargs):

        video   = Video.objects.filter(id=video_pk).first()

        print(video.user.id)
        print(request.user.id)

        if video.user.id == request.user.id:
            print("削除")
            video.delete()
            error   = False
            message = "削除しました。"

        else:
            print("拒否")
            error   = True
            message = "削除できませんでした。"

        json        = {"error":error,
                       "message":message,}

        return JsonResponse(json)

single_mod = SingleModView.as_view()


class RankingView(views.APIView):

    def get(self,request,*args,**kwargs):

        return render(request,"tube/rank.html")

rank    = RankingView.as_view()


class MyPageView(LoginRequiredMixin, views.APIView):

    def get(self, request,*args, **kwargs):

        videos = Video.objects.filter(user=request.user.id).order_by("-dt")
        good_videos = GoodVideo.objects.filter(user=request.user.id).order_by("-dt")

        context = {"videos": videos,
                   "good_videos": good_videos,
                   }

        return render(request, "tube/mypage.html", context)


    def post(self,request, *args,**kwargs):

        print(request.data)
        print(request.user.id)

        instance = CustomUser.objects.get(id=request.user.id)

        serializer = IconSerializer(instance, data=request.data)

        if serializer.is_valid():
            print("validation OK")
            serializer.save()

            json = {"error": False,
                    "message":"アイコンが登録されました。",
                    }

        else:
            print("バリデーションエラー")
            json = {"error": True,
                    "message": "アイコン登録に失敗しました。",
                    }

        return JsonResponse(json)


mypage = MyPageView.as_view()



# 閲覧履歴表示
class HistoryView(LoginRequiredMixin, views.APIView):

    def get(self, request, *args, **kwargs):
        histories = History.objects.filter(user=request.user.id).order_by("-dt")
        amount    = len(histories)

        paginator = Paginator(histories, 5)

        if "page" in request.GET:
            histories = paginator.get_page(request.GET["page"])
        else:
            histories = paginator.get_page(1)

        context = {"histories": histories,
                   "amount": amount}

        return render(request, "tube/history.html", context)


history = HistoryView.as_view()


# おすすめ動画
class RecommendView(LoginRequiredMixin,views.APIView):

    def get(self,request,*args,**kwargs):

        return render(request, "tube/recommend.html")

recommend = RecommendView.as_view()


#通知
class NotifyView(views.APIView):

    def get(self,request,*args,**kwargs):

        return render(request, "tube/notify.html")

notify = NotifyView.as_view()



#マイリスト
class MyListView(LoginRequiredMixin,views.APIView):

    def get(self,request,*args,**kwargs):

        mylists = MyList.objects.filter(user=request.user.id).order_by("-dt")

        context = {"mylists":mylists}

        return render(request,"tube/mylist.html",context)

    def post(self,request,*args,**kwargs):

        copied          = request.POST.copy()
        copied["user"]  = request.user.id

        serializer      = MyListSerializer(data=copied)
        if serializer.is_valid():

            mylist      = MyList.objects.filter(user=request.user.id, target=request.POST["target"])
            if not mylist:
                serializer.save()
                error   = False
                message = "マイリスト登録完了"
            else:
                error   = True
                message = "すでにマイリストに登録しています。"

        else:
            error       = True
            message     = "入力内容に誤りがあります。"

        json            = { "error":error,
                            "message":message,
                            }

        return JsonResponse(json)

    #TODO:マイリストの削除を
    

mylist = MyListView.as_view()




class ConfigViews(LoginRequiredMixin,views.APIView):

    def get(self, request, *args, **kwargs):

        # 自分がフォローしているユーザー、ブロックしているユーザーの一覧
        follow_users = FollowUser.objects.filter(from_user=request.user.id)
        block_users = BlockUser.objects.filter(from_user=request.user.id)

        # 自分をフォローしているユーザー、ブロックしているユーザーの一覧
        follower_users = FollowUser.objects.filter(to_user=request.user.id)
        #blocker_users = BlockUser.objects.filter(to_user=request.user.id)

        context = {"follow_users":follow_users,
                   "block_users":block_users,
                   "follower_users":follower_users,
                   #"blocker_users":blocker_users,
                  }

        return render(request, "tube/config.html", context)

config = ConfigViews.as_view()



#ユーザーページの表示
class UserSingleView(views.APIView):

    def get(self, request, pk, *args, **kwargs):

        user    = CustomUser.objects.filter(id=pk).first()


        #このユーザーがフォローしているユーザー、ブロックしているユーザーの一覧
        follow_users = FollowUser.objects.filter(from_user=pk)
        block_users  = BlockUser.objects.filter(from_user=pk)

        #このユーザーをフォローしているユーザーしているユーザーの一覧
        follower_users    = FollowUser.objects.filter(to_user=pk)


        context = { "user":user,
                    "follow_users":follow_users,
                    "block_users":block_users,
                    "follower_users":follower_users,
                  }

        return render(request, "tube/user.html", context)

usersingle  = UserSingleView.as_view()




class UserFollowView(LoginRequiredMixin,views.APIView):

    def post(self,request,pk,*args,**kwargs):

        followusers  = FollowUser.objects.filter(from_user=request.user.id,to_user=pk) #from_userは自分自身。to_user はフォローした相手。

        json    = { "error":False }

        #すでにある場合は該当レコードを削除、無い場合は挿入
        #TIPS:↑メソッドやビュークラスを切り分けてしまうと、多重に中間テーブルへレコードが挿入されてしまう可能性があるため1つのメソッド内で分岐するやり方が無難。
        if followusers:
            print("ある。フォロー解除。")
            followusers.delete()

            return JsonResponse(json)
        else:
            print("無い")

        data        = { "from_user":request.user.id,"to_user":pk }
        serializer  = FollowUserSerializer(data=data)

        if serializer.is_valid():
            print("フォローOK")
            serializer.save()
        else:
            print("フォロー失敗")
            json["error"]   = True

        return JsonResponse(json)


userfollow   = UserFollowView.as_view()


class UserBlockView(LoginRequiredMixin,views.APIView):

    def post(self,request,pk,*args,**kwargs):

        blockusers  = BlockUser.objects.filter(from_user=request.user.id,to_user=pk)

        json    = { "error":False }

        if blockusers:
            print("ある。ブロック解除。")
            blockusers.delete()

            return JsonResponse(json)
        else:
            print("無い")

        data        = { "from_user":request.user.id,"to_user":pk }
        serializer  = BlockUserSerializer(data=data)

        if serializer.is_valid():
            print("ブロックOK")


            serializer.save()
        else:
            print("ブロック失敗")
            json["error"]   = True

        return JsonResponse(json)


userblock   = UserBlockView.as_view()


class UserEditView(LoginRequiredMixin,views.APIView):

    def put(self, request, pk, *args, **kwargs):

        print(request.user.id)

        json = {"error": True}

        # 編集対象の動画を特定する。
        instance = CustomUser.objects.filter(id=request.user.id).first()


        # 無い場合はそのまま返す
        if not instance:
            print('ない')
            return JsonResponse(json)

        # 受け取ったリクエストのdataにAjaxの送信内容が含まれているのでこれをバリデーション。

        print(request.data)

        serializer = UserInformationSerializer(instance, data=request.data)
        print('ある')


        if serializer.is_valid():
            data    = serializer.validated_data
            print("バリデーションしたときの中身")
            print(data)



            result  = serializer.save()
            print(result)
            print(result.self_introduction)
            print('バリデーションOK')
            json = {"error": False,
                    "message":"登録しました。",}

        else:
            print('失敗')

        return JsonResponse(json)

useredit = UserEditView.as_view()
