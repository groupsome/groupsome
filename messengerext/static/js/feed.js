window.prepareAudios = function () {
 $("audio").each(function () {
				$(this).on("timeupdate", function (e) {
					updateAudioProgressBar($(this).data("audio-id"));
				});
			});
}

$(function () {
    var UPDATE_INTERVALL = 60*1000;
    var feed = $('.feed');
    // layout Masonry after each image loads, needed for group view
    feed.imagesLoaded().progress( function() {
      feed.masonry();
      prepareAudios();
    });

    var updateFeed = function () {
		var groups = $('.feed-select input[type="checkbox"]:checked').map(function () {
			return $(this).val();
		}).get();

        newest_item_timestamp = $('.timestamp').first().text();
        var url = '/home?newest-item-timestamp='+ newest_item_timestamp + '&group=' + groups.join('&group=') + "#content";
        $.ajax({
            url: url,
            type: "GET",
        }).success(function(response){
            if (response.length > 0){
                var feed = $('.feed');
                feed.prepend(response);
                feed.imagesLoaded().progress( function() {
                  feed.masonry("reloadItems");
                  feed.masonry();
                  prepareAudios();
                });

            }

        });
	}

	var loadFeed = function () {
		var groups = $('.feed-select input[type="checkbox"]:checked').map(function () {
			return $(this).val();
		}).get();
		
		if (groups.length == 0) {
			$(".feed").html("");
			$('#feed-empty').removeClass("hidden");
		} else {
			var url = '/home?group=' + groups.join('&group=') + "#content";
			$.ajax({
				url: url,
				type: "GET",
			}).success(function(response){
                var feed = $('.feed');
				feed.html(response);
                feed.imagesLoaded().progress( function() {
                  feed.masonry("reloadItems");
                  feed.masonry();
                  prepareAudios();
                });

                setInterval(function(){updateFeed()}, UPDATE_INTERVALL);

				if ($('.item').length === 0){
					$('#feed-empty').removeClass('hidden');
				} else{
					$('#feed-empty').addClass('hidden');
				}
				
			});
		}
		
		localStorage.setItem("home-feed-group-selection", JSON.stringify(groups));
	}

	if ($(".feed-select").length) {
		var groups = localStorage.getItem("home-feed-group-selection");
		if (groups != null) {
			groups = JSON.parse(groups);
			for (var i = 0; i < groups.length; i++) {
				$('.feed-select input[type="checkbox"][value="'+groups[i]+'"]')
					.prop("checked", true)
					.parents(".btn-default").addClass("active");
			}
		} else {
			$('.feed-select input[type="checkbox"]').each(function () {
				$(this).prop("checked", true).parents(".btn-default").addClass("active");
			});
		}
		
		$('.feed-select input[type="checkbox"]').on("change", function () {
			loadFeed();
		});
		
		loadFeed();
	}
	
	if ($("[data-endless-paginate]").length) {
		$.endlessPaginate({ paginateOnScroll: true, paginateOnScrollMargin: 20, onCompleted: function(){
            var feed = $('.feed');
            // layout Masonry for next chunk

            feed.imagesLoaded().progress( function() {
                feed.masonry("reloadItems");
                feed.masonry();
                prepareAudios();
            });

		}});
	}

});