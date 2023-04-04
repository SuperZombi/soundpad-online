var theme_after_load = _=>{}

async function initThemes(){
	changeTheme()
	document.querySelectorAll(".setting[name='theme']").forEach(e=>{
		e.onchange = _=>{changeTheme()}
	})
	await loadLocalThemes()
	theme_after_load()
	await loadWebThemes()
	theme_after_load()
}
function changeTheme(){
	let el = document.querySelector(".setting[name='theme']:checked")
	let old = document.getElementById("theme")
	if (old){
		old.remove()
	}
	let link = document.createElement("link")
	link.id = "theme"
	link.rel = "stylesheet"
	link.href = el.getAttribute("url")
	document.head.appendChild(link)
}
async function loadLocalThemes(){
	let arr = await eel.get_local_themes()();
	arr.forEach(e=>{
		e['type'] = "local"
		loadTheme(e)
	})
}
async function loadWebThemes(){
	let arr = await eel.get_web_themes()();
	arr.forEach(e=>{
		e['type'] = "web"
		loadTheme(e)
	})
}
async function loadTheme(config){
	if (document.querySelector(`.setting[name='theme'][value='${config.name}']`)){
		return
	}

	let file;
	if (config.css){
		let blob = new Blob([config.css], {type: "text/css"})
		file = URL.createObjectURL(blob);
	} else{
		file = config.url
	}

	let element = document.createElement("label")
	element.classList.add("theme", config.type)
	element.innerHTML = `
		<input class="setting" name="theme" type="radio" value="${config.name}" url="${file}">
		<img draggable="false" src="${config.image}">
		<span>${config.name}</span>
	`
	document.querySelector(".themes").appendChild(element)
	element.querySelector("input").onchange = _=>{
		changeTheme()
		eel.change_setting("theme", config.name)()
	}
}
