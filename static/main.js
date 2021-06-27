async function addOldLinesToConsole(mode) {
    mode = mode || "out";
    const response = await fetch(`/logs.txt?mode=${mode}`);
    const text = await response.text();
    const element = document.createElement("span");
    element.textContent = text+"\n"
    if (mode==="error") {
        element.style.color = "#ff3f3f";
    }
    else if (mode==="out") {
        element.style.color = "#11c201";
    };
    document.querySelector("code").appendChild(element);
    return true;
};


function reboot() {
    for(let i=0;i++;i<5) {
        if(!confirm(`Are you sure you want to reboot the bot? (prompt ${i}/5)`)) {
            createEvent("Cancelled reboot.", "info");
            return;
        }
    }
    createEvent("Rebooting bot...", "pending");
    fetch(
        "/reboot",
        {
            method: "POST"
        }
    ).then(
        (response) => {
            if(!response.ok) {
                createEvent(`Reboot failed. Status ${response.status} ${response.statusText}.`, "bad");
            }
            else {
                createEvent("Reboot succeeded. It may take a few moments to take effect.", "good");
            }
        }
    ).catch((e) => {createEvent("Reboot failed. Check your network.", "bad");console.error(e)})
}


function reload() {
    var cogs = prompt("Cogs to reload (separated by space):");
    if(cogs === null) {
        createEvent("Cancelled reloading cogs (none provided).", "info")
        return alert("No cogs provided to reload. No action taken.");
    }
    else {
        cogs = cogs.split(" ");
    }
    if(!confirm(`Are you sure you would like to (re)load ${cogs.length} cogs?`)) {
        alert("Action was cancelled.");
    };
    
    createEvent("Reloading cogs: " + JSON.stringify(cogs), "pending");
    fetch(
        "/reload-cogs",
        {
            body: {'cogs': JSON.stringify(cogs)},
            method: "POST"
        }
    )
    .then(
        (response) => {
            if(response.status === 200) {
                createEvent("Reloaded cogs.", "good");
            }
            else {
                createEvent(`Failed to reload cogs. Got HTTP ${response.status} ${response.statusText}.`, "bad");
            };
        }
    )
    .catch((e)=>{createEvent(`Failed to reload cogs due to browser error. Check your network.`, "bad");console.error(e)})
};


function createEvent(content, mode) {
    mode = mode || "info"
    if(!["good", "pending", "bad", "info"].includes(mode)) {
        throw new TypeError("Invalid type " + mode);
    };

    const parentBox = document.createElement("div");
    parentBox.classList.add("event");
    parentBox.classList.add("event-"+mode);
    parentBox.textContent = `[${new Date().toString()}] ` + content;
    const log = document.querySelector("#event-log");
    if(!log) {
        document.body.appendChild(parentBox);
    }
    else {
        log.prepend(parentBox)
    }
};


window.onload = function () {
    createEvent("Webpage loaded");
    createEvent("Loading stdout...", "pending");
    addOldLinesToConsole("out").then(
        () => {createEvent("Loaded stdout.", "good")}
    ).catch((e) => {createEvent("Failed to load stdout.", "bad");console.error(e);});
    createEvent("Loading stderr...", "pending");
    addOldLinesToConsole("error").then(
        () => {createEvent("Loaded stderr", "good")}
    ).catch((e) => {createEvent("Failed to load stderr.", "bad");console.error(e);});
    const functions = {
        "reboot": reboot,
        "reload": reload
    };
    for(let f of Object.keys(functions)) {
        document.getElementById(f).addEventListener(
            "click",
            functions[f]
        );
    };
    createEvent("Init finished.", "good");
};
