
function getList(name){
    var retval = sessionStorage.getItem(name);
    if(retval == null){
	retval = []
    }
    else{
	retval = JSON.parse(retval);
    }
    console.info("Returning value of", name, "as", retval);
    return retval;
}

function setList(name, value){
    sessionStorage.setItem(name, JSON.stringify(value));
}

function checkValue(name, value){
    console.info("Checking for value", value, "in", name);
    var cur = getList(name);
    return cur.includes(value);
}

function removeValue(name, value){
    console.info("Removing value", value, "from", name);
    var cur = getList(name);
    setList(name, cur.filter(c => c != value));
}

function addValue(name, value){
    var cur = getList(name);
    if(!(cur.includes(value))){
	cur.push(value);
    }
    console.info("Adding value", value, "to", name, "resulting in", cur);
    setList(name, cur);
}

function collapseChild(btn){
    ct = document.getElementById(btn.getAttribute("aria-controls"));
    btn.setAttribute("aria-expanded", "false");
    btn.classList.add("collapsed");
    ct.classList.add("collapse");
    ct.classList.remove("show");    
}


function cdhSetup(root, htmxSwap){
    console.info("Running CDH setup on ", root);

    // reactivate accordion items
    /*
    var seenAccordionItems = new Map();
    for(let el of root.getElementsByClassName("cdh-accordion-button")){
	ct = document.getElementById(el.getAttribute("aria-controls"));
	seenAccordionItems.set(ct.id, true);
	if(checkValue("active_accordion_items", ct.id)){
	    console.info("showing accordion", el.id);
	    el.setAttribute("aria-expanded", "true");
	    el.classList.remove("collapsed");
	    ct.classList.remove("collapse");
	    ct.classList.add("show");
	}
	else{
	    console.info("hiding accordion", el.id);
	    el.setAttribute("aria-expanded", "false");
	    el.classList.add("collapsed");
	    ct.classList.add("collapse");
	    ct.classList.remove("show");
	}
	ct.addEventListener("hide.bs.collapse", event => {
	    removeValue("active_accordion_items", event.target.id);
	    var el = document.getElementById(event.target.id);
	    for(let btn of el.getElementsByClassName("cdh-accordion-button")){
		collapseChild(btn);
	    }
	});
	ct.addEventListener("show.bs.collapse", event => { addValue("active_accordion_items", event.target.id) });
    }
    */
    // remove unseen accorion items
    /*
    for(let aid of getList("active_accordion_items")){
	if(!seenAccordionItems.has(aid)){
	    console.info("removing unseen accordion item", aid);
	    removeValue("active_accordion_items", aid);
	}
    }
    */
    
    // reactivate tab items
    /*
    for(let el of root.getElementsByClassName("cdh-tab-button")){
	ct = document.getElementById(el.getAttribute("aria-controls"));
	if(checkValue("active_tab_items", el.id)){
	    console.info("showing tab", el.id);
	    el.setAttribute("aria-selected", "true");
	    el.classList.add("active");
	    ct.classList.add("show");
	    ct.classList.add("active");
	}
	else{
	    console.info("hiding tab", el.id);	    
	    el.setAttribute("aria-selected", "false");
	    el.classList.remove("active");
	    ct.classList.remove("show");
	    ct.classList.remove("active");
	}
	el.addEventListener("show.bs.tab", event => { addValue("active_tab_items", event.target.id); });
	el.addEventListener("hide.bs.tab", event => { removeValue("active_tab_items", event.target.id) });
    }
    */
    // make sure exactly one tab is visible for every set of tabs
    for(let el of root.getElementsByClassName("cdh-nav-tabs")){
	console.info("Processing tabs ", el);
	var buttons = [];
	var anySet = false;
	for(let ch of el.children){
	    var isSet = ch.firstElementChild.classList.contains("active");
	    if(isSet == true && anySet == true){
		console.error("More than one tab is active on ", el);
	    }
	    else if(anySet == false){
		anySet = isSet;
	    }
	    buttons.push(ch.firstElementChild);
	}
	if(!anySet){
	    var first = buttons[0];
	    ct = document.getElementById(first.getAttribute("aria-controls"));
	    console.info("No tab was visible, so showing tab", first.id);
	    first.setAttribute("aria-selected", "true");
	    first.classList.add("active");
	    ct.classList.add("show");
	    ct.classList.add("active");	    
	}
	else{
	    console.info("Exactly one tab was already visible on ", el);
	}
    }

    for(let el of root.getElementsByClassName("cdh-select")){
	el.addEventListener("change", event => {
	    var tgt = document.getElementById(event.target.value);
	    htmx.trigger(tgt, "select");
	});
    }

    if(root.parentNode != null && root.classList.contains("cdh-select")){
	root.addEventListener("change", event => {
	    var tgt = document.getElementById(event.target.value);
	    htmx.trigger(tgt, "select");
	});
    }
    // remember and restore where you were on the page (this probably doesn't work in some situations!)
    /*
    var pathName = document.location.pathname;
    window.onbeforeunload = function () {
        var scrollPosition = $(document).scrollTop();
        sessionStorage.setItem("scrollPosition_" + pathName, scrollPosition.toString());
    }
    if (sessionStorage["scrollPosition_" + pathName]) {
        $(document).scrollTop(sessionStorage.getItem("scrollPosition_" + pathName));
	}
	*/

    // rerun initialization for Monaco editor widgets
    for(let el of root.getElementsByClassName("cdh-editor")){
	if(el.getAttribute("processed") != "true"){
	require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.0-dev.20220625/min/vs' } });	
	require(['vs/editor/editor.main'], function () {
	    var listValue = JSON.parse(document.getElementById(el.getAttribute("value_id")).textContent);
	    var form = el.parentNode;
	    var editor = monaco.editor.create(el, {	      
		value: listValue.join('\n'),
		language: el.getAttribute("language"),
		automaticLayout: true
	    });	    
	    editor.getModel().onDidChangeContent((event) => {
		var content = editor.getModel().getValue();
		var hid = document.getElementById(el.getAttribute("field_name") + "-hidden");
		hid.setAttribute("value", content);
	    });
	});
	    el.setAttribute("processed", "true");
	}
    }

    // annotated documents
    var elms=root.getElementsByClassName("labeled-token");
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
}


function handleCdhEvent(event){
    for(let el of document.getElementsByClassName("accordion-item")){
	if(event.detail.app == el.getAttribute("app") && event.detail.model == el.getAttribute("model") && event.detail.id == el.getAttribute("obj_id")){
	    if(event.detail.type == "delete"){
		// remove element
		el.remove();
		for(let ch of el.children){
		    if(ch.classList.contains("accordion-collapse")){
			// remove id from active
		    }
		}
	    }
	    else if(event.detail.type == "update"){
		
	    }
	    else if(event.detail.type == "create"){
	    }
	}
    }
}
