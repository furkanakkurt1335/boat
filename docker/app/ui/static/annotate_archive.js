
heading.addEventListener("click", function () {
    column_click(heading.innerHTML.toLowerCase());
});

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
