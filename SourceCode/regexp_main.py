from openai import OpenAI
import os, json

import tools, sources

# OpenAI kliens inicializálása a környezeti változóban tárolt kulccsal
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if __name__ == "__main__":
    history = tools.ChatHistory()  # állapot – megmarad a cikluson túl

    while True:
        # ── 1. felhasználói bemenet ───────────────────────────
        input_prompt = input("regex> ")
        history.add({"role": "user", "content": input_prompt})

        # ── 2. OpenAI hívás (eszközmenüvel) ────────────────────
        TOOLS = [sources.regex_tool, sources.history_tool]
        first = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=history.to_list(),
            tools=TOOLS,
            tool_choice="auto",
        )
        msg = first.choices[0].message

        # ── 3. Ha a modell tool‑hívást kér ─────────────────────
        if msg.tool_calls:
            history.add(msg)
            for call in msg.tool_calls:
                fn_name = call.function.name
                args = json.loads(call.function.arguments or "{}")

                # függvény diszpécser adott névre
                if fn_name == "get_history":
                    result = history.get_history(**args)
                else:  # validateRegex
                    result = tools.validateRegex(**args)

                # tool válasz betoldása a hisztoriba
                history.add({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": fn_name,
                    "content": result,
                })

            # ── 4. Második kör – a modell most már látja a tool eredményt ──
            second = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=history.to_list(),
            )
            reply = second.choices[0].message.content
        else:
            reply = msg.content

        # ── 5. Válasz kiírása + tárolása ───────────────────────
        print(reply, "\n")
        history.add({"role": "assistant", "content": reply})