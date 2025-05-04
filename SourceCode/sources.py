#Rendszerüzenet a modellnek, hogy pontosan mit csináljon.
system_msg = {
  "role": "system",
  "content": (
    "You are an AI coding assistant that helps with creating or decoding regular expressions."
    "If the user asks for previous prompts or outputs (for example: 'the prompt above' or the prompt before'), use the history_tool i provided you"
    "If the user tries to get REALLY out of topic, you MAY say that you cant help with that subject."
    "Remember, you are a persistive agent, you try your best to help the user as much as you can."
    "If the user asks about the previous regex or ask for more detailed information, please answer that."
    "Get to the point, only create the regex and explain it, refrain from lines like 'of course ill help' or 'i hope this helps'"
    "Don't hallucinate. If you are not sure in some regex or don't know the solution, you are allowed to say no."
    ),
}
#regex validáló függvény
regex_tool = {
    "type": "function",
    "function": {
        "name": "validateRegex",
        "description": (
            "Validate a regex. If invalid, return an error message; "
            "the pattern parameter should be the regex that you would show the user in the output message."
            "optionally test it against a sample string."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pattern":     {"type": "string"},
                "test_str": {"type": "string", "nullable": True},
            },
            "required": ["pattern"],
        },
    },
}
#a regex validáló függvény, csak benchmark tesztekre
benchmark_tool = [
    {
        "type": "function",
        "function": {
            "name": "validateRegex",
            "description": (
                "Compile the regex and raise an error if malformed. "
                "You MUST use a test string if the input prompt gives one."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern":  {"type": "string"},
                    "test_str": {"type": "string", "nullable": True},
                },
                "required": ["pattern"],
            },
        },
    }
]
#a chat history-hoz használt függvény
history_tool = {
    "type": "function",
    "function": {
        "name": "get_history",
        "description": (
            "Return a slice of past messages so the assistant can quote them."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "startIdx": {"type": "integer", "nullable": True},
                "endIdx":   {"type": "integer", "nullable": True},
            },
        },
    },
}
#a benchmarkhoz használt promptok
benchmark_prompts = [
"Generate me a regex that matches an IPv4 address. Here is the test string to test the regex with: My router is at 192.168.1.254",
"Generate me a regex that matches a valid IPv6 address. Here is the test string to test the regex with: IPv6 sample 2001:0db8:85a3:0000:0000:8a2e:0370:7334",
"Generate me a regex that matches U.S. ZIP codes with an optional four‑digit extension. Here is the test string to test the regex with: Send mail to 12345‑6789",
"Generate me a regex that matches email addresses (RFC 5322 basics). Here is the test string to test the regex with: Contact me at alice.bob@example.co.uk",
"Generate me a regex that matches dates in YYYY‑MM‑DD ISO format and rejects invalid leap‑year dates. Here is the test string to test the regex with: The due date is 2025‑04‑30",
"Generate me a regex that matches times in 24‑hour HH:MM format. Here is the test string to test the regex with: Event starts at 23:45",
"Generate me a regex that matches credit‑card numbers written as four groups of four digits separated by spaces or dashes. Here is the test string to test the regex with: My card is 4111‑1111‑1111‑1111",
"Generate me a regex that matches hexadecimal color codes like #FFAA33. Here is the test string to test the regex with: Background color #1e90ff",
"Generate me a regex that matches floating‑point numbers with optional sign and scientific exponent. Here is the test string to test the regex with: Value ‑1.23e‑10",
"Generate me a regex that matches URLs beginning with http:// or https://, including an optional port. Here is the test string to test the regex with: Visit https://example.com:8080/index.html",
"Generate me a regex that matches slug‑style strings (lowercase letters, numbers, and dashes). Here is the test string to test the regex with: article slug my-first-blog-post-2025",
"Generate me a regex that matches MAC addresses (00:1A:2B:3C:4D:5E). Here is the test string to test the regex with: Device MAC 00:1A:2B:3C:4D:5E",
"Generate me a regex that matches HTML <img> tags and captures the src attribute. Here is the test string to test the regex with: <img src='https://example.com/logo.png' alt='logo'>",
"Generate me a regex that matches C‑style block comments (/* comment */) across multiple lines. Here is the test string to test the regex with: / multi‑line\ncomment /",
"Generate me a regex that matches lines that are empty or contain only whitespace. Here is the test string to test the regex with: Line1\n \nLine2",
"Generate me a regex that matches valid JavaScript variable names. Here is the test string to test the regex with: let userName123 = 'John';",
"Generate me a regex that matches positive integers that are multiples of 5. Here is the test string to test the regex with: Tickets sold 75",
"Generate me a regex that matches numbers formatted as European currency (1.234,56 €). Here is the test string to test the regex with: Total cost 1.234,56 €",
"Generate me a regex that matches Markdown headings from level 1 to 6. Here is the test string to test the regex with: # Heading 1",
"Generate me a regex that matches hashtags in a tweet, including Unicode letters. Here is the test string to test the regex with: Loving this! #CaféLife",
"Generate me a regex that matches U.S. phone numbers in (555) 123‑4567 format. Here is the test string to test the regex with: Call (555) 123‑4567 now",
"Generate me a regex that matches SQL SELECT statements and captures the table name. Here is the test string to test the regex with: SELECT name, age FROM employees WHERE id=1;",
"Generate me a regex that matches GUID/UUID strings with optional braces. Here is the test string to test the regex with: {550e8400-e29b-41d4-a716-446655440000}",
"Generate me a regex that matches railway station codes consisting of three uppercase letters. Here is the test string to test the regex with: Station code PAD",
"Generate me a regex that matches filenames ending in .jpg, .png, or .gif (case‑insensitive). Here is the test string to test the regex with: Assets hero.PNG",
"Generate me a regex that matches Roman numerals up to 3999. Here is the test string to test the regex with: Chapter XLII",
"Generate me a regex that matches YAML key–value pairs like key: value ignoring leading spaces. Here is the test string to test the regex with: \u00A0\u00A0config: enabled",
"Generate me a regex that matches LaTeX inline math expressions delimited by $...$. Here is the test string to test the regex with: Einstein said $E=mc^2$.",
"Generate me a regex that matches PascalCase words in a sentence. Here is the test string to test the regex with: ThisStringHasPascalCaseWords",
"Generate me a regex that matches JSON boolean literals (true or false) with optional surrounding whitespace. Here is the test string to test the regex with: Flag is  true",
]