
// On document load
window.onload = function () {
    window.CSRF_TOKEN = document.getElementsByName('csrfmiddlewaretoken')[0];
    window.sent_id = document.getElementById('sentence.sent_id').innerHTML;
    window.text = document.getElementById('sentence.text').innerHTML;
    window.cells = JSON.parse(document.getElementById('annotation.cats').innerHTML);
    window.notes = document.getElementById('annotation.notes').innerHTML;
    window.status = parseInt(document.getElementById('annotation.status').innerHTML);
    window.status_d = { 0: "Incomplete", 1: "Finished", 2: "Draft" };
    window.errors = document.getElementById('errors').innerHTML;
    window.graph_preference = parseInt(document.getElementById('graph_preference').innerHTML);
    window.graph_d = { 0: "None", 1: "conllu.js", 2: "treex", 3: "spacy" };
    let error_condition_t = document.getElementById('error_condition').innerHTML;
    if (error_condition_t == "1") window.error_condition = 1;
    else window.error_condition = 0;
    window.current_columns = document.getElementById('current_columns').innerHTML.replace('[', '').replace(']', '').replaceAll("'", '').split(', '); // splitting list coming from preferences
    $('#sent_id').remove();
    $('#text').remove();
    $('#cells').remove();
    $('#notes').remove();
    $('#errors').remove();
    $('#graph_preference').remove();
    $('#error_condition').remove();
    $('#current_columns').remove();
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
    window.initial_cells = JSON.parse(JSON.stringify(window.cells)); // deep copy
    window.edits = []; // use for undo, redos
    window.edits_undone = [];
    window.last_focus = null;
    window.last_focus_value = null;
    init_page();
};

function get_data_changed() {
    let cells_keys = Object.keys(window.cells);
    let initial_cells_keys = Object.keys(window.initial_cells);
    if (cells_keys.length != initial_cells_keys.length) return true;
    for (let i = 0; i < cells_keys.length; i++) {
        if (cells_keys[i] != initial_cells_keys[i]) return true;

        for (let j = 0; j < cats_low.length; j++) {
            if (window.cells[cells_keys[i]][cats_low[j]] != window.initial_cells[initial_cells_keys[i]][cats_low[j]]) {
                return true;
            }
        }
    }
    return false;
}

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

    // Data Changed
    input = document.createElement('input');
    input.type = 'hidden';
    input.name = "data_changed";
    input.value = get_data_changed();
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

    // Error condition
    input = document.createElement('input');
    input.type = 'hidden';
    input.name = "error_condition";
    input.value = window.error_condition;
    form.append(input);
    document.body.append(form);

    // Graph preference
    input = document.createElement('input');
    input.type = 'hidden';
    input.name = "graph_preference";
    input.value = window.graph_preference;
    form.append(input);
    document.body.append(form);

    // Current columns
    input = document.createElement('input');
    input.type = 'hidden';
    input.name = "current_columns";
    input.value = current_columns;
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
        if (input_number == "") return;
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
        if (window.status == 0) {
            button.className = button.className.replace('border', 'border-success');
            window.status = 1;
        }
        else if (window.status == 1) {
            button.className = button.className.replace('border-success', 'border-danger');
            window.status = 2;
        }
        else if (window.status == 2) {
            button.className = button.className.replace('border-danger', 'border');
            window.status = 0;
        }
        button.innerHTML = window.status_d[window.status];
    }
    else if (type == "profile") {
        post_to_save(type);
    }
    else if (type == "errors") {
        let button = $('button#errors')[0];
        if (window.error_condition == 0) {
            window.error_condition = 1;
            display_errors();
            $('#error_div')[0].hidden = false;
            let img = $('#exclamation-square-fill')[0].cloneNode(true);
            img.hidden = false;
            $('button#errors').find('img')[0].remove();
            button.append(img);
            button.setAttribute('title', 'Hide errors');
        }
        else if (window.error_condition == 1) {
            $('#error_div')[0].hidden = true;
            let img = $('#exclamation-square')[0].cloneNode(true);
            img.hidden = false;
            $('button#errors').find('img')[0].remove();
            button.append(img);
            button.setAttribute('title', 'Show errors');
            window.error_condition = 0;
        }
    }
    else if (type == "graph") {
        let select = $('select#graph')[0];
        let selected = select.options[select.selectedIndex].text;
        let options = $('select#graph').find('option');
        for (let i = 0; i < options.length; i++) {
            if (options[i].innerHTML == selected) options[i].style = "color: gray;";
            else options[i].style = "color: black;";
        }
        if (selected == window.graph_d[0]) window.graph_preference = 0;
        else if (selected == window.graph_d[1]) window.graph_preference = 1;
        else if (selected == window.graph_d[2]) window.graph_preference = 2;
        else if (selected == window.graph_d[3]) window.graph_preference = 3;
        create_graph();
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

    // previous-next button group
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    let btn_group = document.createElement('div');
    btn_group.className = 'btn-group';
    div_col.append(btn_group);

    // previous
    button = document.createElement("button");
    button.id = "previous";
    let img = $('#arrow-left')[0].cloneNode(true);
    img.hidden = false;
    button.setAttribute('data-bs-toggle', 'tooltip');
    button.setAttribute('data-bs-placement', 'bottom');
    button.setAttribute('title', 'Go to the previous sentence');
    button.append(img);
    btn_group.append(button);

    // next
    button = document.createElement("button");
    button.id = "next";
    img = $('#arrow-right')[0].cloneNode(true);
    img.hidden = false;
    button.append(img);
    button.setAttribute('data-bs-toggle', 'tooltip');
    button.setAttribute('data-bs-placement', 'bottom');
    button.setAttribute('title', 'Go to the next sentence');
    btn_group.append(button);
    div_row.append(div_col);

    // split
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    div_row.append(div_col);

    // reset-undo-redo button group
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    btn_group = document.createElement('div');
    btn_group.className = 'btn-group';
    div_col.append(btn_group);

    // reset
    button = document.createElement("button");
    button.id = "reset";
    img = $('img#x')[0].cloneNode(true);
    img.hidden = false;
    button.setAttribute('data-bs-toggle', 'tooltip');
    button.setAttribute('data-bs-placement', 'bottom');
    button.setAttribute('title', 'Reset edits');
    button.append(img);
    btn_group.append(button);

    // undo
    button = document.createElement("button");
    button.id = "undo";
    img = $('img#arrow-counterclockwise')[0].cloneNode(true);
    img.hidden = false;
    button.setAttribute('data-bs-toggle', 'tooltip');
    button.setAttribute('data-bs-placement', 'bottom');
    button.setAttribute('title', 'Undo edits');
    button.append(img);
    btn_group.append(button);

    // redo
    button = document.createElement("button");
    button.id = "redo";
    img = $('img#arrow-clockwise')[0].cloneNode(true);
    img.hidden = false;
    button.setAttribute('data-bs-toggle', 'tooltip');
    button.setAttribute('data-bs-placement', 'bottom');
    button.setAttribute('title', 'Redo edits');
    button.append(img);
    btn_group.append(button);
    div_row.append(div_col);

    // split
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    div_row.append(div_col);

    // input-group
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    let input_group = document.createElement('div');
    input_group.className = 'input-group';
    div_col.append(input_group);

    // do_input
    let input = document.createElement("input");
    input.type = "text";
    input.id = "row_select_input";
    input.className = "form-control form-control-sm";
    input_group.append(input);

    // do_select
    let select = document.createElement("select");
    select.id = "row_select_select";
    select.className = "form-select form-select-sm";
    let options = ["Go to sentence", "Add row", "Remove row"];
    for (let i = 0; i < options.length; i++) {
        let option = document.createElement("option");
        option.innerHTML = options[i];
        select.append(option);
    }
    input_group.append(select);

    // do_button
    button = document.createElement("button");
    button.id = "do";
    img = $('#check')[0].cloneNode(true);
    img.hidden = false;
    button.append(img);
    input_group.append(button);
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

    // errors
    div_col = document.createElement('div');
    div_col.className = 'col';
    button = document.createElement("button");
    button.id = "errors";
    button.setAttribute('data-bs-toggle', 'tooltip');
    button.setAttribute('data-bs-placement', 'bottom');
    if (window.error_condition == 1) {
        img = $('#exclamation-square-fill')[0].cloneNode(true);
        button.setAttribute('title', 'Hide errors');
    }
    else if (window.error_condition == 0) {
        img = $('#exclamation-square')[0].cloneNode(true);
        button.setAttribute('title', 'Show errors');
    }
    img.hidden = false;
    button.append(img);
    div_col.append(button);
    div_row.append(div_col);

    // split
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    div_row.append(div_col);

    // input-group
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    input_group = document.createElement('div');
    input_group.className = 'input-group';
    div_col.append(input_group);

    // graph_select
    select = document.createElement("select");
    select.id = "graph";
    select.className = "form-select form-select-sm";
    option = document.createElement("option");
    option.disabled = true;
    option.selected = true;
    option.innerHTML = "Graphs";
    select.append(option);
    options = [];
    let graph_keys = Object.keys(window.graph_d);
    for (let i = 0; i < graph_keys.length; i++) {
        options.push(window.graph_d[parseInt(graph_keys[i])]);
    }
    for (let i = 0; i < options.length; i++) {
        option = document.createElement("option");
        option.innerHTML = options[i];
        if (window.graph_preference == i) {
            option.style = "color: gray;";
        }
        else {
            option.style = "color: black;";
        }
        select.append(option);
    }
    input_group.append(select);

    // graph_button
    button = document.createElement("button");
    button.id = "graph";
    img = $('#check')[0].cloneNode(true);
    img.hidden = false;
    button.append(img);
    input_group.append(button);
    div_row.append(div_col);

    // split
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    div_row.append(div_col);

    // input-group
    div_col = document.createElement('div');
    div_col.className = 'col-md-auto';
    input_group = document.createElement('div');
    input_group.className = 'input-group';
    div_col.append(input_group);

    // column_select
    select = document.createElement("select");
    select.id = "col_add_rm_select";
    select.className = "form-select form-select-sm";
    // select.multiple = true;
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
        if (current_columns.includes(options[i].toLowerCase())) option.style = "color: gray;"; // not working in firefox
        else option.style = "color: black;";
        select.append(option);
    }
    input_group.append(select);

    // column_button
    button = document.createElement("button");
    button.id = "col_add_rm_button";
    img = $('#check')[0].cloneNode(true);
    img.hidden = false;
    button.append(img);
    input_group.append(button);
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
    img = $('#save')[0].cloneNode(true);
    img.hidden = false;
    button.setAttribute('data-bs-toggle', 'tooltip');
    button.setAttribute('data-bs-placement', 'bottom');
    button.setAttribute('title', 'Save edits');
    button.append(img);
    div_col.append(button);
    div_row.append(div_col);

    div_cont.append(div_row);
    $('div#buttons')[0].append(div_cont);

    let buttons = document.getElementsByTagName("button");
    for (let i = 0; i < buttons.length; i++) {
        buttons[i].addEventListener("click", function () {
            button_handle(buttons[i].id);
        });
        buttons[i].className = "btn btn-light btn-sm border";
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
    sentence_text.className = "table-sm mx-auto border border-secondary";
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
    let nav_table1 = $('nav#table1')[0];
    nav_table1.append(sentence_text);

    // Show table
    let word_lines = document.createElement("table");
    word_lines.id = "word_lines";
    word_lines.className = "table table-sm border border-secondary";
    let thead = document.createElement("thead");
    tbody = document.createElement("tbody");
    word_lines.append(thead);
    word_lines.append(tbody);
    let row = document.createElement("tr");
    for (let i = 0; i < current_columns.length; i++) {
        let heading = document.createElement("th");
        let column_t = current_columns[i].toLowerCase();
        if (cats_low.includes(column_t)) heading.innerHTML = cats[cats_low.indexOf(column_t)];
        else heading.innerHTML = features[features_low.indexOf(column_t)];
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
                let column = matches[1].toLowerCase();
                cells[cells_keys[i]][column] = matches[2];
            }
        }
        let row = document.createElement("tr");
        for (let j = 0; j < current_columns.length; j++) {
            let column_t = current_columns[j].toLowerCase();
            let row_t = cells_keys[i];
            let data = document.createElement("td");
            if (column_t == "id") data.innerHTML = row_t;
            else if (cells[row_t][column_t] == undefined) data.innerHTML = "_";
            else data.innerHTML = cells[row_t][column_t];
            data.id = `${row_t} ${column_t}`;
            if (column_t != "id") data.contentEditable = true;
            data.addEventListener("focus", (event) => {
                window.last_focus = [row_t, column_t];
                window.last_focus_value = event.target.innerHTML;
            });
            if (['aspect', 'case', 'evident', 'mood', 'number', 'number[psor]', 'numtype', 'person', 'person[psor]', 'polarity', 'prontype', 'tense', 'verbform', 'voice', 'upos', 'xpos', 'deprel'].includes(column_t)) {
                data.classList.add("autocomplete");
                data.classList.add(column_t);
            }
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
    $('div#table2')[0].append(word_lines);

    // autocomplete
    let autocomplete_d = { 'Aspect': ['Gen', 'Hab', 'Imp', 'Perf', 'Prog', 'Prosp'], 'Case': ['Abl', 'Acc', 'Dat', 'Equ', 'Gen', 'Ins', 'Nom', 'Loc', 'Voc'], 'Evident': ['Fh', 'Nfh'], 'Mood': ['Cnd', 'Des', 'Dur', 'Gen', 'Imp', 'Ind', 'Nec', 'Opt', 'Pot', 'Rapid'], 'Number': ['Sing', 'Plur'], 'Number[psor]': ['Sing', 'Plur'], 'NumType': ['Card', 'Dist', 'Frac', 'Ord'], 'Person': ['1', '2', '3'], 'Person[psor]': ['1', '2', '3'], 'Polarity': ['Pos', 'Neg'], 'PronType': ['Dem', 'Ind', 'Int', 'Loc', 'Prs', 'Rcp', 'Rfl', 'Quant'], 'Tense': ['Past', 'Pres', 'Fut'], 'VerbForm': ['Conv', 'Part', 'Vnoun'], 'Voice': ['Cau', 'Pass', 'Rcp', 'Rfl'], 'DEPREL': ['acl', 'advcl', 'advlc:cond', 'advmod', 'advmod:emph', 'amod', 'case', 'cc', 'cc:preconj', 'compound', 'compound:lvc', 'compound:redup', 'conj', 'cop', 'csubj', 'det', 'dep', 'dep:der', 'discourse', 'discourse:q', 'discourse:tag', 'flat', 'iobj', 'nmod', 'nmod:part', 'nmod:poss', 'nsubj', 'nummod', 'obl', 'obl:cl', 'obl:comp', 'obl:tmod', 'obj', 'punct', 'root', 'xcomp'], 'UPOS': ['ADJ', 'ADP', 'ADV', 'AUX', 'CCONJ', 'DET', 'INTJ', 'NOUN', 'NUM', 'PART', 'PRON', 'PROPN', 'PUNCT', 'VERB'], 'XPOS': ['Adj', 'ANum', 'Attr', 'Comma', 'Conv', 'Det', 'Demons', 'Exist', 'Indef', 'Inst', 'NNum', 'Noun', 'Partic', 'PCNom', 'PCDat', 'PCGen', 'Pers', 'Place', 'Ptcp', 'Punc', 'Reflex', 'Separ', 'Stop', 'Tdots', 'Topic', 'Typo', 'Ques', 'Quant', 'Verb', 'Vnoun', 'Year', 'Zero'] };
    let ac_keys = Object.keys(autocomplete_d);
    for (let i = 0; i < ac_keys.length; i++) {
        let source_t = autocomplete_d[ac_keys[i]];
        $(`.autocomplete.${ac_keys[i].toLowerCase()}`).autocomplete({ source: source_t });
    }

    create_graph();
    display_errors();
}

function create_graph() {
    $('div#graph').empty();
    let div_graph = $('div#graph')[0];
    if (window.graph_preference == 0) return;
    else if (window.graph_preference == 1) {
        $('#vis').remove();
        $('#dep_graph').remove();
        let cells = window.cells;
        let vis = document.createElement('div');
        vis.id = "vis";
        let dep_graph = document.createElement('div');
        dep_graph.className = "conllu-parse";
        dep_graph.setAttribute('data-inputid', 'input');
        dep_graph.setAttribute('data-parsedid', 'parsed');
        dep_graph.setAttribute('data-logid', 'log');
        let order = ['form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps']; // id & misc removed
        let cells_keys = get_sorted_cells_keys();
        for (let i = 0; i < cells_keys.length; i++) {
            let key = cells_keys[i];
            dep_graph.innerHTML += key + "\t";
            for (let j = 0; j < 8; j++) {
                dep_graph.innerHTML += cells[key][order[j]] + "\t";
            }
            dep_graph.innerHTML += cells[key]["misc"] + "\n"; // misc
        }
        div_graph.append(vis);
        div_graph.append(dep_graph);
        Annodoc.activate(Config.bratCollData, {});
        $('#embedded-1-sh').remove();
    }
    else if (window.graph_preference == 2) {
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
                div_graph.append(graph);
                $("#ud_graph").after($("#error_div"));
            });
    }
    else if (window.graph_preference == 3) {
        $.post("/spacy/",
            {
                cells: JSON.stringify(window.cells)
            },
            function (data) {
                let textarea_t = document.createElement('textarea');
                textarea_t.innerHTML = data;
                let graph = document.createElement('div');
                graph.innerHTML = textarea_t.value;
                div_graph.append(graph);
            });
    }
}

function display_errors() {
    if (window.error_condition == 0) return;

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
    error_div.className = "card bg-light mb-3";
    error_div.style = "max-width: 100rem;";
    let error_header = document.createElement('div');
    error_div.append(error_header);
    error_header.id = "error_header";
    error_header.className = "card-header";
    error_header.innerHTML = 'Errors';
    let error_body = document.createElement('div');
    error_body.id = "error_body";
    error_body.className = "card-body";
    error_div.append(error_body);
    let errors = window.errors.split('\n');
    if (errors[0] == "*** PASSED ***") {
        error_div.classList.add("border-success");
        error_header.classList.add("border-success");
    }
    else {
        error_div.classList.add("border-danger");
        error_header.classList.add("border-danger");
    }
    for (let i = 0; i < errors.length; i++) {
        error_body.innerHTML += errors[i];
        error_body.append(document.createElement('br'));
    }
    $('div#error')[0].append(error_div);
}

function cell_change(key, column, cell) {

    cell = cell.replace('<br>', '');
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
