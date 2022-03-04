// TODO: don"t remove table, adjust

var current_sentence_index = 0;
var current_columns = [];

// On document load
window.onload = function() {
};

function button_handle(type) {
	if (type == "previous") {
		if (current_sentence_index > 0) {
			current_sentence_index -= 1
			inject_sentence(sentences[current_sentence_index]);
		}
	}
	else if (type == "next") {
		if (current_sentence_index < sentences.length-1) {
			current_sentence_index += 1
			inject_sentence(sentences[current_sentence_index]);
		}
	}
	else if (type == "save") {
		var content = "";
		var sentences_len_t = sentences.length;
		for (let i = 0; i < sentences_len_t; i++) {
			var sentence_t = sentences[i];
			content += "# sent_id = " + sentence_t["sent_id"] + "\n";
			content += "# text = " + sentence_t["text"] + "\n";
			var parts_t = sentence_t["parts"];
			var parts_len_t = parts_t.length;
			for (let j = 0; j < parts_len_t; j++) {
				var cols_t = parts_t[j];
				var cols_len_t = cols_t.length;
				for (let k = 0; k < cols_len_t; k++) {
					content += cols_t[k];
					if (k != cols_len_t-1) content += "\t";
				}
				content += "\n";
			}
			if (i != sentences_len_t-1) content += "\n";
		}
		var conllu_blob = new Blob([content], {type: "text/plain"});
		var url = window.URL.createObjectURL(conllu_blob);
		var anchor = document.createElement("a");
		anchor.href = url;
		anchor.download = "main.conllu";
		anchor.click();
		window.URL.revokeObjectURL(url);
		document.removeChild(anchor);
	}
	else if (type == "do") {

	}
	else if (type == "reset") {

	}
}

// On input file load
document.getElementById("inputfile").addEventListener("change", function() {
	var fr = new FileReader();
	fr.readAsText(this.files[0]);
	fr.onload = function() {
		document.getElementById("inputfile").remove();
		document.getElementById("load-file").remove();

		const previous_button = document.createElement("button");
		previous_button.id = "previous";
		previous_button.innerHTML = "Previous";
		document.body.append(previous_button);
		
		const reset_button = document.createElement("button");
		reset_button.id = "reset";
		reset_button.innerHTML = "Reset";
		document.body.append(reset_button);

		const row_select_input = document.createElement("input");
		row_select_input.type = "number";
		row_select_input.id = "row_select";
		document.body.append(row_select_input);

		const row_select_select = document.createElement("select");
		row_select_select.id = "row_select";
		var row_select_options = ["Go to sentence", "Add row", "Remove row"];
		for (let i = 0; i < row_select_options.length; i++) {
			var row_select_option = document.createElement("option");
			row_select_option.innerHTML = row_select_options[i];
			row_select_select.append(row_select_option);
		}
		document.body.append(row_select_select);

		const do_button = document.createElement("button");
		do_button.id = "do";
		do_button.innerHTML = "Do";
		document.body.append(do_button);


		const col_add_rm_select = document.createElement("select");
		col_add_rm_select.id = "col_add_rm";
		var col_sel_placeholder = document.createElement("option");
		col_sel_placeholder.disabled = true;
		col_sel_placeholder.selected = true;
		col_sel_placeholder.innerHTML = "Select Column to add or remove";
		col_add_rm_select.append(col_sel_placeholder);
		var column_options = cats.concat(features);
		for (let i = 0; i < column_options.length; i++) {
			var column_option = document.createElement("option");
			column_option.innerHTML = column_options[i];
			col_add_rm_select.append(column_option);
		}
		col_add_rm_select.addEventListener("change", (event) => {
			column_change(event.target.value);
		});
		document.body.append(col_add_rm_select);

		row_select_input.style = "margin: 5px";
		row_select_select.style = "margin: 5px";
		col_add_rm_select.style = "margin: 5px";

		const next_button = document.createElement("button");
		next_button.id = "next";
		next_button.innerHTML = "Next";
		document.body.append(next_button);

		const save_button = document.createElement("button");
		save_button.id = "save";
		save_button.innerHTML = "Save";
		document.body.append(save_button);

		const buttons = document.getElementsByTagName("button");
		for (let i = 0; i < buttons.length; i++) {
			buttons[i].addEventListener("click", function() {
				button_handle(buttons[i].id);
			});
			buttons[i].style = "margin: 5px";
		}

		let br = document.createElement("br");
		br.id = "br";
		document.body.append(br);

		const p_text = document.createElement("p");
		p_text.id = "sentence_text";
		document.body.append(p_text);
		document.body.append(br);

		const table = document.createElement("table");
		table.id = "sentence_table";
		document.body.append(table);

		current_columns = ["ID", "FORM", "LEMMA", "UPOS", "XPOS", "FEATS", "HEAD", "DEPREL", "DEPS", "MISC"];
		parse_file(fr.result);
		inject_sentence(sentences[0]);
	}
})

function column_change(column_option) {
	if (current_columns.includes(column_option)) current_columns.splice(current_columns.indexOf(column_option), 1);
	else current_columns = current_columns.concat(column_option);
	inject_sentence(sentences[current_sentence_index]);
}

// document.getElementById("inputfile").addEventListener("change", read_file);

// function read_file() {
// 	var fr = new FileReader();
// 	fr.readAsText(this.files[0]);
// 	fr.onload = init_page(fr.result);
// }

// function init_page(file_content) {
// 	parse_file(file_content);
// }

var sentences = [];
function parse_file(text) {
	const lines = text.split("\n");
	var sentence_count = 0;
	var sentence = {};
	for (let i = 0; i < lines.length; i++) {
		var line = lines[i];
		if (line.trim() == "" && sentence[0] != undefined) {
			sentences[sentence_count] = sentence;
			sentence_count += 1;
			sentence = {};
		}
		else if (line.startsWith("#")) {
			let matches = line.match(/#(.*)=(.*)/);
			sentence[matches[1].trim()] = matches[2].trim();
		}
		else {
			let parts = line.split("\t");
			let parts_d = {};

			for (let i = 0; i < parts.length; i++) {
				parts_d[cats[i]] = parts[i].trim();
			}
			let feats = parts_d["FEATS"];
			if (feats != "_") {
				if (!feats.includes("|")) feats = [feats];
				else feats = feats.split("|");
				for (let i = 0; i < feats.length; i++) {
					let feat_t = feats[i].split("=");
					parts_d[feat_t[0]] = feat_t[1];
				}
			}
			sentence[Object.keys(sentence).length-2] = parts_d; // -2 for sent_id & text
		}
	}
}

var cats = ["ID", "FORM", "LEMMA", "UPOS", "XPOS", "FEATS", "HEAD", "DEPREL", "DEPS", "MISC"];
var features = ["Abbr", "Animacy", "Aspect", "Case", "Clusivity", "Definite", "Degree", "Evident", "Foreign", "Gender", "Mood", "NounClass", "Number", "NumType", "Person", "Polarity", "Polite", "Poss", "PronType", "Reflex", "Tense", "Typo", "VerbForm", "Voice"];

function create_table() {

}

function inject_sentence(sentence) {
	let t_s_i = document.getElementById("sentence_indices");
	if (document.getElementById("sentence_indices") != undefined) document.body.removeChild(t_s_i);
	let t = document.getElementById("table");
	if (t != undefined) document.body.removeChild(t);
	let br = document.getElementById("br");
	if (br != undefined) document.body.removeChild(br);

	// Show sentence in table form with indices
	let table = document.createElement("table");
	table.id = "sentence_indices";
	let thead = document.createElement("thead");
	let tbody = document.createElement("tbody");
	table.append(thead);
	table.append(tbody);
	let row = document.createElement("tr");
	let form_count = Object.keys(sentence).length-2; // -2 for sent_id & text
	for (let i = 0; i < form_count; i++) {
		let heading = document.createElement("th");
		heading.innerHTML = sentence[i]["ID"];
		heading.style.textAlign = "center";
		row.append(heading);
	}
	thead.append(row);
	row = document.createElement("tr");
	for (let i = 0; i < form_count; i++) {
		let data = document.createElement("td");
		data.innerHTML = sentence[i]["FORM"];
		data.style.textAlign = "center";
		row.append(data);
	}
	tbody.append(row);
	document.body.append(table);
	
	br = document.createElement("br");
	br.id = "br";
	document.body.append(br);

	// Show table
	table = document.createElement("table");
	table.id = "table";
	thead = document.createElement("thead");
	tbody = document.createElement("tbody");
	table.append(thead);
	table.append(tbody);
	row = document.createElement("tr");
	for (let i = 0; i < current_columns.length; i++) {
		let heading = document.createElement("th");
		heading.innerHTML = current_columns[i];
		heading.addEventListener("click", function() {
			column_click(heading.innerHTML);
		});
		row.append(heading);
	}
	thead.append(row);

	for (let i = 0; i < form_count; i++) {
		let row = document.createElement("tr");
		for (let j = 0; j < current_columns.length; j++) {
			let data = document.createElement("td");
			if (sentence[i][current_columns[j]] == undefined) data.innerHTML = "_";
			else data.innerHTML = sentence[i][current_columns[j]];
			data.style.textAlign = "center";
			data.contentEditable = "true";
			row.append(data);
		}
		tbody.append(row);
	}
	document.body.append(table);
}

function column_click(column_name) {
	var arr_t = [];
	let index_remove = current_columns.indexOf(column_name);
	for (let i = 0; i < current_columns.length; i++) {
		if (i != index_remove) arr_t = arr_t.concat(current_columns[i]);
	}
	current_columns = arr_t;
	inject_sentence(sentences[current_sentence_index]);
}

function error_handle() {

}