var elms=document.getElementsByClassName("labeled-token");
for(var i=0;i<elms.length;i++){
    elms[i].onmousedown = function(event){
	var targetClass = Array.from(event.target.classList.values()).find(el => el.startsWith("topic"));
        for(var k=0;k<elms.length;k++){
	    if(elms[k].classList.contains(targetClass)){
		elms[k].classList.toggle("selected");
	    }
	    else{
		elms[k].classList.remove("selected");
	    }
        }
    }
    elms[i].onmouseenter = function(event){
	var targetClass = Array.from(event.target.classList.values()).find(el => el.startsWith("topic"));
        for(var k=0;k<elms.length;k++){
	    if(elms[k].classList.contains(targetClass)){
		elms[k].classList.toggle("highlighted");
	    }
	    else{
		elms[k].classList.remove("highlighted");
	    }
        }
    }
    elms[i].onmouseexit = function(event){
	var targetClass = Array.from(event.target.classList.values()).find(el => el.startsWith("topic"));
        for(var k=0;k<elms.length;k++){
	    if(elms[k].classList.contains(targetClass)){
		elms[k].classList.toggle("highlighted");
	    }
	    else{
		elms[k].classList.remove("highlighted");
	    }
        }
    }
}

