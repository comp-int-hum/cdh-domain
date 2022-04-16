jQuery(function($){
  
  // set up our breakpoints
  $.breakpoints([768,979]);
  
  /**
   * Primary navigation (dropdowns)
   *
   * Figure out if the tertiary menus need to be displayed to the left
   * of the submenu
   */
  (function dropdown_fix(){
    
    
    $('#main-nav').find('div > ul > li > ul > li > ul').each(function(){
      
      var $this = $(this)
        , $main_nav = $('#main-nav')
        , $c = $this.parents('div>ul>li')
        , $parent = $this.parent().parent()
        , pw = $parent.width()
        , l = $c.offset().left
        , r = $main_nav.offset().left + $main_nav.width()
      
      if ( l + pw + $this.width() > r ) {
        $this.addClass('left-side');
      }
      
    });

    if (!Modernizr.focuswithin){
      $('#main-nav').find('li.menu-item a').focus(function(ev){
        var parentMenus = $(ev.target).parents('li.menu-item-has-children');
        
        parentMenus.addClass('focus-within-shim');
      });
      $('#main-nav').find('li.menu-item a').focusout(function(ev){
        var parentMenus = $(ev.target).parents('li.menu-item-has-children');

        parentMenus.removeClass('focus-within-shim');
      });
    }
    
  })();
  
  /**
   * Phone Menu
   */
  (function phone_menu(){
    
    var transitionEnd = 'webkitTransitionEnd otransitionend oTransitionEnd msTransitionEnd transitionend';
    
    function PhoneMenu(){
      var self = this;
      
      if( $(window).width() < 768 ){
        this.init();
      }
      else {
        $(window).on('resize', function on_resize(){
          if( $(window).width() < 768 ){
            self.init();
            $(window).off('resize', on_resize);
          }
        });
      }
    }
    
    $.extend(PhoneMenu.prototype, {
      
      visible : false,
      
      init : function(){
        // we need to build our menu...
        this.$el = $('.phone-menu');
        this.$wrap = $('<div />').addClass('phone-menu-wrap').appendTo(this.$el);
        this.$content = $('.content-wrap');
        this.$trigger = $('[data-toggle="phone-menu"]');
        
        this.$search = $('.page-header .widget_search, #page-header .widget_search').clone().appendTo( this.$wrap );
        this.$menu = $('#main-nav').clone().attr('id', 'phone-main-nav').appendTo( this.$wrap );
        
        this.$utility = $('#utility-nav > div').clone().appendTo( this.$wrap );
        
        this.on( this.$trigger, 'click', this.toggle );
        
        this.addDepartments();
        this.initMenu();
        this.$wrap.focusout(function(ev){
          setTimeout(function () {
            var $focus = $(document.activeElement);
            if (!$.contains($('.phone-menu')[0], $focus[0])){
              $('[data-toggle="phone-menu"]').click();
            }
          });
        });
        
      },
      
      addDepartments : function(){
        
        var $ul = this.$menu.find('>div>ul');
        $('#department-nav .view-all-link-container a');
        var $li = $('<li class="menu-item-has-children" />');
        var $a = $('#department-nav .view-all-link-container a').clone();
        if( $a.length ){
          $a.html( $a.text().replace(/\s›/,'') );
        }
        $li.append( $a );
        $li.appendTo($ul);
        $departmentUl = $('<ul />').appendTo($li);
        $('#department-nav li').each(function(){
          $(this).clone().appendTo($departmentUl);
        });
      },
      
      initMenu : function(){
        this.$menu.find('li.menu-item-has-children').each(function(){
          if( !$(this).find('>ul').length ) return;
          $(this).find('>a').prepend('<span class="menu-toggle"><i class="icon-angle-down" /></span>').addClass('has-child-menu');
        });
        var self = this;
        this.$menu.on('click', 'a>.menu-toggle', function(e){
          e.preventDefault();
        });
        this.$menu.on('mousedown', 'a>.menu-toggle', function(e){
          e.preventDefault();
          var $li = $(this).parent().parent(),
              $ul = $li.find('> ul');
          
          if( $li.is(self._cur) ) return;
          
          $li.toggleClass('menu-open');
          if( $li.hasClass('menu-open') ){
            $ul.css({height:0});
            $ul.show();
            $ul.animate({height: $ul.prop('scrollHeight')}, 300, function(){
              $ul.css({height:'auto'});
            });
          }
          else {
            $ul.css({height:$ul.height()});
            $ul.animate({height: 0}, 300, function() {
              $ul.hide();
            });
          }
        });

        this.$menu.on('focus', 'a.has-child-menu', function(e){
          var $target = $(e.target);
          if (!$target.parent().hasClass('menu-open')){
            $(e.target).find('span.menu-toggle').mousedown();
          }
        });

        this.$menu.on('focusout', 'li.menu-item-has-children a', function(e){
          var $target = $(e.target),
              $parentMenu = $($target.parents('li.menu-item-has-children')[0]);
          
          setTimeout(function () {
            var $focus = $(document.activeElement),
                $toggleElement = $parentMenu.find('span.menu-toggle');

            if (-1 === $parentMenu.find('a').index($focus)) {
              $toggleElement.each(function() {
                if ($(this).parent().parent().hasClass('menu-open')){
                  $(this).mousedown();
                }
              });
            }
          }, 0);
        });
      },
      
      on : function( $el, event, fn ){
        var self = this;
        $el.on(event, function(){
          fn.apply(self, arguments);
        });
      },
      
      off : function( $el, event, fn ){
        var self = this;
        $el.off(event, function(){
          fn.apply(self, arguments);
        });
      },
      
      toggle : function(e){
        var self = this;
        e.preventDefault();
        this.open = !$('html').hasClass('phone-menu-open');
        
        var content = $('meta[name=viewport]').attr('content');
        $('html').toggleClass('phone-menu-open');
        
        if( this.open ){
          this.$el.scrollTop(0);
          this.$el.css({top: $(window).scrollTop()});
          setTimeout(function(){
            self.on(self.$content,'touchstart.phonemenu click.phonemenu', self.onContentTouch );
          },1);
          
          $('meta[name=viewport]').attr('content', content+', user-scalable=no');
          // 2019-09-25 rstring3@jhu.edu
          // Added to automatically focus the first element in the menu when it is opened
          this.$el.find('input')[0].focus();
          
        }
        else {
          $('meta[name=viewport]').attr('content', content.replace(/\,\suser\-scalable\=no/, ''));
          this.$content.off('.phonemenu');
          this.$trigger.focus();
        }
        
      },
      
      onContentTouch : function(e){
        e.preventDefault();
        this.toggle(e);
      }
      
    });
    
    var phoneMenu = new PhoneMenu();
    
  })();
  
  /**
   * Navigation toggles
   */
  $('[data-toggle=nav]').click(function(e){
    
    e.preventDefault();
    e.stopPropagation();
    
    var $toggle = $(this)
      , $target = $($(this).attr('href'))
      , open = !$target.hasClass('open')
      
    $target.toggleClass('open');
    
    $(this)[open?'addClass':'removeClass']('active');
    if ( open ) {
      $(document).on('click.navtoggle keyup.navtoggle', document_listener);
      if ( !Modernizr.csstransforms3d && $target.attr('id') === 'department-nav') {
        $target.stop().animate({height: $target.find('.wrap').outerHeight()}, 'fast' );
      }
    }
    else {
      $(document).off('.navtoggle');
      if ( !Modernizr.csstransforms3d && $target.attr('id') === 'department-nav') {
        $target.stop().animate({height: 0}, 'fast' );
      }
    }
    
    function document_listener(e){
      var target = e.target;
      // check to see what the
      if( e.type == 'keyup' && e.keyCode == 27) {
        e.stopPropagation();
        $toggle.click();
      }
      else if( e.type == 'click' && !$(target).is($target) && !$(target).parents().is($target) ){
        e.stopPropagation();
        $toggle.click();
      }
    }
  });
  
  /**
   * Added by rstring3@jhu.edu
   * 2019-9-24
   * When the "Jump to Department & Program Websites" navigation menu loses keyboard focus, call
   * the toggle.click behavior to hide the menu
   */
  $('#department-nav').focusout(function(e){
    var toggle = $('[data-toggle=nav]'),
        navItems = $(this).find('a'),
        navMenu = $(this),
        focus;
    // This needs to be in a setTimeout or the browser thinks the body element has focus
    setTimeout(function () {
      focus = document.activeElement;
      if (-1 === navItems.index(focus) && navMenu.hasClass('open')){
        toggle.click();
      }
    }, 0);
  });

  /**
   * Accordion helper
   */
  (function accordion_helper(){
    
    $('.accordion-toggle')
      .prepend('<i class="icon-plus-sign"></i>')
      .prepend('<i class="icon-minus-sign"></i>');
      
    $('.accordion-group .accordion-body').on('show', function(){
      $(this).parents('.accordion-group').addClass('open');
      
    });
    $('.accordion-group .accordion-body').on('hide', function(){
      $(this).parents('.accordion-group').removeClass('open');
    });
    
    // scroll to top of current after shown
    $('.accordion-group .accordion-body').on('shown', function(){
      if( $.breakpoint() ) return;
      $('.content-wrap').scrollTo( $(this).parent(), 100 );
      
    });
    
  })();
  
  // /**
  //  * Twitter feed
  //  */
  // (function twitter_feed(){
  //   var $el = $('.twitter-feed')
  //     , $nav = $el.find('.twitter-nav')
  //     , $tweets = $el.find('ul.tweets li.tweet')
  //     , rotator = window.twitter_rotator = new Fabrizio_Rotator( $tweets )
  //     , activeAnimation = false
    
  //   rotator.on('change', function(cur, last){
  //     if ( activeAnimation ) {
  //       last = activeAnimation;
  //     }
  //     activeAnimation = $(last).stop().animate({opacity:0}, 'fast', function(){
  //       $(last).css({display:'none'});
  //       activeAnimation = $(cur).css({opacity:0, display:'inline-block'}).animate({opacity:1}, 'fast', function(){
  //         activeAnimation = false;
  //       });
  //     });
  //   });
    
  //   $nav.find('.next').on('click', function(e){ e.preventDefault(); rotator.next(); });
  //   $nav.find('.prev').on('click', function(e){ e.preventDefault(); rotator.prev(); });
    
  // })();
  
  /**
   * Smooth Scrolls on the site
   */
  (function smooth_scrolls(){
    $('a[data-scroll="smooth"]').click(function(e){
      e.preventDefault();
      $.scrollTo( $( $(this).attr('href') ), 400 );
    });
  })();
  
  /**
   * Back to Top button
   
  (function back_to_top(){
    var visible = false,
        $el = $('.back-to-top-container');
        
    function check_height() {
      var wh = $(window).height()
        , bh = $('.content-wrap').height();
        
      if ( bh > wh && !visible ) {
        $el.css({opacity:1});
        visible = true;
      }
      else if ( bh < wh && visible) {
        $el.css({opacity:0});
        visible = false;
      }
    }
    
    function on_scroll(){
      if( $('.content-wrap').scrollTop() > 0 && !visible ){
        $el.css({opacity:1});
        visible = true;
      }
      else if( $('.content-wrap').scrollTop() <= 0 && visible ){
        $el.css({opacity:0});
        visible = false;
      }
    }
    
    $el.on('click', function(){
      $('.content-wrap').scrollTo(0, {duration:200});
    });
    
    $('.content-wrap').on('scroll', on_scroll);
    $(window).on('resize', check_height);
    check_height();
    on_scroll();
    
  })();
  */ 

  /**
   * Slideshows
   */
  (function slideshows(){
    $('.slideshow').each(function(){
      var $slideshow = $(this)
        , $slide_images = $slideshow.find('.slide-images')
        , $images = $slide_images.find('img')
        , $contents = $slideshow.find('.slide-content')
      
      $images.addClass('positioned');
      if( !Modernizr.cssfilters ) $images.eq(0).css({opacity:1});
      
      if ( $images.length < 2 ) {
        // we don't need to do anything in this case
        return;
      }
      
      var rotator = new Fabrizio_Rotator( $images )
        , $controls = $('<div class="span4 controls" aria-controls="slideshow" />').appendTo( $slideshow )
        , $prev = $('<a href="#" aria-label="Previous Slide" class="prev"><i class="icon-chevron-left" /></a>')
          .appendTo($controls)
          .click(function(e){ e.preventDefault(); rotator.prev() })
        , $next = $('<a href="#" aria-label="Next Slide" class="next"><i class="icon-chevron-right" /></a>')
          .appendTo($controls)
          .click(function(e){ e.preventDefault(); rotator.next() })
        
      // add our buttons
      for(var i=0; i<$images.length; i++) {
        (function(i){
          $('<a class="bullet'+(!i?' active-bullet" aria-current="true':'')+'" aria-label="Display Slide '+(i+1)+'" href="#"><i class="icon-radio-unchecked" /></a>"').click(function(e){
            e.preventDefault(); 
            rotator.go(i);
          }).insertBefore($next);
        })(i);
      }
      
      
      rotator.on('change', function(cur, last, curIndex, lastIndex){
        if( cur === undefined ) return;
        $contents.removeClass('active').attr('aria-hidden', true)
                 .eq(curIndex)
                 .addClass('active').attr('aria-hidden', false);
        $images.parent('a').removeClass('active').attr('aria-hidden', true);
        $images.removeClass('active')
               .eq(curIndex)
               .addClass('active')
               .parent('a').addClass('active').attr('aria-hidden', false);
        $controls.find('a.bullet')
            .removeClass('active-bullet')
            .removeAttr('aria-current')
            .eq(curIndex).addClass('active-bullet').attr('aria-current', true);
        if ( !Modernizr.cssfilters) {
          $(last).css({zIndex: 1}).stop().animate({opacity:0}, 300);
          $(cur).css({zIndex: 2}).stop().animate({opacity:1}, 300);
        }
      });
      
      if( $(window).width() >= 768 ) rotator.play();
      
      $slideshow.on('mouseenter', function(){
        if( $(window).width() >= 768 ) rotator.pause();
      });
      $slideshow.on('mouseleave', function(){
        if( $(window).width() >= 768 ) rotator.play();
      });
      
      $(window).on('resize', function(){
        if( $(window).width() < 768 ) rotator.pause();
        else rotator.play();
      });
      
    });
  })();
  
  /**
   * Image Blocks
   */
  (function image_blocks(){
    $('.image-block.reveal-teaser').each(function(){
      var $block = $(this)
        , $teaser = $block.find('.teaser')
        , $excerpt = $teaser.find('.excerpt')
        , $h2 = $teaser.find('h2')
      
      $teaser.height('auto');
      $excerpt.height('0');
      
      $block
        .on('mouseenter', function(){
          
          if( $(window).width() < 768 ){
            return;
          }
          
          
          var h = $block.innerHeight() 
            - parseInt($teaser.css('padding-top'), 10) 
            - parseInt($teaser.css('padding-bottom'), 10);
            
          $teaser
            .animate({height: h}, 150);
          
          $excerpt.height('auto');
            
        })
        .on('mouseleave', function(){
          $teaser.stop().animate({'height':$h2.outerHeight()+parseInt($teaser.css('padding-top'),10)+parseInt($teaser.css('padding-bottom'),10)}, 150, function(){
            $excerpt.height(0);
            $teaser.height('auto');
          });
          
        });
    });
  })();
  
  /**
   * Video Blocks
   */
  (function video_blocks(){
    $('.video-block').each(function(){
      var $block = $(this)
        , $teaser = $block.find('.teaser')
        , $h2 = $teaser.find('h2')
        , $playButton = $block.find('.play-button')
      
      $playButton.css({top: ($block.height() - $teaser.height())/2});
    });
  })();
  
  /**
   * Site Alert
   */
  (function site_alert(){
    $('#site-alert').bind('closed', function(){
      // drop a cookie
      $.cookie('site_alert_closed', true, {path:'/'} );
    });
  })();
  
  /**
   * Video Archive
   */
  (function video_triggers(){
    $(document).on('click', '.video-trigger', function(e){
      
      e.preventDefault();
      
      var $trigger = $(this)
        , $container = $trigger.parents('.video-container')
        
      if ( !$container.length ) return;
      
      var w = $container.parent().width()
      
      $container.data('orig_width', $container.width() );
      $container.data('orig_height', $container.height() );
      $container.data('orig_html', $container.html() );
      $container.html( '<div class="media video"><div class="responsive-media">'+$trigger.data('embed')+'</div></div>' );
      $container.animate({width: w, height: w * $trigger.data('ratio') });
      $container.find('.responsive-media').css('padding-bottom', ($trigger.data('ratio')*100)+'%');
      $container.parents('.video-list-entry').addClass('playing');
    });
    
    $(document).on('click', '.video-list-entry .collapse-button', function(e){
      var $btn = $(this)
        , $container = $btn.parents('.video-list-entry').find('.video-container')
        
      e.preventDefault();
      $container.animate({width: $container.data('orig_width'), height: $container.data('orig_height')}, function(){
        $container.html( $container.data('orig_html') );
      });
      $container.parents('.video-list-entry').removeClass('playing');
    });
    
  })();
  
  /**
   * News & Events Videos
   */
  (function video_triggers(){
    $(document).on('click', '.videos .video-choice', function(e){
      
      e.preventDefault();
      
      var $trigger = $(this)
        , $container = $trigger.parents('.videos').find('.video-player .responsive-media')
        
      if ( !$container.length ) return;
      
      $container.css({'padding-bottom': ($trigger.data('ratio')*100)+'%'});
      $container.html( $trigger.data('embed') );
      
      $trigger.parents('.video-chooser').find('.video-choice').removeClass('active');
      $trigger.addClass('active');
      
    });
  })();
  
  /**
   * Feedback button
   */
  (function feedback(){
    var open = false;
    $('.feedback .button, .feedback .icon-remove-sign, .feedback-cover').click(function(){
      
      $('.feedback .container').animate({
        height: open ? 0 : $(window).innerHeight() - 130,
      });
      
      $('.feedback').animate({
        bottom: open ? 0 : 50,
      });
      
      $('.feedback-cover')[open?'fadeOut':'fadeIn']();
      
      $('.feedback .icon-remove-sign')[open?'hide':'show']();
      
      open = !open;
      
      $(document)[open?'on':'off']('keyup', listen_for_escape);
      $(window)[open?'on':'off']('resize', fix_height);
      
    });
    
    function fix_height() {
       $('.feedback .container').stop().animate({
        height: !open ? 0 : $(window).innerHeight() - 130,
      }, function(){
        $(this).css({'overflow':'scroll'});
      });
       
    }
    
    function listen_for_escape(e) {
      if ( e.keyCode == 27 && open ) {
        $('.feedback .button').click();
      }
    }
  })();
  
  (function sortable_tables(){
    $('th.sortable').each(function(){
      var $th = $(this)
        , i = $th.index()
        , $table = $(this).parents('table')
        
      $th.click(function(e){
        
        var $trs = $table.find('tbody tr')
          , sorted = $th.hasClass('sorted')
          , reverse = $th.hasClass('sorted-asc')
        
        $trs.sort(function(a,b){
          return $(a).find('td').eq(i).text() == $(b).find('td').eq(i).text() ? 0 :
            ($(a).find('td').eq(i).text() > $(b).find('td').eq(i).text() ? 1 : -1);
        });
        
        if( reverse ) Array.prototype.reverse.call($trs);
        
        $trs.each(function(){
          $table.find('tbody').append(this);
        });
        
        $table.find('thead th').removeClass('sorted').removeClass('sorted-asc');
        $th.addClass('sorted');
        
        if ( !reverse ) {
          $th.addClass('sorted-asc');
        }
        
      });
      
    });
  })();
  
  if( $('.faculty-search').length ) (function faculty_search(){
    
    // initialize data
    var $table = $('.faculty-search table')
      , $tbody = $table.find('tbody')
      , members = [];
      
    $('tr[data-name]').each(function(){
      members[members.length] = {
        name            :$(this).data('name'),
        research_areas  :$(this).data('research-areas'),
        department      :$(this).data('department'),
        tr              :$(this)
      };
    });
    
    $('.faculty-search input').keyup(do_search);
    
    function do_search(e) {
      e.preventDefault();
      var $this = $(this)
        , name = $('.faculty-search input[name="name"]').val().toLowerCase()
        , research_area = $('.faculty-search input[name="research-area"]').val().toLowerCase()
        
      // filter the members...
      var results = $.grep(members, function(member){
        var ret = false;
        if( name && ~member.name.toLowerCase().indexOf( name ) ) ret = true;
        if( research_area && member.research_areas && member.research_areas.length ){
          // go through research areas
          var f=false;
          for(var i=0; i<member.research_areas.length; i++) {
            if ( ~member.research_areas[i].toLowerCase().indexOf(research_area) ){
              f = true;
              break;
            }
          }
          if (!name) {
            ret = f;
          }
          else {
            ret = ret && f;
          }
        }
        return ret;
      });
      
      $tbody.empty();
      if( !results.length ) {
        $table.removeClass('has-results');
      }
      else {
        $table.addClass('has-results');
        $.each(results, function(i, result){
          var $tr = result.tr.clone();
          $('<td>'+result.department+'</td>').insertBefore( $tr.find('td').last() );
          $tr.appendTo( $tbody );
        });
      }
    }
  })();
  
  (function gsa_instant_search(){
    var $form = $('#page-header .search-form, .page-header .search-form')
      , $input = $form.find('input[name=s]')
      , $submit = $form.find('input[type=submit]')
      , timeout
      , req
      , $box
      , currentHighlight = false
      , boxVisible = false
      , lastResponse
      , currentSearch
      , lastValue
      , lastSearch
      , delayedSearch = delay( search, 150 )
      , isFocused = false
      
    $input.keyup( keyUp );
    $input.focus( focus );
    
    function keyUp(e) {
      // if this is the same as last
      if ( lastValue != $input.val() ) delayedSearch();
      lastValue = $input.val();
      if ( e.keyCode != 27 && !isFocused ) {
        focus();
      }
    }
    
    function focus() {
      
      if ( lastResponse && lastResponse.hits && $box) {
        showBox();
      }
      
      if ( !isFocused) {
        $(document).on('focusin', changeFocus);
        $(document).on('keydown', keyDown);
        $(document).on('click', documentClick );
      }
      isFocused = true;
    }
    
    function changeFocus(e) {
      var $target = $(e.target)
      if( !$target.parents('.search-form').length ){
        hideBox();
        return;
      }
      if ( $box ) {        
        // check to see if the focused object is a list item and highlight it.
        $box.find('.results li').removeClass('current');
        currentHighlight = false;
        if ( $target.parents('li').length ) {
          currentHighlight = $target.parents('li').addClass('current');
        }
      }
    }
    
    function documentClick(e) {
      if ( !$.contains( $form[0], e.target ) ){
        blur();
      }
    }
    
    function blur() {
      
      if ( $box ) hideBox();
      $(document).off('focusin', changeFocus);
      $(document).off('keydown', keyDown);
      isFocused = false;
      
    }
    
    function keyDown(e) {
      
      if ( !isFocused ) return;
      var k = e.keyCode
        , isInput = $(e.target)[0] == $input[0]
        
      if ( isInput && (k == 39 || k == 37) ) {
        return;
      }
      
      if ( isInput && k == 9 && lastSearch) {
        next();
        e.preventDefault();
        return;
      }
      
      switch ( k ) {
        // find the next result
        case 39: case 40:
          next();
          e.preventDefault();
          break;
        
        // find last result
        case 37: case 38:
          prev();
          e.preventDefault();
          break;
        
        // escape
        case 27:
          e.preventDefault();
          blur();
          break;
        
        case 13:
          if ( $(e.target).hasClass('all-results') ){
            $submit.click();
            blur();
          }
          else if ( e.target.tagName.toLowerCase() == 'a') {
            blur();
          }
      }
    }
    
    function submitKeyUp(e) {
      if ( e.keyCode == 9 && boxVisible) {
        next();
        e.preventDefault();
      }
    }
    
    function next(){
      if ( !$box) {
        return;
      }
      if ( !currentHighlight) {
        $box.find('li a').first().focus();
      }
      else {
        // find the next
        var $next = currentHighlight.next();
        if ( $next.length ) $next.find('a').focus();
        else  {
          currentHighlight.parents('ul').find('li').first().find('a').focus();
        }
      }
    }
    
    function prev() {
      if ( !$box) {
        return;
      }
      if ( !currentHighlight) {
        $box.find('li a').first().focus();
      }
      else {
        // find the next
        var $prev = currentHighlight.prev();
        if ( $prev.length ) $prev.find('a').focus();
        else  {
          $input.focus();
        }
      }
    }
    
    function search() {
      
      if ( lastSearch  == $input.val() ) {
        return;
      }
      
      if ( $input.val() == '' ) {
        if( $box ) {
          $box.find('.results').empty();
          $box.addClass('no-results');
        }
        
        lastSearch = '';
        return;
      }
      
      var data = {
        action  :'gsa_search',
        s       :$input.val()
      };
      
      if ( req && req.state() == 'pending') req.abort();
      
      showBox();
      showLoading();
        
    }
    
    function handleResponse(response, success, req) {
      
      currentHighlight = false;
      lastSearch = req.search;
      lastResponse = response;
      $box.find('.results').empty();
      
      if ( !response.hits ) {
        $box.addClass('no-results');
        return;
      }
      else {
        $box.removeClass('no-results');
      }
      
      $.each(response.results, function(i, result){
        var $li = $('<li />').appendTo( $box.find('.results') );
        $li.append('<h5><a href="'+result.path+'">'+result.title[0]+'</a></h5>');
        
        var $a = $li.find('a');
        if ( $a[0].hostname !== window.location.hostname ) {
          $a.attr('target', '_blank');
        }
        
        if ( result.mimeType && result.mimeType[0] == 'application/pdf') {
          $a.prepend('<i class="icon-file-pdf"></i> ')
        }
        
        $a.click(function(e){
          e.stopPropagation();
        });
        $li.append('<div class="description">'+result.description+'</div>');
        
        $li.click( function(){
          if( $a.attr('target') == '_blank' ){
            window.open( $a.attr('href'), '_blank' );
          }
          else {
            $a.click();
          }
        });
        
      });
      var $allResults = $(
        '<li class="all-results"><a href="#">View all results <i class="icon-chevron-right"></i></a></li>'
      ).click(function(){
        $form.submit();
      });
      $box.find('.results').append($allResults);
    }
    
    function handleError(e) {
      
      // if we aborted a request, its not really an error.
      if ( req.state == 'abort') {
        return;
      }
      
      // else, we should figure out what to do in this error situation
    }
    
    function showBox() {
      if ( !$box ) {
        $box = $('<div class="instant"><div class="heading"><div class="loading-text">Searching...</div><h5>Search Results</h5></div><ul class="results"></ul></div>').appendTo( $form )
        $box.append( $('<div class="no-results-text">No Results Found</div>'));
        // $box.append( $('<div class="error"><p>An error occured</p></div>'));
      }
      $box.stop().fadeIn(100);
      boxVisible = true;
    }
    
    function hideBox() {
      if ( $box ) $box.stop().fadeOut(100);
      boxVisible = false;
    }
    
    function showLoading(args) {
      $box.addClass('loading');
    }
    
    function hideLoading() {
      $box.removeClass('loading');
    }
  })();
  
  function delay(fn, interval) {
    var timeout;
    return function(){
      if ( timeout ) clearInterval( timeout );
      timeout = setTimeout(fn, interval);
    }
  }
  
  (function tabs_on_mobile(){
    var $tabs = $('[data-toggle="tab"]');
    
    function update() {
      if( !$.breakpoint() ){
        $tabs.attr('data-toggle', '_tab');
        $('.nav-tabs li.active').removeClass('active').addClass('_active');
      }
      else {
        $tabs.attr('data-toggle', 'tab');
        $('.nav-tabs li._active').removeClass('_active').addClass('active');
      }
      
    }
    update();
    $(window).on('breakpoint', update);
  })();
  
  (function empty_sidebar(){
    $('.sidebar').each(function(){
      if( $(this).is(':empty') || $(this).text().match(/^\s*$/) ){
        $(this).addClass('empty-sidebar');
      }
    });
  })();
});
