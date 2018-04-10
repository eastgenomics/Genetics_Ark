
$(document).ready(function() {


    var bestGuess = new Bloodhound({
	datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
	queryTokenizer: Bloodhound.tokenizers.whitespace,
	remote: {
	    url: '/genetics_ark/api/search/%QUERY',
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