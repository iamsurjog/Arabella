from query_bridge import QueryBridge

def run_tests():
    bridge = QueryBridge()
    test_cases = {
        "What is artificial intelligence?": "artificial intelligence",
        "How do solar panels generate electricity?": "solar panels generate electricity",
        "Tell me about quantum computing": "tell quantum computing",
        "Why is the sky blue?": "sky blue",
        "": "",
        "AI": "ai",
        "What?": "what"
    }

    for inp, expected in test_cases.items():
        output = bridge.transform(inp)
        print(f"Input:    {inp}")
        print(f"Output:   {output}")
        print(f"Expected: {expected}")
        print(f"Pass:     {output == expected}\n")

if __name__ == "__main__":
    run_tests()
