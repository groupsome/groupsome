$(function () {
	if ($("body").is(".can-move-files")) {
		$(document).on("click", ".files-create-folder-btn", function (e) {
			var button = $(this);
			nicePrompt("Create folder", "Name", function (value) {
				if (value != "") {
					var form = $("<form />")
						.attr("method", "post")
						.attr("action", "/groups/"+button.data("group-id")+"/files/directories/create")
						.append($('<input type="hidden" name="csrfmiddlewaretoken" />').val(Cookies.get("csrftoken")))
						.append($('<input type="hidden" name="name" />').val(value))
						.append($('<input type="hidden" name="parent" />').val(button.data("parent-id")))
						.appendTo($("body"))
						.submit();
				}
			});
		});

		$(document).on("click", ".file-delete-btn", function (e) {
			e.preventDefault();
			if (!confirm(deleteFileText))
				return;
			
			var file = $(this).parents("tr");
			$.ajax({
				type: "POST",
				url: "/groups/"+$(this).data("group-id")+"/files/"+$(this).data("file-id")+"/delete",
				data: {
					csrfmiddlewaretoken: Cookies.get("csrftoken"),
				},
				success: function (response) {
					toast(response.message);
					file.remove();
				},
				error: function () {
					errorToast();
				}
			});
		});

		$(document).on("click", ".directory-delete-btn", function (e) {
			e.preventDefault();
			if (!confirm(deleteDirectoryText))
				return;
			
			var directory = $(this).parents("tr");
			$.ajax({
				type: "POST",
				url: "/groups/"+$(this).data("group-id")+"/files/directories/"+$(this).data("directory-id")+"/delete",
				data: {
					csrfmiddlewaretoken: Cookies.get("csrftoken"),
				},
				success: function (response) {
					toast(response.message);
					directory.remove();
				},
				error: function () {
					errorToast();
				}
			});
		});
		
		$(".file-table .file").draggable({
			helper: function (e) {
				return $('<span class="file-drag"><i class="fa fa-file"></i></span>');
			},
			cursorAt: {
				top: 10,
				left: 10,
			}
		});
		
		$(".file-table .directory").draggable({
			helper: function (e) {
				return $('<span class="file-drag"><i class="fa fa-folder"></i></span>');
			},
			cursorAt: {
				top: 10,
				left: 10,
			}
		});
		
		$(".file-table .directory").droppable({
			drop: function (e, ui) {
				var directory = $(e.target);
				var content = $(ui.draggable);
				
				if ($(ui.draggable).is(".file")) {
					$.ajax({
						type: "POST",
						url: "/groups/"+directory.data("group-id")+"/files/"+content.data("file-id")+"/move",
						data: {
							csrfmiddlewaretoken: Cookies.get("csrftoken"),
							directory: directory.data("directory-id"),
						},
						success: function (response) {
							toast(response.message);
							content.remove();
						},
						error: function () {
							errorToast();
						}
					});
				} else if ($(ui.draggable).is(".directory")) {
					$.ajax({
						type: "POST",
						url: "/groups/"+directory.data("group-id")+"/files/directories/"+content.data("directory-id")+"/move",
						data: {
							csrfmiddlewaretoken: Cookies.get("csrftoken"),
							directory: directory.data("directory-id"),
						},
						success: function (response) {
							toast(response.message);
							content.remove();
						},
						error: function () {
							errorToast();
						}
					});
				}
			},
		});
	}
});
