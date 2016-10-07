$(function () {
	$(document).on("click", ".link-delete-btn", function (e) {
		e.preventDefault();
		if (!confirm(deleteLinkText))
			return;

		var link = $(this).parents("tr");
		$.ajax({
			type: "POST",
			url: "/groups/"+$(this).data("group-id")+"/links/"+$(this).data("link-id")+"/delete",
			data: {
				csrfmiddlewaretoken: Cookies.get("csrftoken"),
			},
			success: function (response) {
				toast(response.message);
				link.remove();
			},
			error: function () {
				errorToast();
			}
		});
	});
});
