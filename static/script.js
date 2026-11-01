async function sendMessage() {

    const input = document.getElementById("question");
    const chatBox = document.getElementById("chat-box");

    const message = input.value.trim();

    if (!message) {
        return;
    }

    // Show user message
    chatBox.innerHTML += `
        <div class="message user">
            ${message}
        </div>
    `;

    input.value = "";

    // Scroll to latest message
    chatBox.scrollTop = chatBox.scrollHeight;

    try {

        const response = await fetch("/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: message
            })
        });

        const data = await response.json();

        // Show AI response
        if (data.response) {

            chatBox.innerHTML += `
                <div class="message bot">
                    🤖 ${data.response}
                </div>
            `;

        } else {

            chatBox.innerHTML += `
                <div class="message bot">
                    ⚠️ ${data.error || "No response received."}
                </div>
            `;
        }

        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (error) {

        console.error("Error:", error);

        chatBox.innerHTML += `
            <div class="message bot">
                ⚠️ Something went wrong. Please try again.
            </div>
        `;

        chatBox.scrollTop = chatBox.scrollHeight;
    }
}


// Press Enter to send
function handleEnter(event) {

    if (event.key === "Enter" && !event.shiftKey) {

        event.preventDefault();
        sendMessage();
    }
}


// Suggestion buttons
function askSuggestion(question) {

    const input = document.getElementById("question");

    input.value = question;

    sendMessage();
}


// Clear chat
function clearChat() {

    const chatBox = document.getElementById("chat-box");

    chatBox.innerHTML = `
        <div class="message bot">
            Hello! 👋 I am your AI College Assistant.
            Ask me about BCA, exams, fees, Python, assignments or attendance.
        </div>
    `;
}