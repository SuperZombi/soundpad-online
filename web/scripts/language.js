var LANGUAGE;
function LANG(word){
	return LANGUAGE[word] ? LANGUAGE[word] : word;
}
async function getTranslation(){
	let translation = document.querySelector('.setting[name=language]').value
	LANGUAGE = await getTranslationAsk(translation)
	localizeHtmlPage(LANGUAGE);
}
async function getTranslationAsk(lang){
	var lang_file = await eel.get_translation(lang)()
	if (lang_file){
		if (lang_file.__root__?.inherit){
			let parrent_translate = await getTranslationAsk(lang_file.__root__.inherit)
			return {...parrent_translate, ...lang_file}
		}
		return lang_file
	}
}
function localizeHtmlPage(lang)
{
	var objects = document.querySelectorAll('[translation]');
	for (var j = 0; j < objects.length; j++)
	{
		function trim(str, ch) {
			var start = 0, end = str.length;
			while(start < end && str[start] === ch)
			++start;
			while(end > start && str[end - 1] === ch)
			--end;
			return (start > 0 || end < str.length) ? str.substring(start, end) : str;
		}

		let atr = objects[j].getAttribute("translation")
		atr.split(" ").forEach(e=>{
			let cur = trim(e, "_")
			let arr = cur.split(":")
			if (arr.length > 1){
				if (lang[arr[1]]){
					objects[j].setAttribute(arr[0], lang[arr[1]])
				}
			}
			else{
				if (lang[arr[0]]){
					objects[j].innerHTML = lang[arr[0]]
				}
			}
		})
	}
}