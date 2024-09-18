$(function() {
    /*
    This is not an ideal way of doing this, here on the JS side.
    TODO: Modify python side to include cover url in media info.
    A side-effect of doing it this way is that '+' in filenames 
    is going to cause problems. That's ok with me because I don't 
    allow '+' in my filenames.
    */
    var trackUrl = $("#trackList a.trackLink:first").attr("href");
    var tokens = decodeURIComponent(trackUrl).replace(/\+/g, " ").split("/");
    var coverUrl = tokens.slice(0, -1).join("/") + "/cover.jpg";
    $("#coverImg").attr("src", coverUrl);
});
