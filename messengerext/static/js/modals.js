$(function () {
	var exitMobileVideoDiv = function () {
		if (document.webkitIsFullScreen == false || document.mozFullScreen == false || document.msFullscreenElement == false) {
			$videoDiv = $("#mobilVideoDiv");
			$videoDiv.hide()

			$video = $("#mobilVideo")
			$video.attr("src","");
			$video.attr("poster","");
		}
	};

	document.addEventListener("webkitfullscreenchange", exitMobileVideoDiv, false);
	document.addEventListener("mozfullscreenchange", exitMobileVideoDiv, false);
	document.addEventListener("fullscreenchange", exitMobileVideoDiv, false);
	document.addEventListener("MSFullscreenChange", exitMobileVideoDiv, false);
	
	$(document).delegate('[data-toggle="lightbox"]', "click", function (event) {
		type = $(this).data("type")
		$videoDiv = $("#mobilVideoDiv")

		if($videoDiv && $videoDiv.css("font-size") == "14px" &&  type && type == "video"){
			event.preventDefault();
			href = $(this).attr("href")
			thumbnail = $(this).find("img:first").attr("src")
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
		} else{
			if ($(window).width() > 740) {
				event.preventDefault();
				$(this).ekkoLightbox();
			}
		}
	});
});