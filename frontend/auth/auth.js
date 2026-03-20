const BASE_URL = "http://127.0.0.1:8000/auth";

async function signupUser() {
    const username = document.getElementById("signupUsername").value;
    const email = document.getElementById("signupEmail").value;
    const password = document.getElementById("signupPassword").value;
    const msgEl = document.getElementById("signupMsg");

    const res = await fetch(`${BASE_URL}/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password })
    });

    const data = await res.json();
    msgEl.style.color = res.ok ? "#16a34a" : "#dc2626";
    msgEl.innerText = data.message || data.detail;

    if (res.ok) {
        setTimeout(() => {
            alert("Signup successful. Please login.");
            window.location.href = "/";
        }, 600);
    }
}

async function loginUser() {
    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;
    const msgEl = document.getElementById("loginMsg");

    const res = await fetch(`${BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });

    if (res.redirected) {
        window.location.href = res.url;
        return;
    }

    const data = await res.json();
    msgEl.style.color = res.ok ? "#16a34a" : "#dc2626";
    msgEl.innerText = data.message || data.detail;
}

function loginWithGoogle(){
    window.location.href = `${BASE_URL}/google/login`;
}

let isVoiceRunning = false;

async function startVoiceAuth() {

  if (isVoiceRunning) return;
  isVoiceRunning = true;

  // 🔥 Reset backend session state
  await fetch("/auth/voice-auth/reset", {
    method: "POST",
    credentials: "include"
  });

  let attempts = 0;

  // 🔥 Ask only once (NOT inside loop)
  await speak("Are you a new user or existing user");

  while (attempts < 3) {

    // 🔥 small delay before listening
    await new Promise(res => setTimeout(res, 1500));

    let input = await captureVoice();

    if (!input) {
      attempts++;
      await speak("I did not hear anything, please try again");
      continue;
    }

    // 🔥 STEP 1 → ENTRY / EMAIL FLOW
    let res = await fetch("/auth/voice-auth", {
      method: "POST",
      credentials: "include",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ value: input })
    });

    let data = await res.json();
    console.log("STEP:", data);

    if (!data || !data.next) {
      await speak("Something went wrong, restarting");
      continue;
    }

    await speak(data.message);

    // ───────── EMAIL CONFIRM ─────────
    if (data.next === "confirm_email") {

      await new Promise(res => setTimeout(res, 1500));

      let answer = await captureVoice();

      if (!answer) {
        await speak("Please say yes or no");
        continue;
      }

      let confirmRes = await fetch("/auth/voice-auth", {
        method: "POST",
        credentials: "include",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ value: answer })
      });

      data = await confirmRes.json();
      console.log("CONFIRM:", data);

      await speak(data.message);

      if (data.next === "retry_email") {
        continue;
      }
    }

    // ───────── PIN STEP ─────────
    if (data.next === "ask_pin" || data.next === "set_pin") {

      await new Promise(res => setTimeout(res, 1500));

      let pin = await captureVoice();

      if (!pin) {
        attempts++;
        await speak("I did not hear your pin");
        continue;
      }

      let res2 = await fetch("/auth/voice-auth", {
        method: "POST",
        credentials: "include",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ value: pin })
      });

      if (!res2.ok) {
        const err = await res2.json();
        console.error("VOICE AUTH ERROR:", err);
        await speak(err.detail || "Something went wrong");
        return;
      }

      let final = await res2.json();
      console.log("FINAL:", final);

      if (final.success) {
        await speak("Login successful");

        setTimeout(() => {
          window.location.href = "/dashboard";
        }, 300);

        isVoiceRunning = false;
        return;
      }

      if (final.retry) {
        attempts++;
        await speak("Incorrect pin, try again");
        continue;
      }
    }
  }

  isVoiceRunning = false;
  await speak("Too many attempts. Please try again later");
}

async function speak(text) {
  await fetch("/speak", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ text })
  });
}


async function captureVoice() {

  //  give user time to speak
  await new Promise(res => setTimeout(res, 1500));

  const res = await fetch("/stt-once", {
    method: "POST",
    credentials: "include"
  });

  const data = await res.json();

  if (!data.recognized_text) {
    return null;
  }

  return data.recognized_text;
}