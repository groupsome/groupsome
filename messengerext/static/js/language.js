//Default confirmation texts
closeSurveyText = "Do you really want to close this survey?"
deleteSurveyText = "Do you really want to delete this survey?"
deleteAudioText = "Do you really want to delete this audio?"
deleteEventText = "Do you really want to delete this event?"
deleteFileText = "Do you really want to delete this file?"
deleteDirectoryText = "Do you really want to delete this directory and its content?"
deleteLinkText = "Do you really want to delete this link?"
deleteVideoText = "Do you really want to delete this video?"
addPictureToAlbum = "Successfully added to album"
removePictureFromAlbum = "Successfully removed from album"

$(function () {
	var userLang = navigator.language || navigator.userLanguage;

	if(userLang != null){
		userLang = userLang.substring(0,2)


		if(userLang == "de"){
			$('#timepicker1').timepicker({showMeridian: false});

			$('.pickercontainer .input-group.date').datepicker({
				language: "de",
				autoclose: true,
				todayHighlight: true,
				format: "dd.mm.yyyy"
			});

			closeSurveyText = "Möchten Sie die Umfrage wirklich schließen?"
			deleteSurveyText = "Möchten Sie die Umfrage wirklich löschen?"
			deleteAudioText = "Möchten Sie die Audio Datei wirklich löschen?"
			deleteEventText = "Möchten Sie den Termin wirklich löschen?"
			deleteFileText = "Möchten Sie die Datei wirklich löschen?"
			deleteDirectoryText = "Möchten Sie das Verzeichnis und den Inhalt wirklich löschen?"
			deleteLinkText = "Möchten Sie den Link wirklich löschen?"
			deleteVideoText = "Möchten Sie das Video wirklich löschen?"
			addPictureToAlbum = "Erfolgreich zu Album hinzugefügt"
			removePictureFromAlbum = "Erfolgreich von Album entfernt"

			moment.locale(userLang);
		} //supported languages can be added here
		else{
			setEnglish();
		}
	}
	//default english
	else{
		setEnglish();
	}

});

function setEnglish(){


	$('#timepicker1').timepicker({showMeridian: true});

	$('.pickercontainer .input-group.date').datepicker({
		language: "en",
		autoclose: true,
		todayHighlight: true,
		format: "dd.mm.yyyy"
	});

	moment.locale("en");

}