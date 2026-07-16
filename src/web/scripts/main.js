(async function(){
	let version = await eel.get_version()();
	document.getElementById("version").innerHTML = version;
	// init_tabs()
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
	initApi()
	initSettingsButton()

	donationPopup()
})()

async function load_settings(){
	let settings = await eel.get_settings()();
	Object.keys(settings).forEach(key=>{
		let val = settings[key];
		if (key == "voice_mod"){
			voicemod_details(val)
		}
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
function switchSettings(showSettings) {
	const hideElements = [
		"#bread-crumbs",
		"#list-wrapper",
		".header-area",
	];
	const showElements = [
		"#settings",
		"#settings-header",
	];
	hideElements.forEach(selector => {
		document.querySelector(selector)?.classList.toggle("hide", showSettings);
	});
	showElements.forEach(selector => {
		document.querySelector(selector)?.classList.toggle("hide", !showSettings);
	});
}

function initSettingsButton() {
	document.querySelector("#open_settings").onclick = () => switchSettings(true);

	// document.querySelector("#close_settings")?.addEventListener("click", () => {
	// 	switchSettings(false);
	// });
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
	let input = document.getElementById("volumer")
	input.value = start * 100
	input.oninput = _=>{
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
			if (name == "voice_mod"){
				voicemod_details(value)
			}
			eel.change_setting(name, value)()
		})
	}
})
function voicemod_details(value){
	let details = document.querySelector("input[name='voice_mod']").closest("details")
	if (value){
		details.open = true
		details.querySelector("summary").style.pointerEvents = "none"
	} else{
		details.querySelector("summary").style.pointerEvents = ""
	}
}

var search = document.getElementById("search");
var area = document.getElementById("list-area");
var API = "favorites";


function initApi(){
	const header = document.querySelector("#header")
	document.querySelectorAll("#api-list button").forEach(button=>{
		button.addEventListener("click", e=>{
			switchSettings(false)
			API = e.target.value
			header.textContent = button.textContent
			if (button.getAttribute("translation")){
				header.setAttribute("translation", button.getAttribute("translation"))
			} else {
				header.removeAttribute("translation")
			}
			if (e.target.value == "favorites"){
				header.classList.add("hover")
				header.onclick = _=>open_favorites_dir()
			} else {
				header.classList.remove("hover")
				header.onclick = null
			}
			start_search()
		})
	})
	document.querySelector('button[value="favorites"]').dispatchEvent(new Event("click"))
}

// function start_search_fav(sorting=false) {
// 	if (document.getElementById("api").value == "favorites"){
// 		setTimeout(function(){
// 			if (sorting){
// 				let el = document.querySelector("#bread-crumbs :last-child")
// 				if (el){
// 					change_dir(el.getAttribute("path"))
// 					return
// 				}
// 				return
// 			}
// 			document.getElementById("bread-crumbs").innerHTML = ""
// 			start_search()
// 		}, 0)
// 	}
// }

async function start_search(){
	let value = search.value.trim()
	if (API != "favorites" && !value){
		area.innerHTML = ""
		return
	}
	// if (API == "favorites" && !value){
	// 	let el = document.querySelector("#bread-crumbs :last-child")
	// 	if (el){
	// 		change_dir(el.getAttribute("path"))
	// 		return
	// 	}
	// }

	let results = [];
	area.innerHTML = ""
	document.getElementById("bread-crumbs").innerHTML = ""
	if (API == "youtube"){
		results = await eel.search_youtube(value)();
	}
	else if (API == "favorites"){
		results = await eel.search_favorites(value)();
	}
	else if (API == "myinstants"){
		results = await eel.search_myinstants(value)();
	}
	else if (API == "zvukogram"){
		results = await eel.search_zvukogram(value)();
	}
	else if (API == "uwupad"){
		results = await eel.search_uwupad(value)();
	}
	if (results.length == 0){
		area.innerHTML = `<span translation="__nothing_found__">${LANG("nothing_found")}</span>`
	} else{
		results.forEach(e=>{
			addButton(e)
		})
	}
}
var searchTimer = null;
document.getElementById("search").onkeydown = (e)=>{
	if (e.keyCode == 13){
		if (searchTimer){clearTimeout(searchTimer)}
		start_search()
	}
}
document.getElementById("search").oninput = (e)=>{
	if (searchTimer){clearTimeout(searchTimer)}
	searchTimer = setTimeout(_=>{
		start_search()
	}, 500)
}

async function change_dir(dirname){
	area.innerHTML = ""
	updateCrumbs([])
	results = await eel.search_favorites("", dirname)();
	if (results.length == 0){
		area.innerHTML = `<span translation="__nothing_found__">${LANG("nothing_found")}</span>`
	} else{
		results.forEach(e=>{
			addButton(e)
		})
	}
}

function updateCrumbs(crumbs){
	const parrent = document.getElementById("bread-crumbs")
	parrent.innerHTML = ""
	function createEl(title, path){
		let div = document.createElement("div")
		div.className = "crumb"
		div.textContent = title
		div.onclick = _=>{
			change_dir(path)
		}
		return div
	}
	if (crumbs.length > 0){
		const header = document.querySelector("#header")
		let div = createEl(header.textContent, "")
		if (header.getAttribute("translation")){
			div.setAttribute("translation", header.getAttribute("translation"))
		}
		parrent.appendChild(div)

		crumbs.forEach(crumb=>{
			let icon = document.createElement("i")
			icon.className = "fa-solid fa-angle-right"
			parrent.appendChild(icon)

			parrent.appendChild(createEl(crumb.title, crumb.link))
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
			updateCrumbs(args.crumbs)
			parrent.classList.add("back")
			title.innerHTML = `<i class="fa-solid fa-ellipsis"></i>`
			parrent.onclick = _=>{
				change_dir(args.parent_dir)
			}
		} else{
			let icon = document.createElement("i")
			icon.className = "fa-solid fa-folder"
			parrent.appendChild(icon)

			title.innerHTML = args.title
			parrent.onclick = _=>{
				change_dir(args.link)
			}
		}
		parrent.appendChild(title)
	}
	else {
		let span = document.createElement("span")
		let but = document.createElement("button")
		but.innerHTML = `<i class="fa-solid fa-play"></i>`
		but.className = "play"
		but.onclick = _=>{
			parrent.classList.add("playing")
			but.innerHTML = `<i class="fa-solid fa-stop"></i>`
			but.disabled = true
			play_it(args.link)
		}
		let title = document.createElement("span")
		title.innerHTML = args.title
		span.appendChild(but)
		parrent.appendChild(span)
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
		if (args.local){
			fav.className = "action delete"
			fav.innerHTML = `<i class="fa-solid fa-trash"></i>`
			fav.onclick = _=>{
				eel.delete_sound(args.link)
				parrent.classList.add("deleted")
				fav.disabled = true
				but.disabled = true
				setTimeout(_=>{
					parrent.remove()
				}, 1000)
			}
		} else{
			fav.className = "action save"
			fav.innerHTML = `<i class="fa-solid fa-star"></i>`
			fav.onclick = _=>{
				eel.save_sound(args.link, args.title)
				fav.disabled = true
				fav.innerHTML = `<i class="fa-solid fa-check"></i>`
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
			element.querySelector(".play").innerHTML = `<i class="fa-solid fa-play"></i>`
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
function open_favorites_dir(){
	let path = [...document.querySelectorAll("#bread-crumbs > *")]
	path = path.map(x=>{
		return x.innerText
	})
	eel.open_favorites_dir(path)
}

document.addEventListener("mouseup", (e) => {
	if (e.button == 3) // Back
	{
		let el = area.querySelector('.sound-button.folder.back')
		if (el){
			el.click()
		}
	}
});


function donationPopup(){
	function checkLastNotificationTime(){
		let currentTime = Math.floor(Date.now() / 1000);
		let lastNotificationTime = localStorage.getItem('lastNotificationTime');
		if (!lastNotificationTime || (currentTime - lastNotificationTime > 12*60*60)) {
			return true;
		} else {
			return false;
		}
	}
	function callback(){
		document.querySelector("#donate-popup").classList.remove("show")
		var currentTime = Math.floor(Date.now() / 1000);
		localStorage.setItem('lastNotificationTime', currentTime);
	}
	document.querySelector("#donate-popup .close").onclick = callback
	document.querySelector("#donate-popup button").onclick = callback
	
	if (checkLastNotificationTime()){
		setTimeout(_=>{
			document.querySelector("#donate-popup").classList.add("show")
		}, 60*1000)
	}
}
