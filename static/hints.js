function resetHints() {
    $("#trackList").hide();
    $(".hint").hide();
    $(".hintChk").prop("checked", false);
    $("#showBtn").prop("disabled", false);
    $(".hintChk").prop("disabled", false);
}
function hideAndLockHints() {
    $("#trackList").show();
    $(".hint").hide();  // continuing to show hints would be redudant
    $(".hintChk").prop("checked", false);
    $("#showBtn").prop("disabled", true);  // once details are shown, it's permanent
    $(".hintChk").prop("disabled", true);  // once details are shown, hints are redundant
}
function loadTrackHints(track) {
    $("#hintYear").html("Year: " + track.year);
    var firstLetter = track.artist[0];
    var secondLetter = "(no second letter)";
    if (track.artist.length > 1) {
        secondLetter = track.artist[1];
    }
    $("#hintArtist1stLetter").html("Artist 1st Letter: " + firstLetter);
    $("#hintArtist2ndLetter").html("Artist 2nd Letter: " + secondLetter);
}
function initHints() {
    $("#showBtn").click(function() {
        hideAndLockHints();
    });
    $("#hintYearChk").click(function() {
        $("#hintYear").toggle();
    });
    $("#hintArtist1stLetterChk").click(function() {
        $("#hintArtist1stLetter").toggle();
    });
    $("#hintArtist2ndLetterChk").click(function() {
        $("#hintArtist2ndLetter").toggle();
    });
}