
var current_columns = ["id", "form", "lemma", "upos", "xpos", "feats", "head", "deprel", "deps", "misc"];

// On document load
window.onload = function () {
    window.CSRF_TOKEN = document.getElementsByName('csrfmiddlewaretoken')[0];
    window.sent_id = document.getElementById('sentence.sent_id').innerHTML;
    window.text = document.getElementById('sentence.text').innerHTML;
    window.cells = JSON.parse(document.getElementById('annotation.cats').innerHTML);
    window.notes = document.getElementById('annotation.notes').innerHTML;
    window.status = document.getElementById('annotation.status').innerHTML;
    window.status_d = { "not": "Not", "half": "Half", "done": "Done" };
    window.errors = document.getElementById('errors').innerHTML;
    window.graph_preference = document.getElementById('graph_preference').innerHTML;
    $('#sent_id').remove();
    $('#text').remove();
    $('#cells').remove();
    $('#notes').remove();
    $('#errors').remove();
    $('#graph_preference').remove();
    let cells_keys = get_sorted_cells_keys();
    for (let i = 0; i < cells_keys.length; i++) {
        let feats = window.cells[cells_keys[i]]['feats'];
        if (feats != '_') {
            feats = feats.split('|');
            for (let j = 0; j < feats.length; j++) {
                let matches = feats[j].match(/(.+)=(.+)/);
                let column = matches[1].toLowerCase();
                window.cells[cells_keys[i]][column] = matches[2];
            }
        }
    }
    window.initial_cells = window.cells;
    window.edits = []; // use for undo, redos
    window.edits_undone = [];
    window.last_focus = null;
    window.last_focus_value = null;
    init_page();
};

function post_to_save(type, number) {
    // current columns can be sent for continuing with the same set
    // type should be sent for next, prev, or just save
    let form = document.createElement('form');
    form.method = "post";
    form.action = `${get_sentence_id_url()}`;
    form.enctype = "multipart/form-data";
    let csrf_token_input = document.getElementsByName('csrfmiddlewaretoken')[0];
    form.append(csrf_token_input);

    // Type
    let input = document.createElement('input');
    input.type = 'hidden';
    input.name = "type";
    input.value = type;
    form.append(input);
    if (type == "go") {
        input = document.createElement('input');
        input.type = 'hidden';
        input.name = "number";
        input.value = parseInt(number);
        form.append(input);
    }

    // Cells
    input = document.createElement('input');
    input.type = 'hidden';
    input.name = "data";
    input.value = JSON.stringify(window.cells);
    form.append(input);
    document.body.append(form);

    // Notes
    input = document.createElement('input');
    input.type = 'hidden';
    input.name = "notes";
    input.value = window.notes;
    form.append(input);
    document.body.append(form);

    // Status
    input = document.createElement('input');
    input.type = 'hidden';
    input.name = "status";
    input.value = window.status;
    form.append(input);
    document.body.append(form);

    form.submit();
}

function get_sentence_id_url() {
    var url = window.location.href;
    let matches = url.match(/\/(\d+$)/);
    return parseInt(matches[1]);
}

function get_sorted_cells_keys() {
    let cells_keys = Object.keys(window.cells);
    let new_list = [];
    for (let i = 1; i < cells_keys.length * 2; i++) {
        if (cells_keys.indexOf(`${i}-${i + 1}`) != -1) new_list.push(`${i}-${i + 1}`);
        if (cells_keys.indexOf(`${i}`) != -1) new_list.push(`${i}`);
    }
    return new_list;
}

function button_handle(type, number, way) {
    if (["previous", "next", "save"].includes(type)) {
        post_to_save(type);
    }
    else if (type == "col_add_rm_button") {
        let sel = document.getElementById("col_add_rm_select");
        let opts = sel.options;
        for (let i = 0; i < opts.length; i++) {
            if (opts[i].selected) column_change(opts[i].text.toLowerCase());
        }
    }
    else if (type == "do") {
        let sel = document.getElementById("row_select_select");
        let selected = sel.options[sel.selectedIndex].text;
        let input_number = document.getElementById("row_select_input").value;
        if (selected == "Go to sentence") {
            post_to_save("go", input_number);
        }
        else if (["Add row", "Remove row"].indexOf(selected) != -1) {
            if (number != undefined) {
                input_number = number;
                if (way == "down") selected = "Add row";
                else if (way == "up") selected = "Remove row";
            }
            let cells_keys = get_sorted_cells_keys();
            if (cells_keys.indexOf(input_number) == -1) return;
            let row_place = cells_keys.indexOf(input_number);
            if (selected == "Add row") {
                let first_num = parseInt(input_number);
                if (first_num == NaN) return;
                let new_row = `${first_num}-${first_num + 1}`;
                window.cells[new_row] = { ...window.cells[cells_keys[row_place]] };
                window.cells[(parseInt(cells_keys[cells_keys.length - 1]) + 1).toString()] = { ...window.cells[cells_keys[cells_keys.length - 1]] };
                for (let i = cells_keys.length - 1; i > row_place; i--) {
                    if (cells_keys[i].indexOf('-') != -1) {
                        let matches = cells_keys[i].match(/(\d+)-(\d+)/);
                        let n1 = matches[1];
                        window.cells[`${n1 + 1}-${n1 + 2}`] = window.cells[cells_keys[i]];
                    }
                    else window.cells[cells_keys[i]] = window.cells[cells_keys[i - 1]];
                }
            }
            else if (selected == "Remove row") {
                let new_key = "";
                if (input_number.includes('-')) {
                    delete window.cells[input_number];
                }
                else {
                    for (let i = row_place; i < cells_keys.length - 1; i++) {
                        let key = cells_keys[i + 1];
                        if (key.includes('-')) {
                            let first_num = parseInt(key.split('-')[0]);
                            new_key = `${first_num - 1}-${first_num}`;
                        }
                        else {
                            new_key = `${parseInt(key) - 1}`;
                        }
                        window.cells[new_key] = window.cells[cells_keys[i + 1]];
                        delete window.cells[cells_keys[i + 1]];
                    }
                    delete window.cells[cells_keys[cells_keys.length - 1]];
                }
            }
            inject_sentence();
        }
    }
    else if (type == "undo") {
        if (window.edits.length == 0) return;
        let last_edit = window.edits.pop();
        let undone_pair = [last_edit[0], window.cells[last_edit[0][0]][last_edit[0][1]]];
        window.edits_undone.push(undone_pair);
        window.cells[last_edit[0][0]][last_edit[0][1]] = last_edit[1];
        inject_sentence();
    }
    else if (type == "redo") {
        if (window.edits_undone.length == 0) return;
        let last_edit_undone = window.edits_undone.pop();
        let redone_pair = [last_edit_undone[0], window.cells[last_edit_undone[0][0]][last_edit_undone[0][1]]];
        window.edits.push(redone_pair);
        window.cells[last_edit_undone[0][0]][last_edit_undone[0][1]] = last_edit_undone[1];
        inject_sentence();
    }
    else if (type == "reset") {
        window.cells = window.initial_cells;
        inject_sentence();
    }
    else if (type == "status") {
        let button = $('#status')[0];
        if (window.status == "not") {
            button.innerHTML = "Done";
            button.className = button.className.replace('border', 'border-success');
            window.status = "done";
        }
        else if (window.status == "done") {
            button.innerHTML = "Half";
            button.className = button.className.replace('border-success', 'border-danger');
            window.status = "half";
        }
        else if (window.status == "half") {
            button.innerHTML = "Not";
            button.className = button.className.replace('border-danger', 'border');
            window.status = "not";
        }
    }
    else if (type == "profile") {
        post_to_save(type);
    }
}

// Keyboard shortcuts
document.onkeyup = function (e) {
    if (e.key.toLowerCase() == "p" && e.altKey) {
        button_handle("previous");
    }
    else if (e.key.toLowerCase() == "r" && e.altKey) {
        button_handle("reset");
    }
    else if (e.key.toLowerCase() == "d" && e.altKey) {
        button_handle("do");
    }
    else if (e.key.toLowerCase() == "x" && e.altKey) {
        document.getElementById("col_add_rm_select").focus();
    }
    else if (e.key.toLowerCase() == "c" && e.altKey) {
        button_handle("col_add_rm_button");
    }
    else if (e.key.toLowerCase() == "n" && e.altKey) {
        button_handle("next");
    }
    else if (e.key.toLowerCase() == "s" && e.altKey) {
        button_handle("save");
    }
    else if (e.key.toLowerCase() == "t" && e.altKey) {
        document.getElementById("word_lines").focus();
    }
    else if ((e.key == "ArrowUp" || e.key == "ArrowDown" || e.key == "ArrowLeft" || e.key == "ArrowRight") && e.ctrlKey) {
        if (!document.getElementById('word_lines').contains(document.activeElement)) return;
        let matches = document.activeElement.id.match(/(.+) (.+)/);
        if (matches.length == 3) {
            let cells_keys = get_sorted_cells_keys();
            let row_id = cells_keys.indexOf(matches[1]);
            let column_order = current_columns.indexOf(matches[2]);

            let form_count = document.getElementById("word_lines").getElementsByTagName("tr").length - 1;
            if (e.key == "ArrowUp" && row_id != 0) {
                document.getElementById(`${cells_keys[row_id - 1]} ${matches[2]}`).focus();
            }
            else if (e.key == "ArrowDown" && row_id != form_count - 1) {
                document.getElementById(`${cells_keys[row_id + 1]} ${matches[2]}`).focus();
            }
            else if (e.key == "ArrowRight" && column_order != current_columns.length - 1) {
                document.getElementById(`${matches[1]} ${current_columns[column_order + 1]}`).focus();
            }
            else if (e.key == "ArrowLeft" && column_order != 0) {
                document.getElementById(`${matches[1]} ${current_columns[column_order - 1]}`).focus();
            }
        }
    }
    else if (e.shiftKey && e.altKey) {
        if (e.key == "ArrowUp") {
            button_handle("do", document.activeElement.id.split(' ')[0], "up");
        }
        else if (e.key == "ArrowDown") {
            button_handle("do", document.activeElement.id.split(' ')[0], "down");
        }
    }
};

function column_change(column_option) {
    if (current_columns.includes(column_option)) {
        current_columns.splice(current_columns.indexOf(column_option), 1);
        if (cats_low.includes(column_option)) $(`option:contains('${cats[cats_low.indexOf(column_option)]}')`)[0].style = "color: black";
        else $(`option:contains('${features[features_low.indexOf(column_option)]}')`)[0].style = "color: black";
    }
    else {
        current_columns = current_columns.concat(column_option);
        if (cats_low.includes(column_option)) $(`option:contains('${cats[cats_low.indexOf(column_option)]}')`)[0].style = "color: gray";
        else $(`option:contains('${features[features_low.indexOf(column_option)]}')`)[0].style = "color: gray";
    }
    sort_columns();
    inject_sentence();
}

function sort_columns() {
    for (let i = 0; i < cats.length; i++) {
        let cat_t = cats_low[i];
        if (current_columns.includes(cat_t)) {
            current_columns.splice(current_columns.indexOf(cat_t), 1);
            current_columns = current_columns.concat(cat_t);
        }
    }
    for (let i = 0; i < features.length; i++) {
        let feat_t = features_low[i];
        if (current_columns.includes(feat_t)) {
            current_columns.splice(current_columns.indexOf(feat_t), 1);
            current_columns = current_columns.concat(feat_t);
        }
    }
}

function init_page() {

    let div_cont = document.createElement('div');
    div_cont.className = 'input-group d-flex';
    let div_row = document.createElement('div');
    div_row.className = 'row mx-auto';

    // create button for profile
    let div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    let button = document.createElement("button");
    button.id = "profile";
    button.innerHTML = "Profile";
    div_col.append(button);
    div_row.append(div_col);

    // split
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    div_row.append(div_col);

    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    button = document.createElement("button");
    button.id = "previous";
    button.innerHTML = "Previous";
    div_col.append(button);
    div_row.append(div_col);

    // split
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    div_row.append(div_col);

    // reset
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    button = document.createElement("button");
    button.id = "reset";
    button.innerHTML = "Reset";
    div_col.append(button);
    div_row.append(div_col);

    // undo
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    button = document.createElement("button");
    button.id = "undo";
    button.innerHTML = "Undo";
    div_col.append(button);
    div_row.append(div_col);

    // redo
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    button = document.createElement("button");
    button.id = "redo";
    button.innerHTML = "Redo";
    div_col.append(button);
    div_row.append(div_col);

    // split
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    div_row.append(div_col);

    // do_input
    div_col = document.createElement('div');
    div_col.className = 'col';
    let input = document.createElement("input");
    input.type = "text";
    input.id = "row_select_input";
    input.className = "form-control";
    div_col.append(input);
    div_row.append(div_col);

    // do_select
    div_col = document.createElement('div');
    div_col.className = 'col';
    let select = document.createElement("select");
    select.id = "row_select_select";
    select.className = "form-select";
    let options = ["Go to sentence", "Add row", "Remove row"];
    for (let i = 0; i < options.length; i++) {
        let option = document.createElement("option");
        option.innerHTML = options[i];
        select.append(option);
    }
    div_col.append(select);
    div_row.append(div_col);

    // do_button
    div_col = document.createElement('div');
    div_col.className = 'col';
    button = document.createElement("button");
    button.id = "do";
    button.innerHTML = "Do";
    div_col.append(button);
    div_row.append(div_col);

    // split
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    div_row.append(div_col);

    // status
    div_col = document.createElement('div');
    div_col.className = 'col';
    button = document.createElement("button");
    button.id = "status";
    button.innerHTML = window.status_d[window.status];
    div_col.append(button);
    div_row.append(div_col);

    // split
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    div_row.append(div_col);

    // column_select
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    select = document.createElement("select");
    select.id = "col_add_rm_select";
    select.className = "form-select";
    select.multiple = true;
    option = document.createElement("option");
    option.disabled = true;
    option.selected = true;
    option.innerHTML = "Columns";
    select.append(option);
    let cats_no_id = [...cats];
    cats_no_id.shift();
    options = cats_no_id.concat(features);
    for (let i = 0; i < options.length; i++) {
        option = document.createElement("option");
        option.innerHTML = options[i];
        if (current_columns.includes(options[i].toLowerCase())) {
            option.style = "color: gray;";
        }
        else {
            option.style = "color: black;";
        }
        select.append(option);
    }
    div_col.append(select);
    div_row.append(div_col);

    // column_button
    div_col = document.createElement('div');
    div_col.className = 'col';
    button = document.createElement("button");
    button.id = "col_add_rm_button";
    button.innerHTML = "Show/Hide";
    div_col.append(button);
    div_row.append(div_col);

    // split
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    div_row.append(div_col);

    // next
    div_col = document.createElement('div');
    div_col.className = 'col';
    button = document.createElement("button");
    button.id = "next";
    button.innerHTML = "Next";
    div_col.append(button);
    div_row.append(div_col);

    // split
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    div_row.append(div_col);

    // save
    div_col = document.createElement('div');
    div_col.className = 'col';
    button = document.createElement("button");
    button.id = "save";
    button.innerHTML = "Save";
    div_col.append(button);
    div_row.append(div_col);

    div_cont.append(div_row);
    document.body.append(div_cont);

    let buttons = document.getElementsByTagName("button");
    for (let i = 0; i < buttons.length; i++) {
        buttons[i].addEventListener("click", function () {
            button_handle(buttons[i].id);
        });
        buttons[i].className = "btn btn-light border";
    }

    inject_sentence();
}

var cats = ["ID", "FORM", "LEMMA", "UPOS", "XPOS", "FEATS", "HEAD", "DEPREL", "DEPS", "MISC"];
var cats_low = ["id", "form", "lemma", "upos", "xpos", "feats", "head", "deprel", "deps", "misc"];
var features = ["Abbr", "Animacy", "Aspect", "Case", "Clusivity", "Definite", "Degree", "Evident", "Foreign", "Gender", "Mood", "NounClass", "Number", "NumType", "Person", "Polarity", "Polite", "Poss", "PronType", "Reflex", "Tense", "Typo", "VerbForm", "Voice"];
var features_low = ["abbr", "animacy", "aspect", "case", "clusivity", "definite", "degree", "evident", "foreign", "gender", "mood", "nounclass", "number", "numtype", "person", "polarity", "polite", "poss", "prontype", "reflex", "tense", "typo", "verbform", "voice"];
const all_column_count = cats.length + features.length;

function inject_sentence() {
    $('br').remove();
    $('#sentence_text').remove();
    $('#word_lines').remove();
    let cells = window.cells;

    // Show sentence in table form with indices
    let sentence_text = document.createElement("table");
    sentence_text.id = "sentence_text";
    sentence_text.className = "table-sm table-borderless mx-auto";
    let tbody = document.createElement("tbody");
    let row1 = document.createElement("tr");
    let row2 = document.createElement("tr");
    let cells_keys = get_sorted_cells_keys();
    let form_count = cells_keys.length;
    for (let i = 0; i < form_count; i++) {
        if (cells_keys[i].indexOf('-') != -1) continue;
        let heading = document.createElement("td");
        heading.innerHTML = cells_keys[i];
        heading.style = "text-align: center; color: gray;";
        let data = document.createElement("td");
        data.innerHTML = cells[cells_keys[i]]["form"];
        data.style = "text-align: center;";
        row1.append(data);
        row2.append(heading);
    }
    tbody.append(row1);
    tbody.append(row2);
    sentence_text.append(tbody);
    document.body.append(document.createElement("br"));
    document.body.append(sentence_text);
    document.body.append(document.createElement("br"));

    // Show table
    let word_lines = document.createElement("table");
    word_lines.id = "word_lines";
    word_lines.className = "table";
    let thead = document.createElement("thead");
    tbody = document.createElement("tbody");
    word_lines.append(thead);
    word_lines.append(tbody);
    let row = document.createElement("tr");
    for (let i = 0; i < current_columns.length; i++) {
        let heading = document.createElement("th");
        if (cats_low.includes(current_columns[i])) heading.innerHTML = cats[cats_low.indexOf(current_columns[i])];
        else heading.innerHTML = features[features_low.indexOf(current_columns[i])];
        heading.style = 'text-align:center';
        heading.addEventListener("click", function () {
            column_click(heading.innerHTML.toLowerCase());
        });
        row.append(heading);
    }
    thead.append(row);

    for (let i = 0; i < form_count; i++) {
        let feats = cells[cells_keys[i]]['feats'].split('|');
        if (feats != '_') {
            for (let j = 0; j < feats.length; j++) {
                let matches = feats[j].match(/(.+)=(.+)/);
                let column = matches[1].toLowerCase;
                cells[cells_keys[i]][column] = matches[2];
            }
        }
        let row = document.createElement("tr");
        for (let j = 0; j < current_columns.length; j++) {
            let column_t = current_columns[j];
            let row_t = cells_keys[i];
            let data = document.createElement("td");
            if (column_t == "id") data.innerHTML = row_t;
            else if (cells[row_t][column_t] == undefined) data.innerHTML = "_";
            else data.innerHTML = cells[row_t][column_t];
            data.id = `${row_t} ${column_t}`;
            data.style.textAlign = "center";
            if (column_t != "id") data.contentEditable = true;
            data.addEventListener("focus", (event) => {
                window.last_focus = [row_t, column_t];
                window.last_focus_value = event.target.innerHTML;
            });
            data.addEventListener("blur", (event) => { // potential problem with unfocusing after column removal!
                if (window.last_focus_value != event.target.innerHTML) {
                    cell_change(row_t, column_t, event.target.innerHTML);
                    window.edits.push([window.last_focus, window.last_focus_value]);
                    display_errors();
                }
            });
            row.append(data);
        }
        tbody.append(row);
    }
    document.body.append(word_lines);
    document.body.append(document.createElement("br"));

    create_graph();
    document.body.append(document.createElement("br"));
    display_errors();
}

function create_graph() {
    if (window.graph_preference == "none") return;
    else if (window.graph_preference == "conllu.js") {
        $('#vis').remove();
        $('#dep_graph').remove();
        let cells = window.cells;
        let vis = document.createElement('div');
        vis.id = "vis";
        let dep_graph = document.createElement('div');
        dep_graph.id = "dep_graph";
        dep_graph.className = "conllu-parse";
        dep_graph.attributes = 'data-visid="vis" data-inputid="input" data-parsedid="parsed" data-logid="log"';
        let order = ['form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps'] // id & misc removed
        let cells_keys = get_sorted_cells_keys();
        for (let i = 0; i < cells_keys.length; i++) {
            let key = cells_keys[i];
            dep_graph.innerHTML += key + "\t";
            for (let j = 0; j < 8; j++) {
                dep_graph.innerHTML += cells[key][order[j]] + "\t";
            }
            dep_graph.innerHTML += cells[key]["misc"] + "\n"; // misc
        }
        document.body.append(vis);
        document.body.append(dep_graph);
        Annodoc.activate(Config.bratCollData, {});
    }
    else if (window.graph_preference == "spacy") {
        $.post("/spacy/",
            {
                cells: JSON.stringify(window.cells)
            },
            function (data) {
                let textarea_t = document.createElement('textarea');
                textarea_t.innerHTML = data;
                let graph = document.createElement('div');
                graph.id = "spacy";
                graph.innerHTML = textarea_t.value;
                document.body.append(graph);
                $("#spacy").after($("#error_div"));
            });
    }
    else if (window.graph_preference == "ud") {
        $.post("/ud_graph/",
            {
                cells: JSON.stringify(window.cells),
                sent_id: window.sent_id,
                text: window.text,
            },
            function (data) {
                let graph = document.createElement('embed');
                graph.id = "ud_graph";
                graph.type = "text/html";
                graph.src = data;
                document.body.append(graph);
                $("#ud_graph").after($("#error_div"));
            });
    }
}

function display_errors() {
    $('#error_div').remove();
    $('#error_header').remove();
    $('#error_body').remove();

    $.post("/error/",
        {
            cells: JSON.stringify(window.cells),
            sent_id: window.sent_id,
            text: window.text,
        },
        function (data) {
            window.errors = data;
        });

    let error_div = document.createElement('div');
    error_div.id = "error_div";
    error_div.className = "card border-danger bg-light mb-3";
    error_div.style = "max-width: 100rem;";
    let error_header = document.createElement('div');
    error_div.append(error_header);
    error_header.id = "error_header";
    error_header.className = "card-header border-danger";
    error_header.innerHTML = 'Errors';
    let error_body = document.createElement('div');
    error_body.id = "error_body";
    error_body.className = "card-body";
    error_div.append(error_body);
    let errors = window.errors.split('\n');
    for (let i = 0; i < errors.length; i++) {
        error_body.innerHTML += errors[i];
        error_body.append(document.createElement('br'));
    }
    document.body.append(error_div);
    document.body.append(document.createElement('br'));
}

function cell_change(key, column, cell) {
    // autocomplete
    if (['aspect', 'case', 'evident', 'mood', 'number', 'number[psor]', 'numtype', 'person', 'person[psor]', 'polarity', 'prontype', 'tense', 'verbform', 'voice', 'upos', 'xpos', 'deprel'].includes(column)) {
        console.log('autocomplete');
    }

    if (column == "id") window.cells[cell] = window.cells[key];
    else if (column == "feats") {
        window.cells[key]['feats'] = cell;
        let feats = cell.split('|');
        for (let j = 0; j < feats.length; j++) {
            let matches = feats[j].match(/(.+)=(.+)/);
            let column = matches[1].toLowerCase();
            window.cells[key][column] = matches[2];
            if (current_columns.indexOf(column) != -1) {
                document.getElementById(`${key} ${column}`).innerHTML = matches[2];
            }
        }
    }
    else if (features_low.includes(column)) {
        window.cells[key][column] = cell;
        let new_feats = "";
        if (window.cells[key]['feats'] == "_") {
            new_feats = `${features[features_low.indexOf(column)]}=${cell}`;
        }
        else {
            let feats = window.cells[key]['feats'].split('|');
            for (let j = 0; j < feats.length; j++) {
                let matches = feats[j].match(/(.+)=(.+)/);
                let col_t = matches[1].toLowerCase();
                if (col_t == column) {
                    if (new_feats != "") new_feats += "|";
                    new_feats += `${features[features_low.indexOf(column)]}=${cell}`;
                }
                else {
                    if (new_feats != "") new_feats += "|";
                    new_feats += feats[j];
                }
            }
        }
        document.getElementById(`${key} feats`).innerHTML = new_feats;
        window.cells[key]['feats'] = new_feats;
    }
    else window.cells[key][column] = cell;
}

function column_click(column_name) {
    if (column_name == "id") return;
    var arr_t = [];
    let index_remove = current_columns.indexOf(column_name);
    for (let i = 0; i < current_columns.length; i++) {
        if (i != index_remove) arr_t = arr_t.concat(current_columns[i]);
    }
    current_columns = arr_t;
    inject_sentence();
}
