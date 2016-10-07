$.ajax({
			type: "POST",
			url: "/settings/update_timezone",
			data: {
				csrfmiddlewaretoken: Cookies.get("csrftoken"),
                off: (new Date).getTimezoneOffset(),
				tz: moment.tz.guess()
			}
});