$(function () {
	var playAudio = function (id, btn) {
		var audio = document.getElementById("audio-"+id);
		if (audio.paused) {
			audio.play();
			btn.innerHTML = '<span class="glyphicon glyphicon-pause" aria-hidden="true"></span>';
		} else {
			audio.pause();
			btn.innerHTML = '<span class="glyphicon glyphicon-play" aria-hidden="true"></span>';
		}
	};

	var muteAudio = function (id, btn) {
		var audio = document.getElementById("audio-"+id);
		audio.muted =! audio.muted;
		if (audio.muted) {
			btn.innerHTML = '<span class="glyphicon glyphicon-volume-off" aria-hidden="true"></span>';
		} else {
			btn.innerHTML = '<span class="glyphicon glyphicon-volume-up" aria-hidden="true"></span>';
		}
	};
	
	var seekTo = function (evt,id) {
		var audio = document.getElementById("audio-"+id);
		var progressBar = document.getElementById("audio-progress-"+id);
		var duration = audio.duration;
		if (!isFinite(duration)) duration = $(audio).data("duration");
		var percent = evt.offsetX / progressBar.offsetWidth;
		audio.currentTime = percent * duration;
		progressBar.value = percent * 100;
	};

	window.updateAudioProgressBar = function (id) {
		var audio = document.getElementById("audio-"+id);
		var progressBar = document.getElementById("audio-progress-"+id);
		if (!progressBar) return;
		var duration = audio.duration;
		if (!isFinite(duration)) duration = $(audio).data("duration");
		var percent = Math.floor((100 / duration) * audio.currentTime);
		progressBar.value = percent;
	};
	
	$(document).on("click", ".audio-play-button", function (e) {
		var controls = $(this).parents(".audiocontrols");
		playAudio(controls.data("audio-id"), $(this).get(0));
	});
	
	$(document).on("click", ".audio-mute-button", function (e) {
		var controls = $(this).parents(".audiocontrols");
		muteAudio(controls.data("audio-id"), $(this).get(0));
	});
	
	$(document).on("click", ".audio-progress", function (e) {
		var controls = $(this).parents(".audiocontrols");
		seekTo(e, controls.data("audio-id"), $(this).get(0));
	});
});
