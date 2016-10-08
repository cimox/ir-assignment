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

            $.post("autocomplete/" + request.term + '/', function (data, status, xhr) {
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
});