const output = document.getElementById("output")
const input = document.getElementById("input")
const N = document.getElementById("N")
const pretty = document.getElementById("pretty")
const deg = document.getElementById("deg")
const table = document.getElementById("table")

pretty.checked = false
N.checked = false
deg.checked = true

function changeTable(symbol, value, del) {
    for (let i = 0; i < table.childNodes.length; i++) {
        let child = table.childNodes[i]
        if (child.tagName?.toUpperCase() === "TR" && child.firstChild.firstChild.innerText === symbol) {
            table.removeChild(child)
            break
        }
    }
    if (!del) {
        const tr = document.createElement("tr")
        let td = document.createElement("td")
        let pre = document.createElement("pre")
        pre.innerText = symbol
        td.appendChild(pre)
        tr.appendChild(td)
        td = document.createElement("td")
        pre = document.createElement("pre")
        pre.innerText = value
        td.appendChild(pre)
        tr.appendChild(td)
        table.appendChild(tr)
    }
}

function inputHandler(text) {
    const op = text.split(" ")[0]

    if (TABLES.indexOf(op) != -1) {
        text.split(" ").slice(1).forEach(value => {
            if (value.trim() !== "") {
                changeTable(value, op != "Delete" ? op : "", op == "Delete")
            }
        })
    }

    if (op === "Save") {
        output.innerHTML += `Input: ${"Save " + text.split(" ")[1]}\n`
    } else {
        output.innerHTML += `Input: ${text}\n`
    }

    output.scrollTop = 99999
    output.scrollLeft = -99999
}

function outputHandler(waiting, data) {
    if (data.startsWith("Err: ")) {
        output.innerHTML += `${data.replace("Err: ", "Error: ")}\n\n`
    } else if (waiting.startsWith("Define ")) {
        changeTable(waiting.split(" ")[1], data, false)
    } else if (waiting.startsWith("Load ")) {
        data.split("\n").forEach(line => {
            if (line.trim() != "") {
                queue.push("NoRecord " + line)
            }
        })
    } else {
        output.innerHTML += `${waiting === "" ? "Unexpected: " : ""}Output:${data.indexOf("\n") !== -1 ? "\n" : " "}${data}\n\n`
    }
    output.scrollTop = 99999
    output.scrollLeft = -99999
}

const doQueue = setup(inputHandler, outputHandler)

function changeDeg() {
    if (deg.checked) {
        queue.push("System Define sin Lambda(x, sin(rad(x)))")
        queue.push("System Define cos Lambda(x, cos(rad(x)))")
        queue.push("System Define tan Lambda(x, tan(rad(x)))")
        queue.push("System Define asin Lambda(x, deg(asin(x)))")
        queue.push("System Define acos Lambda(x, deg(acos(x)))")
        queue.push("System Define atan Lambda(x, deg(atan(x)))")
    } else {
        queue.push("System Delete sin")
        queue.push("System Delete cos")
        queue.push("System Delete tan")
        queue.push("System Delete asin")
        queue.push("System Delete acos")
        queue.push("System Delete atan")
    }
    doQueue()
}

socket.onopen = changeDeg

function changePretty() {
    if (pretty.checked) {
        queue.push("System pretty")
    } else {
        queue.push("System nopretty")
    }
    doQueue()
}

function press() {
    if (input.value.trim() === "") {
        return
    }

    const op = input.value.split(" ")[0]
    let special = false

    if (SPECIALS.indexOf(op) != -1 || TABLES.indexOf(op) != -1 || op == "NoRecord") {
        special = true
    }

    if (op == "Save") {
        let command = "Save " + input.value.split(" ")[1].trim()
        // Prevents accidentally saving the file as "System" (the first command always executed)
        if (command == "Save" || command == "Save undefined") {
            return
        }
        command += " " + record
        queue.push("NoRecord " + command)
    } else {
        if (N.checked && !special) {
            queue.push(`N(${input.value})`)
        } else {
            queue.push(input.value)
        }
    }

    input.value = ""
    doQueue()
}

input.addEventListener("keyup", function (event) {
    if (event.key === "Enter") {
        press()
    }
});
