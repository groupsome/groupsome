$(function () {
	if ($("#cookieconsent-script").length) {
		window.cookieconsent_options = {
			message: $("#cookieconsent-script").data("message"),
			dismiss: $("#cookieconsent-script").data("dismiss"),
			learnMore: $("#cookieconsent-script").data("learn-more"),
			link: $("#cookieconsent-script").data("link"),
			theme: $("#cookieconsent-script").data("theme"),
			markup: [
                '<div class="cc_banner-wrapper {{containerClasses}}">',
                '<div class="cc_banner cc_container cc_container--open">',
                '<a href="#null" data-cc-event="click:dismiss" target="_blank" class="cc_btn cc_btn_accept_all">{{options.dismiss}}</a>',

                '<p class="cc_message">{{options.message}} <a data-cc-if="options.link" target="{{ options.target }}" class="cc_more_info" href="{{options.link || "#null"}}">{{options.learnMore}}</a></p>',
                '</div>',
                '</div>'
              ]
		};
	}
});
