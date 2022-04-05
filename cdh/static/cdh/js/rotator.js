/*
      ___         ___                   
     /\__\       /\  \         _____    
    /:/ _/_     /::\  \       /::\  \   
   /:/ /\__\   /:/\:\  \     /:/\:\  \  
  /:/ /:/  /  /:/ /::\  \   /:/ /::\__\ 
 /:/_/:/  /  /:/_/:/\:\__\ /:/_/:/\:|__|
 \:\/:/  /   \:\/:/  \/__/ \:\/:/ /:/  /
  \::/__/     \::/__/       \::/_/:/  / 
   \:\  \      \:\  \        \:\/:/  /  
    \:\__\      \:\__\        \::/  /   
     \/__/       \/__/         \/__/
     
  Generic array rotator because I am sick and tired
  of writing this logic over and over again.
  
  @author     Mark Fabrizio
  @date       March 19, 2013
  @requires   jquery.js
*/

(function($){
  
  var instance = 0;
  
  Fabrizio_Rotator = function(items, options){
    
    instance++;
    
    this.index = 0;
    this.items = items;
    
    this.options = $.extend({
      id: 'fabrizio_rotator_'+instance
    }, this.defaults, options||{});
    
    this.playing = false;
    if( this.options.autoPlay ) this.play();
    
    /********************************************************
    *  This timeout allows for other objects to subscribe
    *  to the event right after instantiation
    *********************************************************/
    var self = this;
    setTimeout(function(){
      self.trigger('init', self.items[self.index], self.index);
    },10);
  };
  
  $.extend( Fabrizio_Rotator.prototype, {
    
    defaults : {
      pause : 8000,
      autoPlay : false
    },
    
    on : function( event, callback, scope ){
      var target = this.options.target || document;
      $(target).on(event+'.'+this.options.id, function(ev){
        var args = arguments.length > 1 ? Array.prototype.slice.call( arguments, 1 ) : []
        return callback.apply( scope || target, args );
      });
      return this;
    },
    
    trigger : function( event ){
      var target = this.options.target || document;
      $(target).trigger(event+'.'+this.options.id, Array.prototype.slice.call(arguments, 1) );
      return this;
    },
    
    off : function(event, handler){
      var target = this.options.target || document;
      event = event || '';
      if ( handler ) {
        $(target).off(event+'.'+this.options.id, '*', handler);
      }
      else {
        $(target).off(event+'.'+this.options.id);
      }
      return this;
    },
    
    next : function(){
      return this.go( this.index+1 );
    },
    
    prev : function(){
      return this.go( this.index-1 );
    },
    
    go : function(i){
      
      var last = this.index;
      if( i == last ) return this;
      if( i > this.items.length-1 ) i=0;
      if( i < 0 ) i=this.items.length-1;
      
      this.index = i;
      clearTimeout( this.timeout );
      this.trigger('change', this.items[this.index], this.items[last], this.index, last, this);
      if( this.playing ) this.delayedNext();
      return this;
    },
    
    play : function(){
      if( this.playing ) return this;
      this.trigger('toggleplay', this.playing, this);
      this.trigger('play', this, this.remainingTime );
      this.playing = true;
      this.delayedNext( this.remainingTime || false );
      return this;
    },
    
    pause : function(){
      if( !this.playing ) return this;
      this.trigger('toggleplay', this.playing, this);
      this.trigger('pause', this);
      this.playing = false;
      if(this.lastStart){
        this.remainingTime = this.options.pause - (new Date().getTime() - this.lastStart);
      }
      clearTimeout(this.timeout);
      return this;
    },
    
    togglePlay : function(){
      return this.playing ? this.pause() : this.play();
    },
    
    delayedNext : function( pause ){
      clearTimeout( this.timeout );
      var self = this;
      this.lastStart = new Date().getTime();
      this.remainingTime = false;
      this.timeout = setTimeout( function(){
        self.next();
      }, pause && pause > 0 ? pause : this.options.pause );
      return this;
    }
    
  });
})(jQuery);