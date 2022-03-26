// TODO: don't remove table, adjust

var current_columns = [];

// On document load
window.onload = function() {
    // document.getElementById("bootstrap_js").remove();
    // document.getElementById("bootstrap_css").remove();
    window.sent_id = document.getElementById('sentence.sent_id').innerHTML;
    window.text = document.getElementById('sentence.text').innerHTML;
    window.cells = JSON.parse(document.getElementById('annotation.cats').innerHTML);
    window.notes = document.getElementById('annotation.notes').innerHTML;
    window.errors = document.getElementById('errors').innerHTML;
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
    const form = document.createElement('form');
    form.method = "post";
    form.action = `${get_sentence_id_url()}`;
    form.enctype = "multipart/form-data";
    const csrf_token_input = document.getElementsByName('csrfmiddlewaretoken')[0];
    form.append(csrf_token_input);

    // Type
    const form_type = document.createElement('input');
    form_type.type = 'hidden';
    form_type.name = "type";
    form_type.value = type;
    form.append(form_type);
    if (type == "go") {
        const form_type = document.createElement('input');
        form_type.type = 'hidden';
        form_type.name = "number";
        form_type.value = parseInt(number);
        form.append(form_type);
    }

    // Cells
    const form_data = document.createElement('input');
    form_data.type = 'hidden';
    form_data.name = "data";
    form_data.value = JSON.stringify(window.cells);
    form.append(form_data);
    document.body.append(form);

    // Notes
    const form_notes = document.createElement('input');
    form_notes.type = 'hidden';
    form_notes.name = "notes";
    form_notes.value = window.notes;
    form.append(form_notes);
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
    for (let i = 1; i < cells_keys.length*2; i++) {
        if (cells_keys.indexOf(`${i}-${i+1}`) != -1) new_list.push(`${i}-${i+1}`);
        if (cells_keys.indexOf(`${i}`) != -1) new_list.push(`${i}`);
    }
    return new_list;
}

function button_handle(type, number, way) {
    if (["previous", "next", "save"].indexOf(type) != -1) {
        post_to_save(type);
    }
    else if (type == "col_add_rm_button") {
        let sel = document.getElementById("col_add_rm_select");
        if (sel.selectedIndex != 0) column_change(sel.options[sel.selectedIndex].text);
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

            }
            else {}
            // TODO
            let cells_keys = get_sorted_cells_keys();
            if (cells_keys.indexOf(input_number) == -1) return;
            let row_place = cells_keys.indexOf(input_number);
            if (selected == "Add row") {
                input_number = parseInt(input_number);
                if (input_number == NaN) return;
                let new_row = `${input_number}-${input_number+1}`;
                window.cells[new_row] = window.cells[cells_keys[row_place]];
                window.cells[(parseInt(cells_keys[cells_keys.length-1])+1).toString()] = window.cells[cells_keys[cells_keys.length-1]];
                for (let i = cells_keys.length-1; i > row_place; i--) {
                    if (cells_keys[i].indexOf('-') != -1) {
                        let matches = cells_keys[i].match(/(\d+)-(\d+)/);
                        let n1 = matches[1];
                        window.cells[`${n1+1}-${n1+2}`] = window.cells[cells_keys[i]];
                    }
                    else window.cells[cells_keys[i]] = window.cells[cells_keys[i-1]];
                }
            }
            else if (selected == "Remove row") {
                for (let i = row_place; i < cells_keys.length-1; i++) {
                    window.cells[cells_keys[i]] = window.cells[cells_keys[i+1]];
                }
                delete window.cells[cells_keys[cells_keys.length-1]];
            }
            inject_sentence();
        }
    }
    else if (type == "undo") {
        if (window.edits.length == 0) return;
        let last_edit = window.edits.pop();
        let undone_pair = [last_edit[0], window.cells[last_edit[0][0]][last_edit[0][1].toLowerCase()]];
        window.edits_undone.push(undone_pair);
        window.cells[last_edit[0][0]][last_edit[0][1].toLowerCase()] = last_edit[1];
        inject_sentence();
    }
    else if (type == "redo") {
        if (window.edits_undone.length == 0) return;
        let last_edit_undone = window.edits_undone.pop();
        let redone_pair = [last_edit_undone[0], window.cells[last_edit_undone[0][0]][last_edit_undone[0][1].toLowerCase()]];
        window.edits.push(redone_pair);
        window.cells[last_edit_undone[0][0]][last_edit_undone[0][1].toLowerCase()] = last_edit_undone[1];
        inject_sentence();
    }
    else if (type == "reset") {
        window.cells = window.initial_cells;
        inject_sentence();
    }
}

// Keyboard shortcuts
document.onkeyup = function(e) {
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
        let act_el_id = document.activeElement.id;
        let matches = act_el_id.match(/row:(\d*), column:(\d*)/);
        if (matches.length == 3) {
            let row = parseInt(matches[1]);
            let column = parseInt(matches[2]);

            let form_count = document.getElementById("word_lines").getElementsByTagName("tr").length-1;
            if (e.key == "ArrowUp" && row != 0) {
                document.getElementById(`row:${row-1}, column:${column}`).focus();
            }
            else if (e.key == "ArrowDown" && row != form_count-1) {
                document.getElementById(`row:${row+1}, column:${column}`).focus();
            }
            else if (e.key == "ArrowRight" && column != current_columns.length-1) {
                document.getElementById(`row:${row}, column:${column+1}`).focus();
            }
            else if (e.key == "ArrowLeft" && column != 0) {
                document.getElementById(`row:${row}, column:${column-1}`).focus();
            }
        }
    }
    else if (e.shiftKey && e.altKey) {
        if (e.key == "ArrowUp") {
            button_handle('')
        }
        else if (e.key == "ArrowDown") {
            console.log('down');
        }
    }
};

function column_change(column_option) {
    if (current_columns.includes(column_option)) current_columns.splice(current_columns.indexOf(column_option), 1);
    else current_columns = current_columns.concat(column_option);
    sort_columns();
    inject_sentence();
}

function sort_columns() {
    for (let i = 0; i < cats.length; i++) {
        let cat_t = cats[i];
        if (current_columns.includes(cat_t)) {
            current_columns.splice(current_columns.indexOf(cat_t), 1);
            current_columns = current_columns.concat(cat_t);
        }
    }
    for (let i = 0; i < features.length; i++) {
        let feat_t = features[i];
        if (current_columns.includes(feat_t)) {
            current_columns.splice(current_columns.indexOf(feat_t), 1);
            current_columns = current_columns.concat(feat_t);
        }
    }
}

function init_page() {

    var element_splitter = document.createElement("span");
    element_splitter.innerHTML = "&nbsp;&nbsp;";
    element_splitter.style = "font-size: large; margin-left: 5px; margin-right: 5px";

    const div_row = document.createElement('div');
    div_row.className = 'row mx-auto';
    const div_col = document.createElement('div');
    div_col.className = 'col';
    div_row.append(div_col);
    document.body.append(div_row);

    const previous_button = document.createElement("button");
    previous_button.id = "previous";
    previous_button.innerHTML = "Previous";
    div_col.append(previous_button);

    div_col.append(element_splitter.cloneNode(true));

    const reset_button = document.createElement("button");
    reset_button.id = "reset";
    reset_button.innerHTML = "Reset";
    div_col.append(reset_button);

    const undo_button = document.createElement("button");
    undo_button.id = "undo";
    undo_button.innerHTML = "Undo";
    div_col.append(undo_button);

    const redo_button = document.createElement("button");
    redo_button.id = "redo";
    redo_button.innerHTML = "Redo";
    div_col.append(redo_button);

    div_col.append(element_splitter.cloneNode(true));

    const row_select_input = document.createElement("input");
    row_select_input.type = "number";
    row_select_input.id = "row_select_input";
    div_col.append(row_select_input);

    const row_select_select = document.createElement("select");
    row_select_select.id = "row_select_select";
    var row_select_options = ["Go to sentence", "Add row", "Remove row"];
    for (let i = 0; i < row_select_options.length; i++) {
        var row_select_option = document.createElement("option");
        row_select_option.innerHTML = row_select_options[i];
        row_select_select.append(row_select_option);
    }
    div_col.append(row_select_select);

    const do_button = document.createElement("button");
    do_button.id = "do";
    do_button.innerHTML = "Do";
    div_col.append(do_button);

    div_col.append(element_splitter.cloneNode(true));

    const col_add_rm_select = document.createElement("select");
    col_add_rm_select.id = "col_add_rm_select";
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
    div_col.append(col_add_rm_select);

    row_select_input.style = "margin: 5px";
    row_select_select.style = "margin: 5px";
    col_add_rm_select.style = "margin: 5px";

    const col_add_rm_button = document.createElement("button");
    col_add_rm_button.id = "col_add_rm_button";
    col_add_rm_button.innerHTML = "Add / Remove column selected";
    div_col.append(col_add_rm_button);

    div_col.append(element_splitter.cloneNode(true));

    const next_button = document.createElement("button");
    next_button.id = "next";
    next_button.innerHTML = "Next";
    div_col.append(next_button);

    div_col.append(element_splitter.cloneNode(true));

    const save_button = document.createElement("button");
    save_button.id = "save";
    save_button.innerHTML = "Save";
    div_col.append(save_button);

    const buttons = document.getElementsByTagName("button");
    for (let i = 0; i < buttons.length; i++) {
        buttons[i].addEventListener("click", function() {
            button_handle(buttons[i].id);
        });
        buttons[i].style = "margin: 5px";
        buttons[i].className = "btn btn-secondary";
    }

    current_columns = ["ID", "FORM", "LEMMA", "UPOS", "XPOS", "FEATS", "HEAD", "DEPREL", "DEPS", "MISC"];
    inject_sentence();
}

var cats = ["ID", "FORM", "LEMMA", "UPOS", "XPOS", "FEATS", "HEAD", "DEPREL", "DEPS", "MISC"];
var features = ["Abbr", "Animacy", "Aspect", "Case", "Clusivity", "Definite", "Degree", "Evident", "Foreign", "Gender", "Mood", "NounClass", "Number", "NumType", "Person", "Polarity", "Polite", "Poss", "PronType", "Reflex", "Tense", "Typo", "VerbForm", "Voice"];
const all_column_count = cats.length + features.length;

function inject_sentence() {
    $('br').remove();
    $('#sentence_text').remove();
    $('#word_lines').remove();
    let cells = window.cells;

    // Show sentence in table form with indices
    let sentence_text = document.createElement("table");
    sentence_text.id = "sentence_text";
    sentence_text.className = "table-xs table-borderless table-sm mx-auto";
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
        data.style.textAlign = "center";
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
    row = document.createElement("tr");
    for (let i = 0; i < current_columns.length; i++) {
        let heading = document.createElement("th");
        heading.innerHTML = current_columns[i];
        heading.style = 'text-align:center';
        heading.addEventListener("click", function() {
            column_click(heading.innerHTML);
        });
        row.append(heading);
    }
    thead.append(row);

    for (let i = 0; i < form_count; i++) {
        let feats = cells[cells_keys[i]]['feats'].split('|');
        for (let j = 0; j < feats.length; j++) {
            let matches = feats[j].match(/(.+)=(.+)/);
            cells[cells_keys[i]][matches[1].toLowerCase()] = matches[2];
        }
        let row = document.createElement("tr");
        for (let j = 0; j < current_columns.length; j++) {
            let data = document.createElement("td");
            if (current_columns[j].toLowerCase() == "id") data.innerHTML = cells_keys[i];
            else if (cells[cells_keys[i]][current_columns[j].toLowerCase()] == undefined) data.innerHTML = "_";
            else data.innerHTML = cells[cells_keys[i]][current_columns[j].toLowerCase()];
            data.id = `row:${i}, column:${j}`;
            data.style.textAlign = "center";
            data.contentEditable = "true";
            data.addEventListener("focus", (event) => {
                window.last_focus = [cells_keys[i], current_columns[j]];
                window.last_focus_value = event.target.innerHTML;
            });
            data.addEventListener("blur", (event) => { // potential problem with unfocusing after column removal!
                if (window.last_focus_value != event.target.innerHTML) {
                    cell_change(i, j, event.target.innerHTML);
                    window.edits.push([window.last_focus, window.last_focus_value]);
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
    let cells = window.cells;
    let pre = document.getElementById("dep_graph");
    pre.innerHTML = "";
    let order = ['form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps'] // id & misc removed
    let cells_keys = get_sorted_cells_keys();
    for (let i = 0; i < cells_keys.length; i++) {
        let key = cells_keys[i];
        pre.innerHTML += key + "\t";
        for (let j = 0; j < 8; j++) {
            pre.innerHTML += cells[key][order[j]] + "\t";
        }
        pre.innerHTML += cells[key]["misc"] + "\n"; // misc
    }
    document.body.append(document.getElementById('vis'));
    document.body.append(document.getElementById('dep_graph'));
    Annodoc.activate(Config.bratCollData, {});
}

function display_errors() {
    $('#error_div').remove();
    $('#error_header').remove();
    $('#error_body').remove();
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
}

function cell_change(key, column, cell) {
    let cells_keys = get_sorted_cells_keys();
    let curr_col = current_columns[column].toLowerCase();
    if (curr_col == "id") window.cells[cell] = window.cells[key];
    else if (curr_col == "feats") {
        window.cells[cells_keys[key]]['feats'] = cell;
        let feats = cell.split('|');
        for (let j = 0; j < feats.length; j++) {
            let matches = feats[j].match(/(.+)=(.+)/);
            cells[cells_keys[key]][matches[1].toLowerCase()] = matches[2];
            if (current_columns.indexOf(matches[1]) != -1) {
                let col_t = current_columns.indexOf(matches[1]);
                document.getElementById(`row:${key}, column:${col_t}`).innerHTML = matches[2];
            }
        }
    }
    else window.cells[cells_keys[key]][curr_col] = cell;
}

function column_click(column_name) {
    var arr_t = [];
    let index_remove = current_columns.indexOf(column_name);
    for (let i = 0; i < current_columns.length; i++) {
        if (i != index_remove) arr_t = arr_t.concat(current_columns[i]);
    }
    current_columns = arr_t;
    inject_sentence();
}
