def build_test_code_from_examples(function_name: str, examples: list) -> str:
    lines = []
    for ex in examples:
        args_str = ", ".join(repr(arg) for arg in ex.inputs)
        lines.append(f"assert {function_name}({args_str}) == {repr(ex.expected_output)}")
    lines.append("print('All example tests passed')")
    return "\n".join(lines)