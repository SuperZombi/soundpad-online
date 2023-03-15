(async function(){
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
	}
	output_devices_area.onchange = _=>{
		eel.change_output_device(output_devices_area.value)();
	}
	eel.change_input_device(input_devices_area.value)();
	eel.change_output_device(output_devices_area.value)();
})()

document.getElementById("stop_play").onclick = _=>{
	eel.stop_play()();
	document.querySelectorAll("#list-area > .sound-button.playing").forEach(e=>{
		e.classList.remove("playing")
		e.querySelector(".play").disabled = false
	})
}
document.getElementById("enable-preview").onchange = _=>{
	eel.toggle_preview(document.getElementById("enable-preview").checked)();
}
document.getElementById("api").onchange =e=>{
	if (e.target.value == "favorites"){
		start_search()
	}
}


var search = document.getElementById("search");
var area = document.getElementById("list-area");
async function start_search(){
	let api = document.getElementById("api").value;
	let value = search.value.trim()
	if (api != "favorites" && !value){return}

	let results = [];
	area.innerHTML = ""
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
		area.innerHTML = "Nothing found"
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
start_search() // onload


function addButton(args){
	let b = document.createElement("div");
	b.className = "sound-button"
	b.setAttribute("data-url", args.link)
	let but = document.createElement("button")
	but.innerHTML = "▶"
	but.className = "play"
	but.onclick = _=>{
		b.classList.add("playing")
		but.disabled = true
		play_it(args.link)
	}
	let title = document.createElement("span")
	title.innerHTML = args.title
	b.appendChild(but)
	b.appendChild(title)
	let fav = document.createElement("button")
	fav.innerHTML = "⭐️"
	fav.className = "favorite"
	if (args.local){
		fav.innerHTML = "❌"
		fav.onclick = _=>{
			eel.delete_sound(args.link)
			b.classList.add("deleted")
			fav.disabled = true
			but.disabled = true
			setTimeout(_=>{
				b.remove()
			}, 1000)
		}
	} else{
		fav.onclick = _=>{
			eel.save_sound(args.link, args.title)
			fav.disabled = true
		}
	}
	b.appendChild(fav)
	if (args.duration){
		let t = document.createElement("span")
		t.className = "time"
		t.innerHTML = args.duration
		b.appendChild(t)
	}
	area.appendChild(b)
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
			element.append(t)
		}
		setTimeout(function() {
			element.classList.remove("playing")
			element.querySelector(".play").disabled = false
		}, duration * 1000)
	}
}