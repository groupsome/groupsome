$(function () {
	var showChatlogModal = function (contentType, contentID) {
		$.ajax({
			type: "GET",
			url: "/chatlog/"+contentType+"/"+contentID,
			data: {
				csrfmiddlewaretoken: Cookies.get("csrftoken"),
			},
			success: function (html) {
				$("#modal-chatlog .modal-body.chatlog").html(html);
				prepareAudios();
				$("#modal-chatlog .modal-title").text($("#modal-chatlog .chatlog-items").data("group-title"));
				$("#modal-chatlog").modal();
				
				var content = $("#modal-chatlog .modal-body.chatlog .chatlog-item-selected");
				var scrollTo = function () {
					$("#modal-chatlog .modal-body.chatlog").scrollTo(content, { margin: true });
				};
				scrollTo();
				$("#modal-chatlog .modal-body.chatlog").imagesLoaded().progress(scrollTo);
				$("#modal-chatlog .modal-body.chatlog").removeClass("loading");
			},
			error: function () {
				errorToast();
			}
		});
	};
	
	var showChatlogEmbed = function (contentType, contentID, elem) {
		$.ajax({
			type: "GET",
			url: "/chatlog/"+contentType+"/"+contentID,
			data: {
				csrfmiddlewaretoken: Cookies.get("csrftoken"),
			},
			success: function (html) {
				elem.html(html);
				prepareAudios();
				
				var content = elem.find('.chatlog-item-selected');
				var scrollTo = function () {
					elem.scrollTo(content, { margin: true });
				};
				scrollTo();
				elem.imagesLoaded().progress(scrollTo);
				elem.removeClass("loading");
			},
			error: function () {
				errorToast();
			}
		});
	};
	
	var chatlogPager = function (chatlog, direction) {
		var reference = chatlog.find(".chatlog-items .chatlog-item:" + (direction == "older" ? "first" : "last"));
		
		$.ajax({
			type: "GET",
			url: "/chatlog/"+reference.data("content-type")+"/"+reference.data("content-id")+"/"+direction,
			data: {
				csrfmiddlewaretoken: Cookies.get("csrftoken"),
			},
			success: function (html) {
				var height = chatlog.get(0).scrollHeight;
				var scroll = chatlog.scrollTop();
				
				if (direction == "older")
					chatlog.find(".chatlog-items").prepend(html);
				else
					chatlog.find(".chatlog-items").append(html);
				prepareAudios();
				
				if (direction == "older") {
					var scrollTo = function () {
						chatlog.scrollTop(scroll + chatlog.get(0).scrollHeight - height);
					};
					scrollTo();
					chatlog.imagesLoaded().progress(scrollTo);
				}
				
				chatlog.removeClass("loading");
			},
			error: function () {
				errorToast();
			}
		});
	};
	
	$(document).on("click", ".chatlog-button", function (e) {
		e.preventDefault();
		showChatlogModal($(this).data("content-type"), $(this).data("content-id"));
	});
	
	$(document).on("click", ".chatlog-pager-button", function (e) {
		var chatlog = $(this).parents(".chatlog");
		var direction = $(this).data("direction");
		chatlogPager(chatlog, direction);
	});
	
	$("#modal-chatlog .chatlog").scroll(function (e) {
		if (!$(this).is(".loading")) {
			if ($(this).scrollTop() == 0) {
				$(this).addClass("loading");
				chatlogPager($("#modal-chatlog .chatlog"), "older");
			} else if (($(this).scrollTop() + $(this).innerHeight()) == $(this).get(0).scrollHeight) {
				$(this).addClass("loading");
				chatlogPager($("#modal-chatlog .chatlog"), "newer");
			}
		}
	});
	
	$(".chatlog-embed").each(function () {
		showChatlogEmbed($(this).data("content-type"), $(this).data("content-id"), $(this));
		
		$(this).scroll(function (e) {
			if (!$(this).is(".loading")) {
				if ($(this).scrollTop() == 0) {
					$(this).addClass("loading");
					chatlogPager($(this), "older");
				} else if (($(this).scrollTop() + $(this).innerHeight()) == $(this).get(0).scrollHeight) {
					$(this).addClass("loading");
					chatlogPager($(this), "newer");
				}
			}
		});
	});
});
