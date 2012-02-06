$(document).ready(function() {
	$.getJSON('/data/', function(data) {
		var chart = d3.select('#when').append('div')
			.attr('class', 'chart');
		chart.selectAll('div')
			.data(data)
			.enter().append('div')
				.style('width', function(d) { return d.value*10 + 'px'; })
				.text(function(d) { return d.value; });
	});
});

