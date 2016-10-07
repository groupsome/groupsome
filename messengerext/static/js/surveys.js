$(function () {


	$(".closed-survey").addClass("hidden");

	$(".survey-select :input").change(function() {
		if($('#id_open input[type="radio"]:checked').length) {
			$(".open-survey").removeClass("hidden");
			$(".closed-survey").addClass("hidden");
		}
		else if($('#id_closed input[type="radio"]:checked').length) {
			$(".closed-survey").removeClass("hidden");
			$(".open-survey").addClass("hidden");
		}
	});


    if(window.location.href.includes("create_survey")){
         $("#cancel-button-modal").hide();
         $("#cancel-button-link").removeClass("hidden");
    }

    if(window.location.href.includes("edit_survey")){
         $("#cancel-button-modal").hide();
         $("#cancel-button-link").removeClass("hidden");
    }



    $(document).on("click", ".survey-details-btn", function (e) {
        e.preventDefault();
        $data = $(this).parents(".survey-list");
        $details = $data.find("div.survey-list-details");
        $button = $(this);
        $details.slideToggle(500, function () {
            if($details.is(":visible")){
                $button.text($button.data("hide"))
            }else{
                $button.text($button.data("show"))
            }
        });
    });


	$('.dropdown-menu .form-list').on('click', function(e){
		e.preventDefault();
		$(this).parent().parent().parent().children().first().val($(this).html());
	});

	window.scrollTo = function( x,y ){
        return true;
    }


    $(document).on("click", ".survey-delete-btn", function (e) {
        e.preventDefault();
        if (!confirm(deleteSurveyText))
                return;

        var survey = $(this).parents(".survey-list");
        $.ajax({
            type: "GET",
            url: "/surveys/"+$(this).data("survey-id")+"/delete",
            data: {
                csrfmiddlewaretoken: Cookies.get("csrftoken"),
            },
            success: function (response) {
                toast(response.message);
                survey.remove();
            },
            error: function () {
                errorToast();
            }
        })
    });

    $(document).on("click", ".survey-send-result-btn", function (e) {
        e.preventDefault();

        var survey = $(this).parents(".survey-list");
        $.ajax({
            type: "POST",
            url: "/surveys/"+$(this).data("survey-id")+"/send",
            data: {
                csrfmiddlewaretoken: Cookies.get("csrftoken"),
            },
            success: function (response) {
                toast(response.message);
            },
            error: function () {
                errorToast();
            }
        })
    });

    $(document).on("click", ".survey-resend-btn", function (e) {
        e.preventDefault();

        var survey = $(this).parents(".survey-list");
        $.ajax({
            type: "POST",
            url: "/surveys/"+$(this).data("survey-id")+"/resend",
            data: {
                csrfmiddlewaretoken: Cookies.get("csrftoken"),
            },
            success: function (response) {
                toast(response.message);
            },
            error: function () {
                errorToast();
            }
        })
    });

    $(document).on("click", ".survey-close-btn", function (e) {
        e.preventDefault();
        if (!confirm(closeSurveyText))
                return;

        var survey = $(this).parents(".survey-list");
        $.ajax({
            type: "GET",
            url: "/surveys/"+$(this).data("survey-id")+"/close",
            data: {
                csrfmiddlewaretoken: Cookies.get("csrftoken"),
            },
            success: function (response) {
                survey.html(response.html);
                survey.removeClass("open-survey")
                survey.addClass("closed-survey")
                $('#id_closed').click();
                toast(response.message);
                $('html, body').animate({
					scrollTop: (survey.offset().top - 10)
				}, 700);

            },
            error: function () {
                errorToast();
            }
        })
    });

    $(document).on("click", ".survey-vote-btn", function (e) {
        e.preventDefault();

        var survey = $(this).parents(".survey-list");
        var choice_id = ""
        var choices = $(this).parent().find('input:checked').each(function(){choice_id += $(this).val()+"-"})
        if(choice_id == "")
        	choice_id = "-"

        $.ajax({
            type: "GET",
            url: "/surveys/"+$(this).attr("name")+"/"+choice_id+"/vote_survey",
            data: {
                csrfmiddlewaretoken: Cookies.get("csrftoken"),
            },
            success: function (response) {
				survey.html(response.html);
				toast(response.message);
            },
            error: function () {
                errorToast();
            }
        })
    });

    $(document).on("click", ".survey-change-vote-btn", function (e) {
        e.preventDefault();

        var parent = $(this).parent();
        parent.addClass("hidden")
        parent.next().removeClass("hidden")
    });

    $(document).on("click", ".survey-cancel-vote-btn", function (e) {
        e.preventDefault();

        var parent = $(this).parent();
        parent.addClass("hidden")
        parent.prev().removeClass("hidden")
    });

	$(document).on("click", ".show-voted-users.has-votes", function (e) {
        e.preventDefault();

		var users_div = $(this).next();
        if(users_div.hasClass("hidden"))
        	users_div.removeClass("hidden")
        else
			users_div.addClass("hidden")
    });

    $(document).on("click", ".attend-link", function (e) {
        e.preventDefault();
        var survey = $(this).parents(".survey-list");
        $.ajax({
            type: "GET",
            url: "/surveys/"+$(this).data("survey-id")+"/"+$(this).data("status")+"",
            data: {
                        csrfmiddlewaretoken: Cookies.get("csrftoken"),
            },
            success: function (response) {
                survey.html(response);
            },
            error: function () {
                error.Toast();
            }
        })
    });

    $('#editSurvey').on('show.bs.modal', function (survey) {
        var button = $(survey.relatedTarget);
        var survey_id = button.data('survey-id');
        var modal = $(this);
        $.ajax({
            type: "GET",
            url: "/surveys/"+survey_id+"/edit_survey",
            data: {
               csrfmiddlewaretoken: Cookies.get("csrftoken"),
            },
            success: function (response) {
                modal.find(".modal-body").html(response);
                addAddBtnEvent();
                addRemoveBtnEvent();
            },
            error: function () {
                 error.Toast();
            }
        })
    });

	addAddBtnEvent();
	addRemoveBtnEvent();

	locationStr = document.location+''

	if(locationStr.lastIndexOf("/")+1== locationStr.length)
		locationStr = locationStr.substr(0,locationStr.length-1)

	if(locationStr.substr(locationStr.lastIndexOf("/")+1) != "surveys" ){
		id = locationStr.substr(locationStr.lastIndexOf("/")+1, locationStr.length)
		if(id){
			$selectedSurvey = $("#surveylist").find("[data-survey-id=\""+id+"\"]:first")
			if($selectedSurvey.length > 0){
				$('html, body').animate({
					scrollTop: ($selectedSurvey.offset().top - 10)
				}, 700);
			}
		}
	}
});

function addAddBtnEvent(){

	$('#add-option-btn').on('click',
		function (e){

			$('#remove-option-btn').parent().remove()

			option_counter = $(this).parent().parent().prev().children().eq(1).children().first().attr('name').split("_")[1]
			option_label = $(this).parent().parent().prev().children().eq(0).html().replace(option_counter,option_counter-0+1)
			option_counter = option_counter - 0 + 1

			html =  '<div class="form-group">'
			html +=	'	<label class="col-md-2 control-label">'+option_label+'</label>'
            html += '   <div class="col-md-3">'
            html += '   	<input class="form-control" required name="option_'+option_counter+'" id="option_'+option_counter+'" maxlength="30" type="text" >'
            html += '   </div>'
            html += '   <div class="col-md-1 ">'
            html +=  '   	<div class="distance-div hidden-lg hidden-md"> </div>'
            html += '   	<div id="remove-option-btn" class="btn btn-default">'
            html += '       	<span class="glyphicon glyphicon-minus" aria-hidden="true"></span>'
            html += '   	</div>'
            html += '   </div>'
            html += '</div>'

            $(this).parent().parent().before(html)
            addRemoveBtnEvent();
		}
	);

	$('#add-option-btn-edit').on('click',
		function (e){

			$('#remove-option-btn-edit').parent().remove()

			option_counter = $(this).parent().parent().prev().children().eq(1).children().first().attr('name').split("_")[1]
			option_label = $(this).parent().parent().prev().children().eq(0).html().replace(option_counter,option_counter-0+1)
			option_counter = option_counter - 0 + 1

			html =  '<div class="form-group">'
			html +=	'	<label class="col-md-2 control-label">'+option_label+'</label>'
            html += '   <div class="col-md-3">'
            html += '   	<input class="form-control" required name="option_'+option_counter+'" id="option_'+option_counter+'" maxlength="30" type="text" >'
            html += '   </div>'
            html += '   <div class="col-md-1 ">'
            html +=  '   	<div class="distance-div hidden-lg hidden-md"> </div>'
            html += '   	<div id="remove-option-btn-edit" class="btn btn-default">'
            html += '       	<span class="glyphicon glyphicon-minus" aria-hidden="true"></span>'
            html += '   	</div>'
            html += '   </div>'
            html += '</div>'

            $(this).parent().parent().before(html)
            addRemoveBtnEvent();
		}
	);

}

function addRemoveBtnEvent(){

	$('#remove-option-btn').on('click',
		function (e){
			option_counter = $(this).parent().parent().prev().children().eq(1).children().first().attr('name').split("_")[1]-0

			if(option_counter > 2){
				html =  '   <div class="col-md-1 ">'
            html +=  '   	<div class="distance-div hidden-lg hidden-md"> </div>'
				html += '   	<div id="remove-option-btn" class="btn btn-default">'
				html += '       	<span class="glyphicon glyphicon-minus" aria-hidden="true"></span>'
				html += '   	</div>'
				html += '   </div>'
				$option= $(this).parent().parent()
				$prev = $option.prev()
				$option.remove();
				$prev.append(html);
			}
			else{
				$option= $(this).parent().parent()
				$option.remove();
			}

			addRemoveBtnEvent();
		}
	);

	$('#remove-option-btn-edit').on('click',
		function (e){
			option_counter = $(this).parent().parent().prev().children().eq(1).children().first().attr('name').split("_")[1]-0

			if(option_counter > 2){
				html =  '   <div class="col-md-1 ">'
            	html +=  '   	<div class="distance-div hidden-lg hidden-md"> </div>'
				html += '   	<div id="remove-option-btn-edit" class="btn btn-default">'
				html += '       	<span class="glyphicon glyphicon-minus" aria-hidden="true"></span>'
				html += '   	</div>'
				html += '   </div>'
				$option= $(this).parent().parent()
				$prev = $option.prev()
				$option.remove();
				$prev.append(html);
			}
			else{
				$option= $(this).parent().parent()
				$option.remove();
			}

			addRemoveBtnEvent();
		}
	);
}