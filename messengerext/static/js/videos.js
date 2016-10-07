$(document).ready(function(){

	highlightFirst();
	htmlText = document.getElementsByClassName("group")[0].innerHTML
	window.history.replaceState(htmlText, document.title, document.location);
});

$(function () {
	$(document).on("click", ".video-delete-btn", function (e) {
		e.preventDefault();
		if (!confirm(deleteVideoText))
			return;

		var video = $(this).parents(".item-video");
		$.ajax({
			type: "POST",
			url: "/groups/"+$(this).data("group-id")+"/videos/"+$(this).data("video-id")+"/delete",
			data: {
				csrfmiddlewaretoken: Cookies.get("csrftoken"),
			},
			success: function (response) {
				toast(response.message);

				if(video.hasClass( "group-highlighted" )){
					video.remove();
					highlightFirst();
				}
				else
					video.remove();

			},
			error: function () {
				errorToast();
			}
		});
	});

});

window.onpopstate = function(e){

	e.preventDefault();

    if(e.state){
        document.getElementsByClassName("group")[0].innerHTML = e.state;
    }


	scrollAfterReload()


	$(".video-scrollbar").mousewheel(function(event, delta) {

      this.scrollLeft -= (delta * 30);

	  event.preventDefault();
   });


};

$(document).delegate('[data-toggle="loadvideo"]', 'click', function(event) {
    event.preventDefault();

    $(".group-highlighted").removeClass("group-highlighted");
    $(this).parent().addClass("group-highlighted");

    href  = $(this).attr("href");
    thumbnail = $(this).find("img:first").attr("src");
    type = $(this).data("type");
    $videoDiv = $("#mobilVideoDiv");

    if($videoDiv && $videoDiv.css("font-size") == "14px"){
        $videoDiv = $("#mobilVideoDiv")
        $video = $("#mobilVideo")

        $videoDiv.show();
        $video.attr("src",href);
        $video.attr("poster",thumbnail);
        $video.load();

        video = document.getElementById("mobilVideo");

        if (video.requestFullscreen) {
            video.requestFullscreen();
        } else if (video.mozRequestFullScreen) {
          video.mozRequestFullScreen();
        } else if (video.webkitRequestFullscreen) {
          video.webkitRequestFullscreen();
        }

        video.play();
    }
    else{
        $video = $("#groupVideo")
        $video.attr("src",href);
        $video.attr("poster",thumbnail);
        $video.load();
        $('html, body').animate({
            scrollTop: $("#video-header").offset().top
        }, 700);
        $('html, body').promise().done(function(){
            $("#groupVideo").get(0).play();
        });
    }

    locationStr = document.location+''
	if(locationStr.lastIndexOf("/")== locationStr.length)
		locationStr = locationStr.substr(0,locationStr.length-1)

	id = $(this).data("id");
	newurl = ""
	if(locationStr.substr(locationStr.lastIndexOf("/")+1) == "videos" ){
		newurl = locationStr + "/"+id;
	}
	else{
		base = locationStr.substr(0,locationStr.lastIndexOf("/"))
		newurl = base + "/"+id;
	}
	htmlText = document.getElementsByClassName("group")[0].innerHTML
	window.history.pushState(htmlText, document.title, newurl);
});

$(function() {

   $(".video-scrollbar").mousewheel(function(event, delta) {

      this.scrollLeft -= (delta * 30);

      event.preventDefault();

   });

});

function highlightFirst(){
	href= ""
	thumbnail = ""
	locationStr = document.location+''

	if(locationStr.lastIndexOf("/")+1== locationStr.length)
		locationStr = locationStr.substr(0,locationStr.length-1)

	if(locationStr.substr(locationStr.lastIndexOf("/")+1) == "videos" ){
		$firstVideo = $(document).find(".item-video:first").children().eq(1)
		id = $firstVideo.data("id");
		newurl = locationStr + "/"+id;
		window.history.pushState({path:newurl},'',newurl);
		$firstVideo.parent().addClass("group-highlighted")
		href = $firstVideo.attr("href")
		thumbnail = $(document).find(".item-video:first").find("img:first").attr("src")
	}

	else{
		id = locationStr.substr(locationStr.lastIndexOf("/")+1, locationStr.length)
		$selectedVideo = $(".item-video").find("[data-id=\""+id+"\"]:first")
		if($selectedVideo.length > 0){
			$selectedVideo.parent().addClass("group-highlighted")
			href = $selectedVideo.attr("href")
			thumbnail = $selectedVideo.find("img:first").attr("src")
			$('html, body').animate({
				scrollTop: ($selectedVideo.offset().top - 50)
				}, 700);

			$videoList = $(".video-list-small").first()
			$(".video-list-small").animate({
				scrollLeft: ($selectedVideo.offset().left - $videoList.offset().left - $videoList.width()/2 + $selectedVideo.width()/2)
				}, 700);

		}

	}

    $video = $("#groupVideo")
    $video.attr("src",href);
    $video.attr("poster",thumbnail);

}

function scrollAfterReload(){

	locationStr = document.location+''

	if(locationStr.substr(locationStr.lastIndexOf("/")+1) != "videos" ){
		id = locationStr.substr(locationStr.lastIndexOf("/")+1, locationStr.length)
		$selectedVideo2 = $(".item-video").find("[data-id=\""+id+"\"]:first")
		if($selectedVideo2){
			$videoDiv = $("#mobilVideoDiv");
			if($videoDiv && $videoDiv.css("font-size") == "14px"){
				$('html, body').animate({
						scrollTop: ($selectedVideo2.offset().top - 50)
				}, 700);
			}
			else{
				$videoList2 = $(".video-list-small").first();

				$('html, body').animate({
						scrollTop: ($videoList2.offset().top + $videoList2.height() + 10)
				}, 700);


				$(".video-list-small").animate({
					scrollLeft: ($selectedVideo2.offset().left - $videoList2.offset().left - $videoList2.width()/2 + $selectedVideo2.width()/2)
				}, 700);
			}
		}
	}
}