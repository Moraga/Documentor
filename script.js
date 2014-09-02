$('nav li').on('click', function() {
    var self = $(this),
	parent = this.parentNode;
    
    if (parent.id == 'property' || parent.id == 'method') {
		$('html,body').animate({scrollTop: $('#i' + self.attr('rel')).offset().top}, 'normal');
    }
    else if (parent.id == 'category') {
		if (self.hasClass('active')) {
			self.removeClass('active');
			$('div').show();
			$('#property li, #method li').show();
		}
		else {
			self.siblings().removeClass('active').end().addClass('active');
			$('div').hide();
			var li = [];
			$('ol li').filter('[title=category]').filter(':contains('+ self.html() +')').each(function() {
				li.push('[rel=' + $(this).parents('div').show().attr('id').substr(1) +']');
			});
			$('#property li, #method li').hide().filter(li.join(',')).show();
		}
    }
});