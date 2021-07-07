window.addEventListener("load" , function (){
    $(document).on("click","#information_update", function() { information_update();});
});


function information_update(){

    let form_elem   = "#information_update_form";

    let data    = new FormData( $(form_elem).get(0) );
    let url     = $(form_elem).prop("action");
    let method  = "PUT";

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
            $("#delete_message").addClass("upload_message_error");
            $("#delete_message").removeClass("upload_message_success");
            console.log(data.error);
        }
        else{
            $("#delete_message").addClass("upload_message_success");
            $("#delete_message").removeClass("upload_message_error");
            console.log("編集完了");

        }

        $("#delete_message").text(data.message)

        console.log(data);

        //setTimeout( function() { location.reload(); }, 1500);

    }).fail( function(xhr, status, error) {
        console.log(status + ":" + error );
    });

}

