function remove_tier(event) {
    event.preventDefault();

    event.target.parentElement.remove();

    var row_labels = document.querySelectorAll("row-number");
    var row_num = 1;
    for (var row_label of row_labels){
        row_label.value = row_num;
        row_num++;
    }
}

window.addEventListener("load", function () {
    const tiers_container = document.getElementById("tiers-content");
    const add_tier_button = document.getElementById("add-tier-button");
    const constraints_input = document.getElementById("penalty-constraints-input");
    const form = document.getElementById("change-form");


    function update_tiers_input() {
        const rows = tiers_container.querySelectorAll("tr");
        var serialized_tiers = [];
        
        for (const row of rows){
            const cpu_quota = row.querySelector("td.cpu-constraint-cell").textContent.trim();
            const memory_max = row.querySelector("td.memory-constraint-cell").textContent.trim();
            serialized_tiers.push({"cpu_quota": parseFloat(cpu_quota), "memory_max": parseFloat(memory_max)});
        }

        var serialized_constraints = {"tiers": serialized_tiers};
        constraints_input.value = JSON.stringify(serialized_constraints);
    }

    

    function add_tier(event) {
        event.preventDefault();

        const row_num = tiers_container.children.length + 1;
        const cpu_quota = parseFloat(document.getElementById('cpu-quota-input').value);
        const memory_max = parseFloat(document.getElementById('memory-max-input').value);

        tiers_container.innerHTML += 
            `<td class="row-number">`+row_num+`</td>
            <td contenteditable="true" class="cpu-constraint-cell">` + cpu_quota + `</td>
            <td contenteditable="true"  class="memory-constraint-cell">` + memory_max + `</td>
            <td ><button class="table-action remove-buttton" onclick="remove_tier" type="submit">Remove</button></td>`;
    }


    form.addEventListener('submit', (event) => {
        update_tiers_input();
    });

    add_tier_button.addEventListener('click', add_tier);

    update_tiers_input();
})