const SPECIALS = ["Define", "Help", "Info", "List", "Trust", "Save", "Load"]
const TABLES = ["Symbol", "Function", "Delete"]

let queue = []
let record = ""
let waiting = ""

const socket = new WebSocket(`ws://${window.location.hostname}:8001`)

function setup(inputHandler, outputHandler) {
    function doQueue() {
        if (waiting !== "") {
            console.error(`doQueue called with non empty waiting: ${waiting}`)
            return
        }
        if (queue.length) {
            waiting = queue.shift().trim()
            if (waiting === "") {
                console.error(`queue contained empty value`)
                return
            }
            if (waiting.startsWith("NoRecord ")) {
                waiting = waiting.replace("NoRecord ", "")
            } else {
                record += waiting + "\n"
            }
            if (waiting.startsWith("System ")) {
                socket.send(waiting.replace("System ", ""))
            } else {
                inputHandler(waiting)
                socket.send(waiting)
            }
        }
    }

    socket.addEventListener('message', function (event) {
        if (waiting.startsWith("System ") || event.data === "Ok") {
            waiting = ""
            doQueue()
            return
        }
        outputHandler(waiting, event.data)
        waiting = ""
        doQueue()
    })

    return doQueue
}
