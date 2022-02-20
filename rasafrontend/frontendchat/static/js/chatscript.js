console.log('chatscript.js');

function submit_post() {
    var input = $("#inputtextbox").val();
    var csrft = $('input[name=csrfmiddlewaretoken]').val();
    console.log(uname);
    if (input != "") {
        document.getElementById("scrollintoviewdiv").outerHTML = "";
        document.getElementById("inputtextbox").value = "";
        document.getElementById("bodyofchat").innerHTML += "<div class=\"outgoing\"><div class=\"bubble lower\"><p>"+input+"</p></div></div>";
        document.getElementById("bodyofchat").innerHTML += "<div class=\"bubble\" id=\"typinganim\"><div class=\"ellipsis dot_1\"></div><div class=\"ellipsis dot_2\"></div><div class=\"ellipsis dot_3\"></div></div>";
        document.getElementById("bodyofchat").innerHTML += "<div id=\"scrollintoviewdiv\"></div>";
        document.getElementById("scrollintoviewdiv").scrollIntoView({behavior: "smooth"});
        fetch('/chat/post/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrft
            },
            body: JSON.stringify({
                input: input,
                uname: uname,
            })
        }).then(function(response) {
            return response.json();
        }
        ).then(function(data) {
            console.log(data);
            //for loop through data
            for (var i = 0; i < data.length; i++) {
                var text = data[i];
                document.getElementById("bodyofchat").innerHTML += "<div class=\"incoming\"><div class=\"bubble\"><p>"+text+"</p></div></div>";
            }
            document.getElementById("bodyofchat").innerHTML += "<div id=\"scrollintoviewdiv\"></div>";
            document.getElementById("typinganim").outerHTML = "";
            document.getElementById("scrollintoviewdiv").scrollIntoView({behavior: "smooth"});
        });
    }
}