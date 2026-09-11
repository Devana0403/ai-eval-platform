# from app.sandbox import run_in_sandbox

# # A harmless test case
# safe_code = "print('Hello from inside the sandbox')"
# print("Test 1 - safe code:")
# print(run_in_sandbox(safe_code))

# # A deliberately bad test case: infinite loop, should get killed by the timeout
# infinite_loop_code = "while True:\n    pass"
# print("\nTest 2 - infinite loop (should time out):")
# print(run_in_sandbox(infinite_loop_code, timeout_seconds=3))

# from app.sandbox import run_in_sandbox

# property_test_code = """
# from hypothesis import given, strategies as st

# def add(a, b):
#     return a + b

# @given(st.integers(), st.integers())
# def test_add_property(a, b):
#     assert add(a, b) == a + b

# test_add_property()
# print("Property test passed across many random inputs")
# """

# print(run_in_sandbox(property_test_code, timeout_seconds=10))


# from app.sandbox import run_in_sandbox

# buggy_property_test = """
# from hypothesis import given, strategies as st

# def add(a, b):
#     # Bug: works for positive numbers, breaks with negatives
#     if a >= 0 and b >= 0:
#         return a + b
#     return a - b   # wrong!

# @given(st.integers(), st.integers())
# def test_add_property(a, b):
#     assert add(a, b) == a + b

# test_add_property()
# print("This should NOT print if Hypothesis does its job")
# """

# print(run_in_sandbox(buggy_property_test, timeout_seconds=10))

from app.sandbox import run_in_sandbox

print("Test 1 - safe code:")
print(run_in_sandbox("print('Hello from Azure sandbox')"))

print("\nTest 2 - infinite loop (should time out):")
print(run_in_sandbox("while True:\n    pass", timeout_seconds=5))