function test_func() {
    alert("test_func");
}

function getGanttChartData() {
    return fetch(`data/`)
        .then(response => response.json())
        .then(data => {
            return data.results;
        })
        .catch(err => console.error(err));
}

function createGanttChart(tasks) {
    var gantt_chart = new Gantt(
        "#gantt",
        tasks,
        {
            language: "ru",
        },
    );

    gantt_chart.render();

    document.querySelector(".chart-controls #day-btn").addEventListener("click", () => {
        gantt_chart.change_view_mode("Day");
    })

    document.querySelector(".chart-controls #week-btn").addEventListener("click", () => {
        gantt_chart.change_view_mode("Week");
    })

    document.querySelector(".chart-controls #month-btn").addEventListener("click", () => {
        gantt_chart.change_view_mode("Month");
    })

    // document.querySelector(".chart-controls #year-btn").addEventListener("click", () => {
    //     gantt_chart.change_view_mode("Year");
    // })
}

function getCurrentProjectVersion() {
    const projectVersion = document.getElementById("project-version");
    console.log(`projectVersion`, projectVersion, projectVersion.dataset.currnent);
    return projectVersion.dataset.currnent;
}

function longPollVersion(projectVersion, buttonId, interval = 5) {
    const _button = document.getElementById(buttonId);
    fetch(`version`)
        .then((response) => response.json())
        .then((data) => {
            console.log(`backend version, currnent version`, data["version"], projectVersion);
            if (_button !== null) {
                if (data["version"] !== projectVersion) {
                    _button.disabled = false; // делаем кнопку активной
                }
                else if (_button !== null) {
                    _button.disabled = true; // делаем кнопку неактивной
                }
            }
            else {
                console.log(`Button not found ${buttonId}`);
            }
            setTimeout(() => longPollVersion(projectVersion, buttonId, interval), interval * 1000);
        })
        .catch((error) => {
            console.error(`Failed to fetch data: ${error}`);
            setTimeout(() => longPollVersion(projectVersion, buttonId, interval), interval * 1000);
        });
}