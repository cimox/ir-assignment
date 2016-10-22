/**
 * Created by cimo on 22/10/2016.
 */

$(function () {
    articlesOverTimeChart = function (dates, values) {
        $('#container').highcharts({
            title: {
                text: 'Count of published articles over time'
            },
            xAxis: {
                title: {
                    text: 'Time'
                },
                categories: dates
            },
            yAxis: {
                title: {
                    text: 'Count of published articles'
                },
                plotLines: [{
                    value: 0,
                    width: 1,
                    color: '#808080'
                }]
            },
            legend: {
                layout: 'vertical',
                align: 'right',
                verticalAlign: 'middle',
                borderWidth: 0
            },
            series: [{
                name: 'Published articles',
                data: values
            }]
        });
    };

    var dates = [], values = [];
    $.getJSON('/articles_over_time/', function (data) {
        dates = data['articles_over_time']['dates'];
        values = data['articles_over_time']['values'];
        articlesOverTimeChart(dates, values);
    });

    articlesLnHistogram = function (data) {
        console.log(data);
        $('#container-articles-over-time').highcharts({
            chart: {
                type: 'scatter',
                zoomType: 'xy'
            },
            title: {
                text: 'Article length versus count of articles'
            },
            xAxis: {
                title: {
                    enabled: true,
                    text: 'Chars'
                },
                startOnTick: true,
                endOnTick: true,
                showLastLabel: true
            },
            yAxis: {
                title: {
                    text: 'Articles'
                }
            },
            legend: {
                layout: 'vertical',
                align: 'right',
                verticalAlign: 'top',
                x: 100,
                y: 70,
                floating: true,
                backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF',
                borderWidth: 1
            },
            plotOptions: {
                scatter: {
                    marker: {
                        radius: 5,
                        states: {
                            hover: {
                                enabled: true,
                                lineColor: 'rgb(100,100,100)'
                            }
                        }
                    },
                    states: {
                        hover: {
                            marker: {
                                enabled: false
                            }
                        }
                    },
                    tooltip: {
                        headerFormat: '<b>{series.name}</b><br>',
                        pointFormat: '{point.x} chars, {point.y} articles'
                    }
                }
            },
            series: [{
                name: 'Article',
                color: 'rgba(223, 83, 83, .5)',
                data: data
            }]
        });
    };
    $.getJSON('/articles_ln_histogram/', function (data) {
        console.log(data['articles_ln_histogram'])
        articlesLnHistogram(data['articles_ln_histogram']);
    });
});