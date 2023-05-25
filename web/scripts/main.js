(async function(){
	let version = await eel.get_version()();
	document.getElementById("version").innerHTML = version;
	init_tabs()
	let devices = await eel.get_audio_devices()();

	let input_devices_area = document.getElementById("input-device");
	let output_devices_area = document.getElementById("output-device");
	function addDevice(area, device){
		let op = document.createElement("option")
		op.value = device.index;
		op.innerHTML = device.name;
		area.appendChild(op)
	}
	devices.input.forEach(device=>{
		addDevice(input_devices_area, device)
	})
	devices.output.forEach(device=>{
		addDevice(output_devices_area, device)
	})
	input_devices_area.onchange = _=>{
		eel.change_input_device(input_devices_area.value)();
		eel.save_settings()();
	}
	output_devices_area.onchange = _=>{
		eel.change_output_device(output_devices_area.value)();
		eel.save_settings()();
	}

	await load_settings();
	initThemes()
	await getTranslation()
	let tab_now = window.location.hash.split("#").at(-1)
	if (tab_now){
		document.querySelector(`#tabs .tab-title[name='${tab_now}']`).click()
	}
	start_search()
})()

function init_tabs(){
	let tabs = document.querySelector("#tabs")
	let content = document.getElementById("tab-content");
	tabs.querySelectorAll(".tab-title").forEach(tab=>{
		tab.onclick =_=>{
			content.querySelectorAll(".tab.active").forEach(e=>{e.classList.remove("active")})
			content.querySelector(`.tab[name='${tab.getAttribute("name")}']`).classList.add("active")
			tabs.querySelectorAll(".tab-title.active").forEach(e=>{e.classList.remove("active")})
			tab.classList.add("active")
			window.location.hash = tab.getAttribute("name")
		}
	})
}
async function load_settings(){
	let settings = await eel.get_settings()();
	Object.keys(settings).forEach(key=>{
		let val = settings[key];
		let arr = document.querySelectorAll(`.setting[name='${key}']`)
		let element;
		if (arr.length > 1){
			element = document.querySelector(`.setting[name='${key}'][value='${val}']`)
			if (!element){
				if (key == "theme"){
					theme_after_load = _=>{
						let element = document.querySelector(`.setting[name='${key}'][value='${val}']`)
						if (element){
							load_one_setting(element, val)
							element.onchange()
						}
					}
				}
				return
			}
		} else{
			element = arr[0]
		}

		load_one_setting(element, val)
	})
}
function load_one_setting(element, val){
	if (element.type == "checkbox"){
		element.checked = val
	}
	else if (element.type == "radio"){
		element.checked = true
	}
	else{
		if (val !== null){
			element.value = val.toString()
		}
	}
}

(async function initVolumer(start=1){
	let volumer = document.getElementById("volumer")
	let input = volumer.querySelector("input")
	let text = volumer.querySelector("[name=value]")
	input.value = start * 100
	text.innerHTML = input.value
	input.oninput = _=>{
		text.innerHTML = input.value;
		eel.change_volume(input.value / 100)
	}
})()

document.getElementById("stop_play").onclick = _=>{
	eel.stop_play()();
	document.querySelectorAll("#list-area > .sound-button.playing").forEach(e=>{
		e.classList.remove("playing")
		e.querySelector(".play").disabled = false
	})
}
document.querySelectorAll(".setting").forEach(e=>{
	let ignore = ["input_device", "output_device"]
	if (!ignore.includes(e.name)){
		e.addEventListener("change", _=>{
			let name = e.name;
			let value;
			if (e.type == "checkbox"){
				value = e.checked
			}
			else{
				if (isNaN(e.value) && e.value != "true" && e.value != "false"){
					value = e.value
				} else{
					value = eval(e.value)
				}
			}
			eel.change_setting(name, value)()
		})
	}
})

var search = document.getElementById("search");
var area = document.getElementById("list-area");

document.getElementById("api").addEventListener("change", e=>{
	if (e.target.value == "favorites"){
		search.value = ""
		start_search()
	}
})

function start_search_fav(sorting=false) {
	if (document.getElementById("api").value == "favorites"){
		setTimeout(function(){
			if (sorting){
				let el = document.querySelector("#bread-crumbs :last-child")
				if (el){
					change_dir(el.getAttribute("path"))
					return
				}
				return
			}
			start_search()
		}, 0)
	}
}

async function start_search(){
	let api = document.getElementById("api").value;
	let value = search.value.trim()
	if (api != "favorites" && !value){return}
	if (api == "favorites" && !value){
		let el = document.querySelector("#bread-crumbs :last-child")
		if (el){
			change_dir(el.getAttribute("path"))
			return
		}
	}

	let results = [];
	area.innerHTML = ""
	document.getElementById("bread-crumbs").innerHTML = ""
	if (api == "youtube"){
		results = await eel.search_youtube(value)();
	}
	else if (api == "favorites"){
		results = await eel.search_favorites(value)();
	}
	else if (api == "myinstants"){
		results = await eel.search_myinstants(value)();
	}
	else if (api == "zvukogram"){
		results = await eel.search_zvukogram(value)();
	}
	else if (api == "meowpad"){
		results = await eel.search_meowpad(value)();
	}
	if (results.length == 0){
		area.innerHTML = `<span translation="__nothing_found__">${LANG("nothing_found")}</span>`
	} else{
		results.forEach(e=>{
			addButton(e)
		})
	}
}
document.getElementById("search_but").onclick = start_search
document.getElementById("search").onkeydown = (e)=>{
	if (e.keyCode == 13){
		start_search()
	}
}

async function change_dir(dirname, element){
	function remove_after(el){
		let next = el.nextElementSibling;
		if (next){
			remove_after(next)
		}
		el.remove()
	}
	if (element && element.nextElementSibling){
		remove_after(element.nextElementSibling)
	}
	
	area.innerHTML = ""
	results = await eel.search_favorites("", dirname)();
	if (results.length == 0){
		area.innerHTML = `<span translation="__nothing_found__">${LANG("nothing_found")}</span>`
	} else{
		results.forEach(e=>{
			addButton(e)
		})
	}
}

function addButton(args){
	let parrent = document.createElement("div");
	parrent.className = "sound-button"
	parrent.setAttribute("data-url", args.link)
	if (args.type == "dir"){
		parrent.classList.add("folder")
		let title = document.createElement("span")
		if (args.parent_dir){
			title.innerHTML = "..."
			parrent.onclick = _=>{
				change_dir(args.parent_dir)
				let el = document.querySelector("#bread-crumbs :last-child")
				if (el){
					el.remove()
				}
			}
		} else{
			title.innerHTML = "📁" + args.title
			parrent.onclick = _=>{
				let div = document.createElement("div")
				div.className = "crumb"
				div.innerHTML = args.title
				div.setAttribute("path", args.link)
				div.onclick = _=>{
					change_dir(args.link, div)
				}
				document.getElementById("bread-crumbs").appendChild(div)
				change_dir(args.link)
			}
		}
		parrent.appendChild(title)
	}
	else {
		let but = document.createElement("button")
		but.innerHTML = "▶"
		but.className = "play"
		but.onclick = _=>{
			parrent.classList.add("playing")
			but.disabled = true
			play_it(args.link)
		}
		let title = document.createElement("span")
		title.innerHTML = args.title
		parrent.appendChild(but)
		parrent.appendChild(title)
		let other = document.createElement("div")
		other.className = "other"

		if (args.duration){
			let t = document.createElement("span")
			t.className = "time"
			t.innerHTML = args.duration
			other.appendChild(t)
		}
		let fav = document.createElement("button")
		fav.innerHTML = "⭐️"
		fav.className = "favorite"
		if (args.local){
			fav.innerHTML = "❌"
			fav.onclick = _=>{
				eel.delete_sound(args.link)
				parrent.classList.add("deleted")
				fav.disabled = true
				but.disabled = true
				setTimeout(_=>{
					parrent.remove()
				}, 500)
			}
		} else{
			fav.onclick = _=>{
				eel.save_sound(args.link, args.title)
				fav.disabled = true
				fav.innerHTML = "✔️"
			}
		}
		other.appendChild(fav)
		parrent.appendChild(other)
	}
	area.appendChild(parrent)
	return parrent
}
function play_it(url){
	eel.play_sound_url(url)()
}

function int_to_time(seconds) {
	let minutes = Math.floor(seconds / 60);
	seconds = seconds % 60;
	return `${minutes.toString().padStart(2, '0')}:${parseInt(seconds).toString().padStart(2, '0')}`;
}
eel.expose(getSoundDuration);
function getSoundDuration(identifier, duration){
	let element = document.querySelector(`#list-area > .sound-button[data-url='${identifier.replaceAll("\\", "\\\\")}']`)
	if (element){
		if (!element.querySelector(".time")){
			let t = document.createElement("span")
			t.className = "time"
			t.innerHTML = int_to_time(duration)
			element.querySelector(".other").prepend(t)
		}
		setTimeout(function() {
			element.classList.remove("playing")
			element.querySelector(".play").disabled = false
		}, duration * 1000)
	}
}

var dragTimer;
['dragenter', 'dragover'].forEach(eventName => {
	document.querySelector("#list-wrapper").addEventListener(eventName, e=>{
		let dt = e.dataTransfer;
		let files = dt.files
		if (dt.types && (dt.types.indexOf ? dt.types.indexOf('Files') != -1 : dt.types.contains('Files'))) {
			document.querySelector("#drag-area").classList.add("show")
			clearTimeout(dragTimer);
		}
		e.preventDefault()
		e.stopPropagation()
	})
})
document.querySelector("#list-wrapper").addEventListener("dragleave", e=>{
	dragTimer = setTimeout(function() {
		document.querySelector("#drag-area").classList.remove("show")
	}, 25);
	e.preventDefault()
	e.stopPropagation()
})
document.querySelector("#list-wrapper").addEventListener("drop", e=>{
	let dt = e.dataTransfer
	let files = dt.files
	document.querySelector("#drag-area").classList.remove("show")
	for (let i=0; i < files.length; i++){
		processFile(files[i])
	}
	e.preventDefault()
	e.stopPropagation()
})
function processFile(file){
	if (file && file['type'].split('/')[0] === 'audio'){
		var reader = new FileReader();
		reader.onload = async _=>{
			let path = [...document.querySelectorAll("#bread-crumbs > *")]
			path = [...path.map(x=>{
				return x.innerText
			}), file.name]
			let filename = path.join("/")
			let el = addButton({
				'title': file.name.split('.').slice(0, -1).join('.'),
				"local": true
			})
			el.classList.add("loading")
			area.prepend(el)

			let args = await eel.drop_file(reader.result, filename)()
			el.remove()
			let new_el = addButton(args)
			area.prepend(new_el)
		};
		reader.readAsDataURL(file);
	}
}
