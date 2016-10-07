function toast(message) {
	$('.toast').text(message);
	$('.toast').fadeIn(400).delay(3000).fadeOut(400);
}

function errorToast() {
	toast("Something went wrong");
}

function nicePrompt(title, label, callback) {
	$("#modal-prompt .modal-title").text(title);
	$("#modal-prompt .control-label").text(label);
	$("#modal-prompt-input").val("");
	
	$("#modal-prompt-input").off("keypress");
	$("#modal-prompt-input").on("keypress", function (e) {
		if (e.which == 13)
			$("#modal-prompt .btn-primary").click();
	});
	
	$("#modal-prompt .btn-primary").off("click");
	$("#modal-prompt .btn-primary").one("click", function (e) {
		callback($("#modal-prompt-input").val());
		$("#modal-prompt").modal("hide");
	});
	
	$("#modal-prompt").modal();
}
