$(function(){let mySwiper2=new Swiper('#our-ser-list',{autoplay:{delay:10000,stopOnLastSlide:false,disableOnInteraction:true,},speed:1000,loop:true,paginationClickable:true,autoplayDisableOnInteraction:false,touchMoveStopPropagation:false,navigation:{nextEl:'.our-ser-btn .button-next',prevEl:'.our-ser-btn .button-prev',},})});
$('.home-hotpro .hotpro-main .home-title').text('Turn your ideas into marketable cap & label & paper box')
if($('.homethriveSwiper').length){var homethriveSwiper = new Swiper(".homethriveSwiper", {spaceBetween: 10,speed:1000,navigation: {nextEl: ".homethrive-btn-right",prevEl: ".homethrive-btn-left"}});}
$('.home-banner').append($('.homebanner-text'))
$('.home-news').before($('.home-middle'))
$(".home-middle #box li").eq(0).addClass("active");
$(".home-middle #box li").click(function () {
  var index = $(this).index();
  $(this).addClass("active").siblings().removeClass("active");
});
if ($(window).width() > 768) {
  $(".home-middle #box li")
    .eq(0)
    .css("width", "75%")
    .siblings()
    .css("width", "11%");
  $(".home-middle #box li")
    .eq(0)
    .css("width", "75%")
    .siblings()
    .find(".dingw")
    .hide();
  $(".home-middle #box li").click(function () {
    $(this).addClass("active");
    $(this).css("width", "75%");
    $(this).find(".dingw").show();
    $(this).find(".jcfwx").hide();
    $(this).siblings().css("width", "11%");
    $(this).siblings().find(".dingw").hide();
    $(this).siblings().find(".jcfwx").show();
  });
}
if ($(window).width() <= 768) {
  $(".home-middle #box li").click(function () {
    $(this).css("height", "190px");
    $(this).find(".tt02").show();
    $(this).siblings().find(".tt02").hide();
    $(this).siblings().css("height", "100px");
  });
}
if($("main.pro-main").length||$("main.protype-main").length){$(".home-contant").remove()}
let liht=''
$(".nav-ul>li").each(function(){
liht += `<li><a href="${ $(this).children("a").attr("href")}">${$(this).children("a").text()}</a></li>`
console.log(liht);
})
$("footer .foot-item:nth-child(2) .foot-list").html(liht)
if($('.indexproserviceSwiper').length){var indexproserviceSwiper = new Swiper(".indexproserviceSwiper",{loop:true,pagination:{el:".indexproservice-swiper-pagination",clickable: true,},breakpoints: {0: {slidesPerView: 1,slidesPerGroup:1},769: {slidesPerGroup:2,slidesPerView: 2}}});}


if(window.innerWidth>768){
$("#videobox .inner-page").append(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 68 48"><path d="M66.52 7.74c-.78-2.93-2.49-5.41-5.42-6.19C55.79.13 34 0 34 0S12.21.13 6.9 1.55c-2.93.78-4.63 3.26-5.42 6.19C.06 13.05 0 24 0 24s.06 10.95 1.48 16.26c.78 2.93 2.49 5.41 5.42 6.19C12.21 47.87 34 48 34 48s21.79-.13 27.1-1.55c2.93-.78 4.64-3.26 5.42-6.19C67.94 34.95 68 24 68 24s-.06-10.95-1.48-16.26z" fill="red"></path><path d="M45 24 27 14v20" fill="white"></path></svg>`)
$("#videobox li").click(function(){
$("body").append(`<div class="body-v-bg"><div class="body-v-box"><div class="body-v-top"><div class="body-v-title">${$(this).find(".tt01").text()}</div><div class="body-v-feexit"><span></span><span></span></div></div><div class="body-viceo"><video controls><source src="${$(this).find("source").attr("src")}"></video></div></div></div>`)
$(".body-viceo video").get(0).play()
$(".body-v-feexit").click(function(){$(".body-v-bg").remove()})})}
if($('.head-info .m-menu').is(':visible')){$('.head-info .m-menu').before($('.head-nav .search-box'))}
$('ul.submenu.nav4 li').each(function(){if($(this).find('>.cate2-item').length){$(this).addClass('navcateli')}})
$('#liproducts .nav4>li .cate2-item >li:first-child').addClass('navcatesmli')
$('#liproducts .nav4>li:first-child').addClass('navcateact');
$('#liproducts').hover(function(){$('#liproducts .nav4>li:first-child').addClass('navcateact').siblings().removeClass('navcateact');})
$('#liproducts .nav4>li').hover(function(){$(this).addClass('navcateact').siblings().removeClass('navcateact')})
$('#liproducts .nav4>li .cate2-item >li').hover(function(){$(this).addClass('navcatesmli').siblings().removeClass('navcatesmli')})
if($('#liproducts .nav4>li .cate2-item li img').length){$('#liproducts .nav4>li .cate2-item li img').each(function(){
let relsrc = $(this).attr('src').split("?");
relsrc = String(relsrc[0]);
$(this).attr('src',relsrc)
})}