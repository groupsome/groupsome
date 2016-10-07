$(function () {
	$(".qrcode").each(function () {
		$(this).qrcode({
			text: $(this).data("code"),
			fill: "#000",
			background: "#fff",
			size: 175,
		});
	});
	
	var poll = function () {
		$.ajax({
			method: "POST",
			url: $(".form-signin").data("url"),
			success: function (response) {
				if (response.redirect)
					location.href = $(".form-signin").data("redirect");
				else
					setTimeout(poll, 1000);
			},
		});
	};
	
	poll();
});
