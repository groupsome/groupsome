$(function () {
	var addImageToAlbum = function (element, album_id, image_id, group_id) {
		var url = "/gallery/" + group_id + '/' + album_id + "/add/"+ image_id;
		item = $(element).parents('.photo-options');
		$.ajax({
			type: "POST",
			url: url,
			data: {
				csrfmiddlewaretoken: Cookies.get("csrftoken"),
			},
			success: function (response) {
				item.html(response);
				toast(addPictureToAlbum);
			},
			error: function () {
				errorToast();
			}
		})
	}

	var removeImageFromAlbum = function (element, album_id, image_id, group_id) {
		var url = '/gallery/' + group_id + '/' + album_id + "/delete_from_album/"+ image_id;
		$(element).parents('.item').fadeOut(400);
		$.ajax({
			type: "POST",
			url: url,
			data: {
				csrfmiddlewaretoken: Cookies.get("csrftoken"),
			},
		}).done(function(data) {
			toast(data['message']);
		});
	}
	var removeImageFromAlbumOverview = function (element, album_id, image_id, group_id) {
		var url = '/gallery/' + group_id + '/' + album_id + "/delete_from_album/"+ image_id;
		item = $(element).parents('.photo-options')
		$.ajax({
			type: "GET",
			url: url,
			data: {
				csrfmiddlewaretoken: Cookies.get("csrftoken"),
			},
			success: function (response) {
				item.html(response);
				toast(removePictureFromAlbum);
			},
			error: function () {
				errorToast();
			}
		})
	}
	
	$(document).on("click", ".remove-from-album-btn", function (e) {
		e.preventDefault();
		removeImageFromAlbum($(this), $(this).data("album-id"), $(this).data("photo-id"),  $(this).data("group-id"));
	});

	$(document).on("click", ".remove-from-album-overview-btn", function (e) {
		e.preventDefault();
		removeImageFromAlbumOverview($(this), $(this).data("album-id"), $(this).data("photo-id"), $(this).data("group-id"));
	});

	$(document).on("click", ".add-photo-to-album-btn", function (e) {
		e.preventDefault();
		addImageToAlbum($(this), $(this).data("album-id"), $(this).data("photo-id"), $(this).data("group-id"));
	});

	$(document).on("click", ".photo-delete-btn", function (e) {
		e.preventDefault();
		
		var photo = $(this).parents(".item");
		$.ajax({
			type: "POST",
			url: "/gallery/photos/"+$(this).data("photo-id")+"/delete",
			data: {
				csrfmiddlewaretoken: Cookies.get("csrftoken"),
			},
			success: function (response) {
				toast(response.message);
				photo.remove();
			},
			error: function () {
				errorToast();
			}
		})
	});
});




$(function () {

	var image_container = $(".group-photo")
	var image = $(".group-photo img");
    var angle = 0;

	var rotateImage = function (delta) {
        angle = angle + delta;
        angle = angle % 360;
        h = image.height();
        w = image.width();
        if (Math.abs(angle) == 90 || Math.abs(angle) == 270){
            var scale_factor = Math.min(h,w)/Math.max(h,w);
            image_container.css('transform','rotate(' + angle + 'deg) scale('+ scale_factor + ',' + scale_factor + ')');
        }
        else {
            image_container.css('transform','rotate(' + angle + 'deg)');
        }
    }

	$(document).on("click", ".photo-rotate-left-btn", function (e) {
		e.preventDefault();
		$.ajax({
			type: "POST",
			url: $(this).data("post-adress"),
			data: {
				csrfmiddlewaretoken: Cookies.get("csrftoken"),
			},
			success: function (response) {
                rotateImage(-90);
			},
			error: function () {
				errorToast();
			}
		})
	});

	$(document).on("click", ".photo-rotate-right-btn", function (e) {
		e.preventDefault();
		$.ajax({
			type: "POST",
			url: $(this).data("post-adress"),
			data: {
				csrfmiddlewaretoken: Cookies.get("csrftoken"),
			},
			success: function (response) {
                rotateImage(+90);
			},
			error: function () {
				errorToast();
			}
		})
	});

});	
