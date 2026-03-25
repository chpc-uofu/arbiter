window.addEventListener("load", function () {
    const tiers_container = document.getElementById("tiers-content");
    const add_tier_button = document.getElementById("add-tier-button");
    const constraints_input = document.getElementById("penalty-constraints-input");
    const form = document.getElementById("change-form");
    const message_list = document.getElementById("penalty-messages");

    function update_message(message, status){
        message_list.innerHTML += `<li class="${status}">${message}</li>`;
    }

    function update_row_nums(){
        var num_rows = 1
        var row_labels = document.querySelectorAll(".row-number")
        
        for (var row_label of row_labels){
            row_label.innerHTML = num_rows;
            num_rows++;
        }
    }

    function update_tiers_input(event) {
        const rows = tiers_container.querySelectorAll("tr");
        var serialized_tiers = [];
        
        if (rows.length == 0){
            event.preventDefault();
            update_message("At least one tier must be set", "error")
        }

        for (const row of rows){
            const cpu_quota = parseFloat(row.querySelector("td.cpu-constraint-cell").textContent.trim());
            const memory_max = parseFloat(row.querySelector("td.memory-constraint-cell").textContent.trim());

            if (isNaN(memory_max) && isNaN(cpu_quota)){
                event.preventDefault();
                update_message("At least one limit must be set per tier, and limits must be blank or valid numbers", "error");
                return;
            }

            serialized_tiers.push({"cpu_quota": blank_if_nan(cpu_quota), "memory_max": blank_if_nan(memory_max)});
        }

        var serialized_constraints = {"tiers": serialized_tiers};
        constraints_input.value = JSON.stringify(serialized_constraints);
    }

    function blank_if_nan(num){
        if (isNaN(num))
            return "";
        else
            return num;
    }


    function add_tier(event) {
        event.preventDefault();

        const row_num = tiers_container.children.length + 1;
        const cpu_quota = parseFloat(document.getElementById('cpu-quota-input').value);
        const memory_max = parseFloat(document.getElementById('memory-max-input').value);

        if (isNaN(memory_max) && isNaN(cpu_quota)){
            update_message("At least one limit must be set per tier, and limits must be blank or valid numbers", "error")
            return
        }

        tiers_container.innerHTML += 
            `<td class="row-number">${row_num}</td>
            <td contenteditable="true" class="cpu-constraint-cell"> ${blank_if_nan(cpu_quota)}</td>
            <td contenteditable="true"  class="memory-constraint-cell">${blank_if_nan(memory_max)}</td>
            <td><button class="table-action remove-tier-buttton">Remove</button></td>`;
    }

    function bodyclicked(event) {
        event.preventDefault();

        if (event.target && event.target.classList.contains("remove-tier-buttton")) {
            const row = event.target.parentElement.parentElement;
            if (row){
                row.remove();
                update_row_nums()
            }
        }
    }


    form.addEventListener('submit', update_tiers_input);
    add_tier_button.addEventListener('click', add_tier);
    tiers_container.addEventListener('click', bodyclicked);

    update_tiers_input();
})