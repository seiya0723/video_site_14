from django.contrib import admin
from django.utils.html import format_html

from .models import Video,VideoComment,Category,MyList

class VideoAdmin(admin.ModelAdmin):

    # 指定したフィールドを表示、編集ができる
    list_display = [ "format_thumbnail","user","id","title","description","category","dt" ]
    list_editable = [ "category","dt","title","description", ]

    #指定したフィールドの検索と絞り込みができる

    search_fields       = [ "id","title","user","description","dt" ]
    list_filter         = [ "title","user" ]

    #1ページ当たりに表示する件数、全件表示を許容する最大件数(ローカルでも5000件を超えた辺りから遅くなるので、10000~50000辺りが無難)
    list_per_page       = 10
    list_max_show_all   = 20000

    #日付ごとに絞り込む、ドリルナビゲーションの設置
    date_hierarchy      = "dt"

    #画像のフィールドはimgタグで画像そのものを表示させる
    def format_thumbnail(self,obj):
        if obj.thumbnail:
            return format_html('<img src="{}" alt="画像" style="width:15rem">', obj.thumbnail.url)

    #画像を表示するときのラベル(thumbnailのverbose_nameをそのまま参照している)
    format_thumbnail.short_description      = Video.thumbnail.field.verbose_name
    format_thumbnail.empty_value_display    = "画像なし"


class VideoCommentAdmin(admin.ModelAdmin):

    list_display = [ "id","format_user","target","content","dt"]
    list_editable = [ "content" ]

    search_fields       = [ "content","dt","user" ]
    list_filter         = [ "content","user" ]

    list_per_page       = 10
    list_max_show_all   = 20000

    date_hierarchy      = "dt"

    def format_user(self,obj):
        if obj.user.handle_name:
            return obj.user.handle_name

    format_user.short_description      = VideoComment.user.field.verbose_name
    format_user.empty_value_display    = "名前がありません"


class MyListAdmin(admin.ModelAdmin):
    list_display = [ "id","dt","target","format_user" ]

    #投稿者の表示。外部キーuserのidを使い、カスタムユーザーモデルのhandle_nameを表示
    def format_user(self,obj):
        if obj.user.handle_name:
            return obj.user.handle_name

    format_user.short_description      = MyList.user.field.verbose_name
    format_user.empty_value_display    = "名前がありません"


admin.site.register(Video,VideoAdmin)
admin.site.register(VideoComment,VideoCommentAdmin)
admin.site.register(Category)
admin.site.register(MyList,MyListAdmin)
