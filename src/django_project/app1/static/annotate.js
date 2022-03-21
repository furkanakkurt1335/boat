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
    let cells_keys = Object.keys(window.cells).sort();
    for (let i = 0; i < cells_keys.length; i++) {
        if (cells_keys[i].indexOf('-') != -1) {
            let temp = cells_keys[i];
            cells_keys[i] = cells_keys[i-1];
            cells_keys[i-1] = temp;
        }
    }
    return cells_keys;
}

function button_handle(type) {
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
        document.getElementById("table").focus();
    }
    else if ((e.key == "ArrowUp" || e.key == "ArrowDown" || e.key == "ArrowLeft" || e.key == "ArrowRight") && e.ctrlKey) {
        let act_el_id = document.activeElement.id;
        let matches = act_el_id.match(/row:(\d*), column:(\d*)/);
        if (matches.length == 3) {
            let row = parseInt(matches[1]);
            let column = parseInt(matches[2]);

            let form_count = document.getElementById("table").getElementsByTagName("tr").length-1;
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
    element_splitter.innerHTML = "|";
    element_splitter.style = "font-size: large; margin-left: 5px; margin-right: 5px";

    const previous_button = document.createElement("button");
    previous_button.id = "previous";
    previous_button.innerHTML = "Previous";
    document.body.append(previous_button);

    document.body.append(element_splitter.cloneNode(true));

    const reset_button = document.createElement("button");
    reset_button.id = "reset";
    reset_button.innerHTML = "Reset";
    document.body.append(reset_button);

    const undo_button = document.createElement("button");
    undo_button.id = "undo";
    undo_button.innerHTML = "Undo";
    document.body.append(undo_button);

    const redo_button = document.createElement("button");
    redo_button.id = "redo";
    redo_button.innerHTML = "Redo";
    document.body.append(redo_button);

    document.body.append(element_splitter.cloneNode(true));

    const row_select_input = document.createElement("input");
    row_select_input.type = "number";
    row_select_input.id = "row_select_input";
    document.body.append(row_select_input);

    const row_select_select = document.createElement("select");
    row_select_select.id = "row_select_select";
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

    document.body.append(element_splitter.cloneNode(true));

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
    document.body.append(col_add_rm_select);

    row_select_input.style = "margin: 5px";
    row_select_select.style = "margin: 5px";
    col_add_rm_select.style = "margin: 5px";

    const col_add_rm_button = document.createElement("button");
    col_add_rm_button.id = "col_add_rm_button";
    col_add_rm_button.innerHTML = "Add / Remove column selected";
    document.body.append(col_add_rm_button);

    document.body.append(element_splitter.cloneNode(true));

    const next_button = document.createElement("button");
    next_button.id = "next";
    next_button.innerHTML = "Next";
    document.body.append(next_button);

    document.body.append(element_splitter.cloneNode(true));

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
    document.body.append(br.cloneNode(true));

    const p_text = document.createElement("p");
    p_text.id = "sentence_text";
    document.body.append(p_text);
    document.body.append(br);

    const table = document.createElement("table");
    table.id = "sentence_table";
    document.body.append(table);

    current_columns = ["ID", "FORM", "LEMMA", "UPOS", "XPOS", "FEATS", "HEAD", "DEPREL", "DEPS", "MISC"];
    inject_sentence();
}

var cats = ["ID", "FORM", "LEMMA", "UPOS", "XPOS", "FEATS", "HEAD", "DEPREL", "DEPS", "MISC"];
var features = ["Abbr", "Animacy", "Aspect", "Case", "Clusivity", "Definite", "Degree", "Evident", "Foreign", "Gender", "Mood", "NounClass", "Number", "NumType", "Person", "Polarity", "Polite", "Poss", "PronType", "Reflex", "Tense", "Typo", "VerbForm", "Voice"];
const all_column_count = cats.length + features.length;

function inject_sentence() {
    let cells = window.cells;
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
    let form_count = Object.keys(cells).length;
    let cells_keys = get_sorted_cells_keys();
    for (let i = 0; i < form_count; i++) {
        let heading = document.createElement("th");
        heading.innerHTML = cells_keys[i];
        heading.style.textAlign = "center";
        row.append(heading);
    }
    thead.append(row);
    row = document.createElement("tr");
    for (let i = 0; i < form_count; i++) {
        let data = document.createElement("td");
        data.innerHTML = cells[cells_keys[i]]["form"];
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
    document.body.append(table);
}

function cell_change(form, column, cell) {
    let cells_keys = get_sorted_cells_keys();
    cells[cells_keys[form]][current_columns[column].toLowerCase()] = cell;
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
