
// Code for the magic search box
$(document).ready(function() {


    var bestGuess = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        remote: {
            url: '/confirmations/api/search/%QUERY',
            wildcard: '%QUERY',
        },
    });

    
    $('.typeahead').typeahead({autoselect: true,
                              },
                              {name: 'search',
                               display: 'value',
                               source: bestGuess,
                               limit: 100,
                              });
});


// We want to keep controld of users not doing cross posting, so we
// need this function to fetch cookies from the user.

function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie != '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
          var cookie = jQuery.trim(cookies[i]);
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) == (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
};
