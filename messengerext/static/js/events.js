$(function () {
	$(".cal-select :input").change(function() {
		if(document.getElementById("cal").checked) {
			 $("#calendar").removeClass("hidden");
			 $("#eventlist").addClass("hidden");
			 $('#calendar').fullCalendar('render');
		}else if(document.getElementById('list').checked) {
			$("#eventlist").removeClass("hidden");
			$("#calendar").addClass("hidden");
		}
	});


    if(window.location.href.includes("create_event")){
         $("#cancel-button-modal").hide();
         $("#cancel-button-link").removeClass("hidden");
    }

    if(window.location.href.includes("edit_event")){
         $("#cancel-button-modal").hide();
         $("#cancel-button-link").removeClass("hidden");
    }

    $(document).on("click", ".form-allday", function (e) {
        var elements = document.getElementsByName("time");
        if($('.form-allday').is(':checked')) {
             for (i = 0; i<elements.length; i++){
                 elements[i].setAttribute('disabled','disabled');
             }
        }else{
             for (i = 0; i<elements.length; i++){
                 elements[i].removeAttribute('disabled');
             }
        }
    });


    $(document).on("click", ".event-details-btn", function (e) {
        e.preventDefault();
        $data = $(this).parents(".event-list");
        $details = $data.find("div.event-list-details");
        $button = $(this);
        $details.slideToggle(500, function () {
            showIcon = "<div style=\"margin-right:5px;\" class=\"glyphicon glyphicon-info-sign\"> </div>"
            hideIcon = "<div style=\"margin-right:5px;\" class=\"glyphicon glyphicon-menu-up\"> </div>"
            if($details.is(":visible")){
                $button.html(hideIcon + $button.data("hide"))

            }else{
                $button.html(showIcon + $button.data("show"))
            }
        });
    });

/*
	$(".event-list").hover(
		function () {
			$(this).find("span.event-more").removeClass("hidden");
		},
		function () {
			$(this).find("span.event-more").addClass("hidden");
		}
	);*/

	if ($("#calendar").length) {
		$('#calendar').fullCalendar({
			height: 0.75*$(window).height(),
			events: $('#calendar').data("events"),
			timeFormat: 'H(:mm)',
			eventRender: function(event, element) {
				element.find('.fc-title').append("<br/>" + event.location + "<br/>" + event.description);
			}
		});
	}

	$('.dropdown-menu .form-list').on('click', function(e){
		e.preventDefault();
		$(this).parent().parent().parent().children().first().val($(this).html());
	});

	window.scrollTo = function( x,y ){
        return true;
    }


    $(document).on("click", ".event-delete-btn", function (e) {
        e.preventDefault();
        if (!confirm(deleteEventText))
                return;

        var event = $(this).parents(".event-list");
        $.ajax({
            type: "GET",
            url: "/events/"+$(this).data("event-id")+"/delete",
            data: {
                csrfmiddlewaretoken: Cookies.get("csrftoken"),
            },
            success: function (response) {
                toast(response.message);
                event.remove();
            },
            error: function () {
                errorToast();
            }
        })
    });

    $(document).on("click", ".attend-link", function (e) {
        e.preventDefault();
        var event = $(this).parents(".event-list");
        $.ajax({
            type: "GET",
            url: "/events/"+$(this).data("event-id")+"/"+$(this).data("status")+"",
            data: {
                        csrfmiddlewaretoken: Cookies.get("csrftoken"),
            },
            success: function (response) {
                event.html(response);
            },
            error: function () {
                error.Toast();
            }
        })
    });

    $('#editEvent').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        var event_id = button.data('event-id');
        var modal = $(this);
        $.ajax({
            type: "GET",
            url: "/events/"+event_id+"/edit_event",
            data: {
               csrfmiddlewaretoken: Cookies.get("csrftoken"),
            },
            success: function (response) {
                modal.find(".modal-body").html(response);
            },
            error: function () {
                 error.Toast();
            }
        })
    });
});

