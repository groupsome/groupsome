$(function () {
	$("[data-post]").click(function (e) {
		e.preventDefault();
		
		if (!$(this).data("confirm") || confirm($(this).data("confirm"))) {
			var form = $("<form />")
				.attr("method", "post")
				.attr("action", $(this).data("post"))
				.append($('<input type="hidden" name="csrfmiddlewaretoken" />').val(Cookies.get("csrftoken")));
			
			if ($(this).data("body")) {
				$.each($(this).data("body"), function (key, value) {
					form.append($('<input type="hidden" />').attr("name", key).val(value));
				});
			}
			
			form.appendTo($("body"))
				.submit();
		}
	});
	
	$('[data-toggle="tooltip"]').tooltip();
});
