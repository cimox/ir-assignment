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
        query = $('#search').val();
        window.location.href = "http://127.0.0.1:8080/search/" + query + '/' + start + '/' + end + '/';
    }
});