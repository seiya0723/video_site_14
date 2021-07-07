window.addEventListener("load" , function (){

    $("#upload").on("click",function(){ video_upload(); });
    upload_form_initialize();

});


function video_upload(){

    let form_elem   = "#video_upload_form";

    let data    = new FormData( $(form_elem).get(0) );
    let url     = $(form_elem).prop("action");
    let method  = $(form_elem).prop("method");

    //指定したタブの値によって、動画よりサムネイル指定の処理
    if ( $("[name='upload_tab']:checked").val() === "1" ){

        let context = document.getElementById('canvas').getContext('2d');
        var base64  = context.canvas.toDataURL('image/png');

        // Base64からバイナリへ変換
        var bin     = atob(base64.replace(/^.*,/, ''));
        var buffer  = new Uint8Array(bin.length);
        for (var i = 0; i < bin.length; i++) {
            buffer[i] = bin.charCodeAt(i);
        }

        //バイナリでファイルを作る
        var file    = new File( [buffer.buffer],"test.png", { type: 'image/png' });

        data.append("thumbnail",file);
    }

    for (let v of data.entries() ){ console.log(v); }

    $.ajax({
        url: url,
        type: method,
        data: data,
        processData: false,
        contentType: false,
        dataType: 'json'
    }).done( function(data, status, xhr ) { 

        if (data.error){
            $("#upload_message").addClass("upload_message_error");
            $("#upload_message").removeClass("upload_message_success");
        }
        else{
            $("#upload_message").addClass("upload_message_success");
            $("#upload_message").removeClass("upload_message_error");
            upload_form_initialize();
        }
        $("#upload_message").text(data.message)

        console.log(data);

    }).fail( function(xhr, status, error) {
        console.log(status + ":" + error );
    });

}
function upload_form_initialize() {
    
    $("[name='title']").val("");
    $("[name='category']").val("");
    $("[name='description']").val("");
    $("[name='movie']").val("");
    $("[name='thumbnail']").val("");

    //動画よりサムネイル指定もクリアに
    let canvas  = document.querySelector('#canvas');
    let ctx     = canvas.getContext('2d');
    let vEle    = document.querySelector('#thumbnail_video');

    //動画サイズに合わせてクリアする。
    let video_w = vEle.videoWidth;
    let video_h = vEle.videoHeight;
    ctx.clearRect(0, 0, video_w, video_h);

    //videoタグもクリア。
    vEle.src    = "";

}



