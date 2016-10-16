/**
 * Created by cimo on 08/10/2016.
 */
$(function () {
    var cache = {};
    $("#search").autocomplete({
        minLength: 2,
        source: function (request, response) {
            var term = request.term;
            if (term in cache) {
                response(cache[term]);
                return;
            }

            $.post("http://127.0.0.1:8080/autocomplete/" + request.term + '/', function (data, status, xhr) {
                cache[term] = data['autocomplete'];
                response(data['autocomplete']);
            });
        },
        select: function (event, ui) {
            console.log('item selected: ' + ui);
            $.parseHTML(ui.content);
        },
        messages: {
            noResults: '',
            results: function () {}
        }
    });

    search = function (start, end) {
        var query = $('#search').val();
        window.location.href = "http://127.0.0.1:8080/search/" + query + '/' + start + '/' + end + '/';
    };

    $("a#article-url").on('click', function () {
        var articleUrl = $(this).attr('url');
        var articleTitle = $(this).text();
        $.redirect('http://127.0.0.1:8080/article/', {'query': articleUrl, 'title': articleTitle});
    });

    $("a#more-article-url").on('click', function () {
        var articleUrl = $(this).attr('url');
        var articleTitle = $(this).find('h5').text();
        $.redirect('http://127.0.0.1:8080/article/', {'query': articleUrl, 'title': articleTitle});
    });
});