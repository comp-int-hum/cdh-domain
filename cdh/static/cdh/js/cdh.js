
function findAll(item, query){
    var retval = Array.from(htmx.findAll(item, query));
    for(let el of htmx.findAll(item.parentElement, query)){
	if(el.id == item.id){
	    retval.push(item);
	}
    }
    return retval;
}

function getList(name){
    var retval = sessionStorage.getItem(name);
    if(retval == null){
	retval = []
    }
    else{
	retval = JSON.parse(retval);
    }
    console.info("Returning value of", name, ":", retval);
    return retval;
}

function setList(name, value){
    console.info("Setting value of", name, "to", value);
    sessionStorage.setItem(name, JSON.stringify(value));
}

function checkValue(name, value){
    var retval = getList(name).includes(value);
    console.info("Checking if value", value, "is in", name, ":", retval);    
    return retval
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
    console.info("Adding value", value, "to", name);
    setList(name, cur);
}

function removeNestedValues(element){
    console.info("Unsetting all accordions and tabs underneath", element);
    for(let el of element.getElementsByClassName("cdh-accordion-item")){
	collapseAccordionItem(el);
    }
    for(let el of element.getElementsByClassName("cdh-tab-button")){
	unsetTab(el);
    }
}

function removeAccordionItem(item){
    console.info("Completely removing accordion item", item);
    removeValue("active_accordion_items", item.id);
    item.remove();
}

function collapseAccordionItem(item){
    console.info("Collapsing accordion item", item);
    var button = item.querySelector(".cdh-accordion-header > button");
    // This is a problem:
    if(button != null){
	var content = document.getElementById(button.getAttribute("aria-controls"));
	button.setAttribute("aria-expanded", "false");
	button.classList.add("collapsed");
	content.classList.add("collapse");
	content.classList.remove("show");
	removeValue("active_accordion_items", item.id);
	removeNestedValues(item);
    }
}

function setFirstTab(tabs){
    setTab(htmx.find(tabs, "li > button"));
}

function expandAccordionItem(item){
    console.info("Expanding accordion item", item);
    var button = item.querySelector(".cdh-accordion-header > button");
    // This is also a problem:
    if(button != null){
	var content = document.getElementById(button.getAttribute("aria-controls"));
	button.setAttribute("aria-expanded", "true");
	button.classList.remove("collapsed");
	content.classList.remove("collapse");
	content.classList.add("show");
	addValue("active_accordion_items", item.id);
	for(let tabs of item.getElementsByClassName(".cdh-nav-tabs")){
	    setFirstTab(tabs);
	}
	item.scrollIntoView(true);
    }
}

function setTab(tab){
    console.info("Setting active tab", tab);
    var content = document.getElementById(tab.getAttribute("aria-controls"));
    tab.setAttribute("aria-selected", "true");
    tab.classList.add("active");
    content.classList.add("show");
    content.classList.add("active");   
    addValue("active_tab_items", tab.id);
    //tab.scrollIntoView(true);
}

function unsetTab(tab){
    console.info("Unsetting active tab", tab);    
    var content = document.getElementById(tab.getAttribute("aria-controls"));
    tab.setAttribute("aria-selected", "false");
    tab.classList.remove("active");
    content.classList.remove("show");
    content.classList.remove("active");   
    removeValue("active_tab_items", tab.id);
    removeNestedValues(content);
}

function refreshAccordionItem(item){    
    console.error("Unimplemented: refreshAccordionItem");
}

// another reminder of how bad this is!
function saveState(){
    console.info("Saving scroll state of page");
    var pathName = document.location.pathname;
    var scrollPosition = $(document).scrollTop();
    sessionStorage.setItem("scrollPosition_" + pathName, scrollPosition.toString());
}

function restoreState(root){
    console.info("Restoring page state");
    for(let acc of findAll(root, ".cdh-accordion")){
	var activeCount = 0;
	for(let item of acc.children){
	    if(checkValue("active_accordion_items", item.id) == true && activeCount == 0){
		expandAccordionItem(item);		
		activeCount += 1;
	    }
	    else{
		collapseAccordionItem(item);
	    }
	}	
    }    
    for(let ct of root.getElementsByClassName("cdh-accordion-collapse")){
	ct.addEventListener("hide.bs.collapse", event => {
	    removeValue("active_accordion_items", event.target.parentElement.id);
	    removeNestedValues(event.target.parentElement);
	});
	ct.addEventListener("show.bs.collapse", event => {
	    for(let el of event.target.parentElement.parentElement.children){
		if(el.id != event.target.parentElement.id){
		    collapseAccordionItem(el);
		}
	    }
	    expandAccordionItem(event.target.parentElement);	    
	    for(let el of event.target.parentElement.getElementsByClassName("cdh-nav-tabs")){
		setFirstTab(el);
	    }
	});	
    }
    for(let tabs of htmx.findAll(root, ".cdh-nav-tabs")){
	var activeCount = 0;
	for(let tab of htmx.findAll(tabs, "li > button")){
	    if(checkValue("active_tab_items", tab.id) == true && activeCount == 0){
		setTab(tab);
		activeCount += 1;
	    }
	    else{
		unsetTab(tab);
	    }
	}
	if(activeCount == 0){
	    setFirstTab(tabs);
	}
    }
    for(let el of root.getElementsByClassName("cdh-tab-button")){
        el.addEventListener("show.bs.tab", event => { addValue("active_tab_items", event.target.id); });
	el.addEventListener("hide.bs.tab", event => { removeValue("active_tab_items", event.target.id) });
    }

}


function cdhSetup(root, htmxSwap){
    console.info("Performing initial setup on", root);


    $(document).ready(function(){
	var options = {
            html: true,
            trigger: 'onclick',
            placement: 'bottom',
	    content: "test"
	};    
	$('[data-toggle="popover"]').popover(options);
    });
    $(document).ready(function(){
	$('[role="dialog"]').modal();
    });
    for(let el of root.getElementsByClassName("cdh-tooltip")){
	new bootstrap.Tooltip(el);
    }
    


    // things that should only happen once, at the top level of the page
    //if(!htmxSwap){
    // preserve accordion, tab, and scroll states when browsing away from or reloading the page
    // this is bad! see just above!
    
    //}

    // restore any previous state (must happen for htmx-loaded fragments too)
    restoreState(root);
    
    for(let el of htmx.findAll(root, ".cdh-select")){
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

    // run initialization for Monaco editor widgets
    for(let el of htmx.findAll(root, ".cdh-editor")){
	if(el.getAttribute("processed") != "true"){
	require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.0-dev.20220625/min/vs' } });	
	require(['vs/editor/editor.main'], function () {
	    var listValue = JSON.parse(document.getElementById(el.getAttribute("value_id")).textContent);
	    var form = el.parentNode;
	    var language = el.getAttribute("language");
	    var editor = monaco.editor.create(el, {	      
		value: listValue.join('\n'),
		language: language,
		automaticLayout: true,
		tabCompletion: "on",
		wordWrap: true
	    });
	    el.addEventListener("keyup", (event) => {
		if(language == "torchserve_text"){
		    if(event.key == "Tab" && event.shiftKey == true){
			var content = editor.getModel().getValue();
			var form = event.target.parentElement.parentElement.parentElement.parentElement;
			$.ajax(
			    {
				headers: JSON.parse(form.getAttribute("hx-headers")),
				url: form.action,
				method: "POST",
				data: {interaction: content},
				success: function (data){
				    var model = editor.getModel();
				    var current = model.getValue();				
				    model.setValue(content + data);
				    var pos = model.getPositionAt(model.getValue().length);
				    editor.setPosition(pos);
				}
			    }
			);
		    }
		}
		else if(language == "markdown" || language == "sparql"){
		    if(event.key == "Tab" && event.shiftKey == true){
			var content = editor.getModel().getValue();
			var div = event.target.parentElement.parentElement.parentElement;
			var form = div.parentElement;
			var pk = form.parentElement.getAttribute("pk");
			var model_name = form.parentElement.getAttribute("model_name");
			var app_label = form.parentElement.getAttribute("app_label");
			var endpoint = div.getAttribute("endpoint_url");
			var target = document.getElementById(div.getAttribute("output_id"));
			$.ajax(
			    {
				headers: JSON.parse(form.getAttribute("hx-headers")),
				url: endpoint,
				method: "POST",
				data: {interaction: content, pk: pk},
				success: function (data){
				    target.innerHTML = data;
				}
			    }
			);
		    }
		}
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
    
    // initialize annotated documents
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
    var event_type = event.detail.event_type;
    var app_label = event.detail.app_label;
    var model_name = event.detail.model_name;
    var pk = event.detail.pk;
    console.info("Handling event of type", event_type, ", app", app_label, ", model",  model_name, ", instance", pk);
    if(event_type == "delete"){
	for(let el of document.getElementsByClassName("cdh-accordion-item")){
	    if(
		app_label == el.getAttribute("app_label") &&
		    model_name == el.getAttribute("model_name") &&
		    pk == el.getAttribute("pk")
	    ){
		/*
		for(let ch of el.children){
		    if(ch.classList.contains("accordion-collapse")){
			// remove id from active
			removeValue("active_accordion_items", el.id);
			console.info("(not yet) removing active id", ch.id);
		    }
		    }
		    */
		//console.info("Deleting", el);
		removeAccordionItem(el);
		//el.remove();
	    }
	}
    }
    else if(event_type == "update"){
	for(let el of document.getElementsByClassName("cdh-accordion-item")){
	    if(
		app_label == el.getAttribute("app") &&
		    model_name == el.getAttribute("model_name") &&
		    pk == el.getAttribute("pk")
	    ){
		//console.error("(not yet) refreshing", el);
		// refresh
	    }
	}	
    }
    else if(event_type == "create"){
	var accItem = event.target.parentElement.parentElement.parentElement.parentElement;
var acc = accItem.parentElement;
	  $.ajax(
	    {		
		url: acc.getAttribute("accordion_url"),
		success: function (data){
		    var dummy = document.createElement( 'html' );
		    dummy.innerHTML = data;
		    for(let el of dummy.getElementsByClassName("cdh-accordion-item")){			
			if(el.getAttribute("app_label") == app_label && el.getAttribute("model_name") == model_name && el.getAttribute("pk") == pk)
			{
			    acc.insertBefore(el, accItem);
			    htmx.process(el);
			    cdhSetup(el, true);
			    dummy.remove();
			    var rel = document.getElementById(el.id);
			    for(let ch of accItem.children){
				htmx.trigger(ch, "refreshForm");
			    }
			    collapseAccordionItem(accItem);
			    for(let ch of el.querySelectorAll("*[hx-trigger='intersect']")){
				htmx.trigger(ch, "intersect");
			    }
			    expandAccordionItem(el);
			}			
		    }		    
		},
		dataType: "html"
	    }
	  );


	/*
	  Adding new item to other accordions requires some thought w.r.t. identifiers
	accItem.insertAdjacentElement("beforestart", newItem);
	
	for(let otherAcc of htmx.findAll(".cdh-accordion")){
	    if(otherAcc.getAttribute("id") != acc.getAttribute("id")){
		if(otherAcc.getAttribute("app_label") == app_label && otherAcc.getAttribute("model_name") == model_name){
		    var added = false;
		    for(let item of otherAcc.children){
			if(item.getAttribute("create") == "true"){
			    // insert before element and break
			    item.insertAdjacentElement("beforebegin", accItem);
			    added = true;
			    if(isExpanded(item)){
				collapseAccordionItem(item);			
				expandAccordionItem(accItem);
			    }
			    break;
			}		    
		    }
		    if(added == false){
			// insert at end of accordion
			acc.insertAdjacentElement("beforeend", newItem);
		    }

		    }
	    }
	}
	*/		    
	
    }
    else{
	console.warn("Unknown CDH event type:", event_type);
    }
}
