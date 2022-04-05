(function breakpoints_plugin($){
  
  /* Default to Bootstrap breakpoints */
  var breakpoints = [768,992,1200]
    , last
    , listening = false
  
  $.breakpoints = function(b){
    if ( b === false && listening ) {
      $(window).off('resize',onResize);
      $(window).off('focus',onResize);
      return;
    }
    if ( b ){
      breakpoints = b;
    }
    breakpoints.sort(function(a,b){ return a-b; });
    init();
  };
  
  $.breakpoint = function( test ){
    if ( test !== undefined ) {
      return test == last;
    }
    return last;
  }
  
  function init(){
    last = getBreakpoint();
    if( !listening ){
      $(window).on('resize',onResize);
      $(window).on('focus',onResize);
      listening = true;
    }
    
  }
  
  function onResize(){
    var bp;
    if( (bp = getBreakpoint()) === last ) return;
    var args = [bp,last];
    last = bp;
    $(window).trigger('breakpoint',args);
    
  }
  
  function getBreakpoint(){
    var w = window.innerWidth;
    for(var i=0; i<breakpoints.length; i++){
      if( w < breakpoints[i] ){
        return i==0 ? 0 : breakpoints[i-1];
      }
    }
    return breakpoints[breakpoints.length-1];
  }
  
})(jQuery);