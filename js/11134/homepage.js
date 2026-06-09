$("#videobox .inner-page").click(function(event) {
 var a=$(this).find('img').attr('data-link');
 $('.popwindow-video video').attr({'src':a,'controls':'controls'})
 $('.popwindow-video').show()
 $(document).one("click",function() {$('.popwindow-video').hide();$('.popwindow-video video').attr({'src':' '})});
 event.stopPropagation();
});
$('.popwindow-video video').click(function(event) {
 event.stopPropagation();
});