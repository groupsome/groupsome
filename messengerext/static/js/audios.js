$(function () {
	$(document).on("click", ".audio-delete-btn", function (e) {
		e.preventDefault();
		if (!confirm(deleteAudioText))
			return;

		var audio = $(this).parents(".item-audio");
		$.ajax({
			type: "POST",
			url: "/groups/"+$(this).data("group-id")+"/audios/"+$(this).data("audio-id")+"/delete",
			data: {
				csrfmiddlewaretoken: Cookies.get("csrftoken"),
			},
			success: function (response) {
				toast(response.message);
				audio.remove();
			},
			error: function () {
				errorToast();
			}
		});
	});

	$.endlessPaginate({
			paginateOnScroll: true,
			paginateOnScrollMargin: 20,
	});

    prepareAudios();
});
