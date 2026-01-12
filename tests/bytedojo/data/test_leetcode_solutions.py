"""
Tests for LeetCode problem test data.

This file contains actual solutions for LeetCode problems 1-100
to verify that our internal test data is correct.
"""

import pytest
import json
from pathlib import Path
from typing import List, Optional


# Get the path to test data
TEST_DATA_DIR = Path(__file__).parent.parent.parent.parent / "src" / "bytedojo" / "data" / "tests" / "leetcode"


def load_test_data(problem_id: int):
    """Load test data for a problem."""
    test_file = TEST_DATA_DIR / f"{problem_id}.json"
    if not test_file.exists():
        pytest.skip(f"No test data for problem {problem_id}")
    with open(test_file) as f:
        return json.load(f)


# ============================================================================
# SOLUTIONS
# ============================================================================

class Solution:
    """Combined solution class for all problems."""

    # Problem 1: Two Sum
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}
        for i, num in enumerate(nums):
            complement = target - num
            if complement in seen:
                return [seen[complement], i]
            seen[num] = i
        return []

    # Problem 2: Add Two Numbers (represented as arrays)
    def addTwoNumbers(self, l1: List[int], l2: List[int]) -> List[int]:
        result = []
        carry = 0
        i = 0
        while i < len(l1) or i < len(l2) or carry:
            val = carry
            if i < len(l1):
                val += l1[i]
            if i < len(l2):
                val += l2[i]
            result.append(val % 10)
            carry = val // 10
            i += 1
        return result

    # Problem 3: Longest Substring Without Repeating Characters
    def lengthOfLongestSubstring(self, s: str) -> int:
        seen = {}
        start = 0
        max_len = 0
        for i, c in enumerate(s):
            if c in seen and seen[c] >= start:
                start = seen[c] + 1
            seen[c] = i
            max_len = max(max_len, i - start + 1)
        return max_len

    # Problem 4: Median of Two Sorted Arrays
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        merged = sorted(nums1 + nums2)
        n = len(merged)
        if n % 2 == 1:
            return float(merged[n // 2])
        return (merged[n // 2 - 1] + merged[n // 2]) / 2

    # Problem 5: Longest Palindromic Substring
    def longestPalindrome(self, s: str) -> str:
        if not s:
            return ""

        def expand(left, right):
            while left >= 0 and right < len(s) and s[left] == s[right]:
                left -= 1
                right += 1
            return s[left + 1:right]

        result = ""
        for i in range(len(s)):
            odd = expand(i, i)
            even = expand(i, i + 1)
            if len(odd) > len(result):
                result = odd
            if len(even) > len(result):
                result = even
        return result

    # Problem 6: Zigzag Conversion
    def convert(self, s: str, numRows: int) -> str:
        if numRows == 1 or numRows >= len(s):
            return s
        rows = [''] * numRows
        row, step = 0, 1
        for c in s:
            rows[row] += c
            if row == 0:
                step = 1
            elif row == numRows - 1:
                step = -1
            row += step
        return ''.join(rows)

    # Problem 7: Reverse Integer
    def reverse(self, x: int) -> int:
        sign = 1 if x >= 0 else -1
        x = abs(x)
        result = 0
        while x:
            result = result * 10 + x % 10
            x //= 10
        result *= sign
        if result < -2**31 or result > 2**31 - 1:
            return 0
        return result

    # Problem 8: String to Integer (atoi)
    def myAtoi(self, s: str) -> int:
        s = s.lstrip()
        if not s:
            return 0
        sign = 1
        i = 0
        if s[0] == '-':
            sign = -1
            i = 1
        elif s[0] == '+':
            i = 1
        result = 0
        while i < len(s) and s[i].isdigit():
            result = result * 10 + int(s[i])
            i += 1
        result *= sign
        return max(-2**31, min(2**31 - 1, result))

    # Problem 9: Palindrome Number
    def isPalindrome(self, x: int) -> bool:
        if x < 0:
            return False
        return str(x) == str(x)[::-1]

    # Problem 11: Container With Most Water
    def maxArea(self, height: List[int]) -> int:
        left, right = 0, len(height) - 1
        max_area = 0
        while left < right:
            area = min(height[left], height[right]) * (right - left)
            max_area = max(max_area, area)
            if height[left] < height[right]:
                left += 1
            else:
                right -= 1
        return max_area

    # Problem 12: Integer to Roman
    def intToRoman(self, num: int) -> str:
        values = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
                  (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
                  (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
        result = ''
        for val, sym in values:
            while num >= val:
                result += sym
                num -= val
        return result

    # Problem 13: Roman to Integer
    def romanToInt(self, s: str) -> int:
        values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        result = 0
        prev = 0
        for c in s:
            curr = values[c]
            if curr > prev:
                result += curr - 2 * prev
            else:
                result += curr
            prev = curr
        return result

    # Problem 14: Longest Common Prefix
    def longestCommonPrefix(self, strs: List[str]) -> str:
        if not strs:
            return ""
        prefix = strs[0]
        for s in strs[1:]:
            while not s.startswith(prefix):
                prefix = prefix[:-1]
                if not prefix:
                    return ""
        return prefix

    # Problem 20: Valid Parentheses
    def isValid(self, s: str) -> bool:
        stack = []
        pairs = {')': '(', ']': '[', '}': '{'}
        for c in s:
            if c in '([{':
                stack.append(c)
            elif c in ')]}':
                if not stack or stack[-1] != pairs[c]:
                    return False
                stack.pop()
        return len(stack) == 0

    # Problem 26: Remove Duplicates from Sorted Array
    def removeDuplicates(self, nums: List[int]) -> int:
        if not nums:
            return 0
        k = 1
        for i in range(1, len(nums)):
            if nums[i] != nums[i-1]:
                nums[k] = nums[i]
                k += 1
        return k

    # Problem 27: Remove Element
    def removeElement(self, nums: List[int], val: int) -> int:
        k = 0
        for i in range(len(nums)):
            if nums[i] != val:
                nums[k] = nums[i]
                k += 1
        return k

    # Problem 28: Find the Index of the First Occurrence in a String
    def strStr(self, haystack: str, needle: str) -> int:
        return haystack.find(needle)

    # Problem 35: Search Insert Position
    def searchInsert(self, nums: List[int], target: int) -> int:
        left, right = 0, len(nums)
        while left < right:
            mid = (left + right) // 2
            if nums[mid] < target:
                left = mid + 1
            else:
                right = mid
        return left

    # Problem 53: Maximum Subarray
    def maxSubArray(self, nums: List[int]) -> int:
        max_sum = curr_sum = nums[0]
        for num in nums[1:]:
            curr_sum = max(num, curr_sum + num)
            max_sum = max(max_sum, curr_sum)
        return max_sum

    # Problem 58: Length of Last Word
    def lengthOfLastWord(self, s: str) -> int:
        return len(s.rstrip().split()[-1]) if s.strip() else 0

    # Problem 66: Plus One
    def plusOne(self, digits: List[int]) -> List[int]:
        for i in range(len(digits) - 1, -1, -1):
            if digits[i] < 9:
                digits[i] += 1
                return digits
            digits[i] = 0
        return [1] + digits

    # Problem 67: Add Binary
    def addBinary(self, a: str, b: str) -> str:
        return bin(int(a, 2) + int(b, 2))[2:]

    # Problem 69: Sqrt(x)
    def mySqrt(self, x: int) -> int:
        if x < 2:
            return x
        left, right = 1, x // 2
        while left <= right:
            mid = (left + right) // 2
            if mid * mid == x:
                return mid
            elif mid * mid < x:
                left = mid + 1
            else:
                right = mid - 1
        return right

    # Problem 70: Climbing Stairs
    def climbStairs(self, n: int) -> int:
        if n <= 2:
            return n
        a, b = 1, 2
        for _ in range(3, n + 1):
            a, b = b, a + b
        return b

    # Problem 10: Regular Expression Matching
    def isMatch(self, s: str, p: str) -> bool:
        dp = [[False] * (len(p) + 1) for _ in range(len(s) + 1)]
        dp[0][0] = True
        for j in range(1, len(p) + 1):
            if p[j-1] == '*':
                dp[0][j] = dp[0][j-2]
        for i in range(1, len(s) + 1):
            for j in range(1, len(p) + 1):
                if p[j-1] == '*':
                    dp[i][j] = dp[i][j-2]
                    if p[j-2] == '.' or p[j-2] == s[i-1]:
                        dp[i][j] = dp[i][j] or dp[i-1][j]
                elif p[j-1] == '.' or p[j-1] == s[i-1]:
                    dp[i][j] = dp[i-1][j-1]
        return dp[len(s)][len(p)]

    # Problem 15: 3Sum
    def threeSum(self, nums: List[int]) -> List[List[int]]:
        nums.sort()
        result = []
        for i in range(len(nums) - 2):
            if i > 0 and nums[i] == nums[i-1]:
                continue
            left, right = i + 1, len(nums) - 1
            while left < right:
                total = nums[i] + nums[left] + nums[right]
                if total < 0:
                    left += 1
                elif total > 0:
                    right -= 1
                else:
                    result.append([nums[i], nums[left], nums[right]])
                    while left < right and nums[left] == nums[left+1]:
                        left += 1
                    while left < right and nums[right] == nums[right-1]:
                        right -= 1
                    left += 1
                    right -= 1
        return result

    # Problem 16: 3Sum Closest
    def threeSumClosest(self, nums: List[int], target: int) -> int:
        nums.sort()
        closest = float('inf')
        for i in range(len(nums) - 2):
            left, right = i + 1, len(nums) - 1
            while left < right:
                total = nums[i] + nums[left] + nums[right]
                if abs(total - target) < abs(closest - target):
                    closest = total
                if total < target:
                    left += 1
                elif total > target:
                    right -= 1
                else:
                    return target
        return closest

    # Problem 17: Letter Combinations of a Phone Number
    def letterCombinations(self, digits: str) -> List[str]:
        if not digits:
            return []
        mapping = {'2': 'abc', '3': 'def', '4': 'ghi', '5': 'jkl',
                   '6': 'mno', '7': 'pqrs', '8': 'tuv', '9': 'wxyz'}
        result = ['']
        for digit in digits:
            result = [prefix + char for prefix in result for char in mapping[digit]]
        return result

    # Problem 18: 4Sum
    def fourSum(self, nums: List[int], target: int) -> List[List[int]]:
        nums.sort()
        result = []
        n = len(nums)
        for i in range(n - 3):
            if i > 0 and nums[i] == nums[i-1]:
                continue
            for j in range(i + 1, n - 2):
                if j > i + 1 and nums[j] == nums[j-1]:
                    continue
                left, right = j + 1, n - 1
                while left < right:
                    total = nums[i] + nums[j] + nums[left] + nums[right]
                    if total < target:
                        left += 1
                    elif total > target:
                        right -= 1
                    else:
                        result.append([nums[i], nums[j], nums[left], nums[right]])
                        while left < right and nums[left] == nums[left+1]:
                            left += 1
                        while left < right and nums[right] == nums[right-1]:
                            right -= 1
                        left += 1
                        right -= 1
        return result

    # Problem 19: Remove Nth Node From End of List (array representation)
    def removeNthFromEnd(self, head: List[int], n: int) -> List[int]:
        if not head:
            return []
        idx = len(head) - n
        return head[:idx] + head[idx+1:]

    # Problem 21: Merge Two Sorted Lists (array representation)
    def mergeTwoLists(self, list1: List[int], list2: List[int]) -> List[int]:
        result = []
        i = j = 0
        while i < len(list1) and j < len(list2):
            if list1[i] <= list2[j]:
                result.append(list1[i])
                i += 1
            else:
                result.append(list2[j])
                j += 1
        result.extend(list1[i:])
        result.extend(list2[j:])
        return result

    # Problem 22: Generate Parentheses
    def generateParenthesis(self, n: int) -> List[str]:
        result = []
        def backtrack(s, left, right):
            if len(s) == 2 * n:
                result.append(s)
                return
            if left < n:
                backtrack(s + '(', left + 1, right)
            if right < left:
                backtrack(s + ')', left, right + 1)
        backtrack('', 0, 0)
        return result

    # Problem 23: Merge k Sorted Lists (array of arrays representation)
    def mergeKLists(self, lists: List[List[int]]) -> List[int]:
        import heapq
        heap = []
        for i, lst in enumerate(lists):
            for j, val in enumerate(lst):
                heapq.heappush(heap, val)
        result = []
        while heap:
            result.append(heapq.heappop(heap))
        return result

    # Problem 24: Swap Nodes in Pairs (array representation)
    def swapPairs(self, head: List[int]) -> List[int]:
        result = head[:]
        for i in range(0, len(result) - 1, 2):
            result[i], result[i+1] = result[i+1], result[i]
        return result

    # Problem 25: Reverse Nodes in k-Group (array representation)
    def reverseKGroup(self, head: List[int], k: int) -> List[int]:
        result = []
        for i in range(0, len(head), k):
            group = head[i:i+k]
            if len(group) == k:
                result.extend(reversed(group))
            else:
                result.extend(group)
        return result

    # Problem 29: Divide Two Integers
    def divide(self, dividend: int, divisor: int) -> int:
        INT_MAX = 2**31 - 1
        INT_MIN = -2**31
        if dividend == INT_MIN and divisor == -1:
            return INT_MAX
        sign = -1 if (dividend < 0) ^ (divisor < 0) else 1
        dividend, divisor = abs(dividend), abs(divisor)
        result = 0
        while dividend >= divisor:
            temp, multiple = divisor, 1
            while dividend >= (temp << 1):
                temp <<= 1
                multiple <<= 1
            dividend -= temp
            result += multiple
        return sign * result

    # Problem 30: Substring with Concatenation of All Words
    def findSubstring(self, s: str, words: List[str]) -> List[int]:
        if not s or not words:
            return []
        word_len = len(words[0])
        total_len = word_len * len(words)
        from collections import Counter
        word_count = Counter(words)
        result = []
        for i in range(len(s) - total_len + 1):
            seen = Counter()
            for j in range(len(words)):
                word = s[i + j * word_len:i + (j + 1) * word_len]
                if word not in word_count:
                    break
                seen[word] += 1
                if seen[word] > word_count[word]:
                    break
            else:
                result.append(i)
        return result

    # Problem 31: Next Permutation
    def nextPermutation(self, nums: List[int]) -> None:
        i = len(nums) - 2
        while i >= 0 and nums[i] >= nums[i + 1]:
            i -= 1
        if i >= 0:
            j = len(nums) - 1
            while nums[j] <= nums[i]:
                j -= 1
            nums[i], nums[j] = nums[j], nums[i]
        nums[i + 1:] = reversed(nums[i + 1:])

    # Problem 32: Longest Valid Parentheses
    def longestValidParentheses(self, s: str) -> int:
        stack = [-1]
        max_len = 0
        for i, c in enumerate(s):
            if c == '(':
                stack.append(i)
            else:
                stack.pop()
                if not stack:
                    stack.append(i)
                else:
                    max_len = max(max_len, i - stack[-1])
        return max_len

    # Problem 33: Search in Rotated Sorted Array
    def search(self, nums: List[int], target: int) -> int:
        left, right = 0, len(nums) - 1
        while left <= right:
            mid = (left + right) // 2
            if nums[mid] == target:
                return mid
            if nums[left] <= nums[mid]:
                if nums[left] <= target < nums[mid]:
                    right = mid - 1
                else:
                    left = mid + 1
            else:
                if nums[mid] < target <= nums[right]:
                    left = mid + 1
                else:
                    right = mid - 1
        return -1

    # Problem 34: Find First and Last Position
    def searchRange(self, nums: List[int], target: int) -> List[int]:
        def find_left():
            left, right = 0, len(nums)
            while left < right:
                mid = (left + right) // 2
                if nums[mid] < target:
                    left = mid + 1
                else:
                    right = mid
            return left

        def find_right():
            left, right = 0, len(nums)
            while left < right:
                mid = (left + right) // 2
                if nums[mid] <= target:
                    left = mid + 1
                else:
                    right = mid
            return left

        left_idx = find_left()
        if left_idx == len(nums) or nums[left_idx] != target:
            return [-1, -1]
        return [left_idx, find_right() - 1]

    # Problem 36: Valid Sudoku
    def isValidSudoku(self, board: List[List[str]]) -> bool:
        rows = [set() for _ in range(9)]
        cols = [set() for _ in range(9)]
        boxes = [set() for _ in range(9)]
        for i in range(9):
            for j in range(9):
                val = board[i][j]
                if val == '.':
                    continue
                box_idx = (i // 3) * 3 + j // 3
                if val in rows[i] or val in cols[j] or val in boxes[box_idx]:
                    return False
                rows[i].add(val)
                cols[j].add(val)
                boxes[box_idx].add(val)
        return True

    # Problem 37: Sudoku Solver
    def solveSudoku(self, board: List[List[str]]) -> None:
        def is_valid(r, c, val):
            for i in range(9):
                if board[r][i] == val or board[i][c] == val:
                    return False
            box_r, box_c = 3 * (r // 3), 3 * (c // 3)
            for i in range(3):
                for j in range(3):
                    if board[box_r + i][box_c + j] == val:
                        return False
            return True

        def solve():
            for i in range(9):
                for j in range(9):
                    if board[i][j] == '.':
                        for val in '123456789':
                            if is_valid(i, j, val):
                                board[i][j] = val
                                if solve():
                                    return True
                                board[i][j] = '.'
                        return False
            return True
        solve()

    # Problem 38: Count and Say
    def countAndSay(self, n: int) -> str:
        if n == 1:
            return "1"
        prev = self.countAndSay(n - 1)
        result = []
        count = 1
        for i in range(1, len(prev)):
            if prev[i] == prev[i - 1]:
                count += 1
            else:
                result.append(str(count) + prev[i - 1])
                count = 1
        result.append(str(count) + prev[-1])
        return ''.join(result)

    # Problem 39: Combination Sum
    def combinationSum(self, candidates: List[int], target: int) -> List[List[int]]:
        result = []
        def backtrack(start, path, remaining):
            if remaining == 0:
                result.append(path[:])
                return
            for i in range(start, len(candidates)):
                if candidates[i] > remaining:
                    continue
                path.append(candidates[i])
                backtrack(i, path, remaining - candidates[i])
                path.pop()
        backtrack(0, [], target)
        return result

    # Problem 40: Combination Sum II
    def combinationSum2(self, candidates: List[int], target: int) -> List[List[int]]:
        candidates.sort()
        result = []
        def backtrack(start, path, remaining):
            if remaining == 0:
                result.append(path[:])
                return
            for i in range(start, len(candidates)):
                if i > start and candidates[i] == candidates[i - 1]:
                    continue
                if candidates[i] > remaining:
                    break
                path.append(candidates[i])
                backtrack(i + 1, path, remaining - candidates[i])
                path.pop()
        backtrack(0, [], target)
        return result

    # Problem 41: First Missing Positive
    def firstMissingPositive(self, nums: List[int]) -> int:
        n = len(nums)
        for i in range(n):
            while 1 <= nums[i] <= n and nums[nums[i] - 1] != nums[i]:
                nums[nums[i] - 1], nums[i] = nums[i], nums[nums[i] - 1]
        for i in range(n):
            if nums[i] != i + 1:
                return i + 1
        return n + 1

    # Problem 42: Trapping Rain Water
    def trap(self, height: List[int]) -> int:
        if not height:
            return 0
        left, right = 0, len(height) - 1
        left_max = right_max = 0
        water = 0
        while left < right:
            if height[left] < height[right]:
                if height[left] >= left_max:
                    left_max = height[left]
                else:
                    water += left_max - height[left]
                left += 1
            else:
                if height[right] >= right_max:
                    right_max = height[right]
                else:
                    water += right_max - height[right]
                right -= 1
        return water

    # Problem 43: Multiply Strings
    def multiply(self, num1: str, num2: str) -> str:
        if num1 == "0" or num2 == "0":
            return "0"
        result = [0] * (len(num1) + len(num2))
        for i in range(len(num1) - 1, -1, -1):
            for j in range(len(num2) - 1, -1, -1):
                mul = int(num1[i]) * int(num2[j])
                p1, p2 = i + j, i + j + 1
                total = mul + result[p2]
                result[p2] = total % 10
                result[p1] += total // 10
        result_str = ''.join(map(str, result))
        return result_str.lstrip('0') or '0'

    # Problem 44: Wildcard Matching
    def isMatchWildcard(self, s: str, p: str) -> bool:
        dp = [[False] * (len(p) + 1) for _ in range(len(s) + 1)]
        dp[0][0] = True
        for j in range(1, len(p) + 1):
            if p[j - 1] == '*':
                dp[0][j] = dp[0][j - 1]
        for i in range(1, len(s) + 1):
            for j in range(1, len(p) + 1):
                if p[j - 1] == '*':
                    dp[i][j] = dp[i - 1][j] or dp[i][j - 1]
                elif p[j - 1] == '?' or s[i - 1] == p[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
        return dp[len(s)][len(p)]

    # Problem 45: Jump Game II
    def jump(self, nums: List[int]) -> int:
        jumps = 0
        current_end = 0
        farthest = 0
        for i in range(len(nums) - 1):
            farthest = max(farthest, i + nums[i])
            if i == current_end:
                jumps += 1
                current_end = farthest
        return jumps

    # Problem 46: Permutations
    def permute(self, nums: List[int]) -> List[List[int]]:
        result = []
        def backtrack(path, remaining):
            if not remaining:
                result.append(path[:])
                return
            for i in range(len(remaining)):
                path.append(remaining[i])
                backtrack(path, remaining[:i] + remaining[i+1:])
                path.pop()
        backtrack([], nums)
        return result

    # Problem 47: Permutations II
    def permuteUnique(self, nums: List[int]) -> List[List[int]]:
        result = []
        nums.sort()
        def backtrack(path, remaining):
            if not remaining:
                result.append(path[:])
                return
            for i in range(len(remaining)):
                if i > 0 and remaining[i] == remaining[i - 1]:
                    continue
                path.append(remaining[i])
                backtrack(path, remaining[:i] + remaining[i+1:])
                path.pop()
        backtrack([], nums)
        return result

    # Problem 48: Rotate Image
    def rotate(self, matrix: List[List[int]]) -> None:
        n = len(matrix)
        # Transpose
        for i in range(n):
            for j in range(i + 1, n):
                matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
        # Reverse each row
        for row in matrix:
            row.reverse()

    # Problem 49: Group Anagrams
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        from collections import defaultdict
        groups = defaultdict(list)
        for s in strs:
            key = ''.join(sorted(s))
            groups[key].append(s)
        return list(groups.values())

    # Problem 50: Pow(x, n)
    def myPow(self, x: float, n: int) -> float:
        if n == 0:
            return 1.0
        if n < 0:
            x = 1 / x
            n = -n
        result = 1.0
        while n:
            if n % 2:
                result *= x
            x *= x
            n //= 2
        return result

    # Problem 51: N-Queens
    def solveNQueens(self, n: int) -> List[List[str]]:
        result = []
        board = [['.'] * n for _ in range(n)]
        cols, diag1, diag2 = set(), set(), set()

        def backtrack(row):
            if row == n:
                result.append([''.join(r) for r in board])
                return
            for col in range(n):
                if col in cols or row - col in diag1 or row + col in diag2:
                    continue
                board[row][col] = 'Q'
                cols.add(col)
                diag1.add(row - col)
                diag2.add(row + col)
                backtrack(row + 1)
                board[row][col] = '.'
                cols.remove(col)
                diag1.remove(row - col)
                diag2.remove(row + col)

        backtrack(0)
        return result

    # Problem 52: N-Queens II
    def totalNQueens(self, n: int) -> int:
        return len(self.solveNQueens(n))

    # Problem 54: Spiral Matrix
    def spiralOrder(self, matrix: List[List[int]]) -> List[int]:
        if not matrix:
            return []
        result = []
        top, bottom, left, right = 0, len(matrix) - 1, 0, len(matrix[0]) - 1
        while top <= bottom and left <= right:
            for i in range(left, right + 1):
                result.append(matrix[top][i])
            top += 1
            for i in range(top, bottom + 1):
                result.append(matrix[i][right])
            right -= 1
            if top <= bottom:
                for i in range(right, left - 1, -1):
                    result.append(matrix[bottom][i])
                bottom -= 1
            if left <= right:
                for i in range(bottom, top - 1, -1):
                    result.append(matrix[i][left])
                left += 1
        return result

    # Problem 55: Jump Game
    def canJump(self, nums: List[int]) -> bool:
        max_reach = 0
        for i, num in enumerate(nums):
            if i > max_reach:
                return False
            max_reach = max(max_reach, i + num)
        return True

    # Problem 56: Merge Intervals
    def merge(self, intervals: List[List[int]]) -> List[List[int]]:
        if not intervals:
            return []
        intervals.sort(key=lambda x: x[0])
        result = [intervals[0]]
        for start, end in intervals[1:]:
            if start <= result[-1][1]:
                result[-1][1] = max(result[-1][1], end)
            else:
                result.append([start, end])
        return result

    # Problem 57: Insert Interval
    def insert(self, intervals: List[List[int]], newInterval: List[int]) -> List[List[int]]:
        result = []
        i = 0
        while i < len(intervals) and intervals[i][1] < newInterval[0]:
            result.append(intervals[i])
            i += 1
        while i < len(intervals) and intervals[i][0] <= newInterval[1]:
            newInterval[0] = min(newInterval[0], intervals[i][0])
            newInterval[1] = max(newInterval[1], intervals[i][1])
            i += 1
        result.append(newInterval)
        result.extend(intervals[i:])
        return result

    # Problem 59: Spiral Matrix II
    def generateMatrix(self, n: int) -> List[List[int]]:
        matrix = [[0] * n for _ in range(n)]
        top, bottom, left, right = 0, n - 1, 0, n - 1
        num = 1
        while top <= bottom and left <= right:
            for i in range(left, right + 1):
                matrix[top][i] = num
                num += 1
            top += 1
            for i in range(top, bottom + 1):
                matrix[i][right] = num
                num += 1
            right -= 1
            if top <= bottom:
                for i in range(right, left - 1, -1):
                    matrix[bottom][i] = num
                    num += 1
                bottom -= 1
            if left <= right:
                for i in range(bottom, top - 1, -1):
                    matrix[i][left] = num
                    num += 1
                left += 1
        return matrix

    # Problem 60: Permutation Sequence
    def getPermutation(self, n: int, k: int) -> str:
        import math
        nums = list(range(1, n + 1))
        k -= 1
        result = []
        for i in range(n, 0, -1):
            fact = math.factorial(i - 1)
            idx = k // fact
            result.append(str(nums[idx]))
            nums.pop(idx)
            k %= fact
        return ''.join(result)

    # Problem 61: Rotate List (array representation)
    def rotateRight(self, head: List[int], k: int) -> List[int]:
        if not head or k == 0:
            return head
        n = len(head)
        k = k % n
        if k == 0:
            return head
        return head[-k:] + head[:-k]

    # Problem 62: Unique Paths
    def uniquePaths(self, m: int, n: int) -> int:
        dp = [[1] * n for _ in range(m)]
        for i in range(1, m):
            for j in range(1, n):
                dp[i][j] = dp[i-1][j] + dp[i][j-1]
        return dp[m-1][n-1]

    # Problem 63: Unique Paths II
    def uniquePathsWithObstacles(self, obstacleGrid: List[List[int]]) -> int:
        m, n = len(obstacleGrid), len(obstacleGrid[0])
        if obstacleGrid[0][0] == 1:
            return 0
        dp = [[0] * n for _ in range(m)]
        dp[0][0] = 1
        for i in range(1, m):
            dp[i][0] = dp[i-1][0] if obstacleGrid[i][0] == 0 else 0
        for j in range(1, n):
            dp[0][j] = dp[0][j-1] if obstacleGrid[0][j] == 0 else 0
        for i in range(1, m):
            for j in range(1, n):
                if obstacleGrid[i][j] == 0:
                    dp[i][j] = dp[i-1][j] + dp[i][j-1]
        return dp[m-1][n-1]

    # Problem 64: Minimum Path Sum
    def minPathSum(self, grid: List[List[int]]) -> int:
        m, n = len(grid), len(grid[0])
        dp = [[0] * n for _ in range(m)]
        dp[0][0] = grid[0][0]
        for i in range(1, m):
            dp[i][0] = dp[i-1][0] + grid[i][0]
        for j in range(1, n):
            dp[0][j] = dp[0][j-1] + grid[0][j]
        for i in range(1, m):
            for j in range(1, n):
                dp[i][j] = min(dp[i-1][j], dp[i][j-1]) + grid[i][j]
        return dp[m-1][n-1]

    # Problem 65: Valid Number
    def isNumber(self, s: str) -> bool:
        try:
            float(s)
            return True
        except:
            return False

    # Problem 68: Text Justification
    def fullJustify(self, words: List[str], maxWidth: int) -> List[str]:
        result = []
        line = []
        line_len = 0
        for word in words:
            if line_len + len(word) + len(line) > maxWidth:
                spaces = maxWidth - line_len
                if len(line) == 1:
                    result.append(line[0] + ' ' * spaces)
                else:
                    base_space = spaces // (len(line) - 1)
                    extra = spaces % (len(line) - 1)
                    justified = ''
                    for i, w in enumerate(line[:-1]):
                        justified += w + ' ' * (base_space + (1 if i < extra else 0))
                    justified += line[-1]
                    result.append(justified)
                line = []
                line_len = 0
            line.append(word)
            line_len += len(word)
        result.append(' '.join(line).ljust(maxWidth))
        return result

    # Problem 71: Simplify Path
    def simplifyPath(self, path: str) -> str:
        stack = []
        for part in path.split('/'):
            if part == '..':
                if stack:
                    stack.pop()
            elif part and part != '.':
                stack.append(part)
        return '/' + '/'.join(stack)

    # Problem 72: Edit Distance
    def minDistance(self, word1: str, word2: str) -> int:
        m, n = len(word1), len(word2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if word1[i-1] == word2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
        return dp[m][n]

    # Problem 73: Set Matrix Zeroes
    def setZeroes(self, matrix: List[List[int]]) -> None:
        m, n = len(matrix), len(matrix[0])
        rows, cols = set(), set()
        for i in range(m):
            for j in range(n):
                if matrix[i][j] == 0:
                    rows.add(i)
                    cols.add(j)
        for i in range(m):
            for j in range(n):
                if i in rows or j in cols:
                    matrix[i][j] = 0

    # Problem 74: Search a 2D Matrix
    def searchMatrix(self, matrix: List[List[int]], target: int) -> bool:
        if not matrix:
            return False
        m, n = len(matrix), len(matrix[0])
        left, right = 0, m * n - 1
        while left <= right:
            mid = (left + right) // 2
            val = matrix[mid // n][mid % n]
            if val == target:
                return True
            elif val < target:
                left = mid + 1
            else:
                right = mid - 1
        return False

    # Problem 75: Sort Colors
    def sortColors(self, nums: List[int]) -> None:
        left, mid, right = 0, 0, len(nums) - 1
        while mid <= right:
            if nums[mid] == 0:
                nums[left], nums[mid] = nums[mid], nums[left]
                left += 1
                mid += 1
            elif nums[mid] == 1:
                mid += 1
            else:
                nums[mid], nums[right] = nums[right], nums[mid]
                right -= 1

    # Problem 76: Minimum Window Substring
    def minWindow(self, s: str, t: str) -> str:
        from collections import Counter
        need = Counter(t)
        have = Counter()
        required = len(need)
        formed = 0
        left = 0
        result = ""
        min_len = float('inf')
        for right, char in enumerate(s):
            have[char] += 1
            if char in need and have[char] == need[char]:
                formed += 1
            while formed == required:
                if right - left + 1 < min_len:
                    min_len = right - left + 1
                    result = s[left:right+1]
                have[s[left]] -= 1
                if s[left] in need and have[s[left]] < need[s[left]]:
                    formed -= 1
                left += 1
        return result

    # Problem 77: Combinations
    def combine(self, n: int, k: int) -> List[List[int]]:
        result = []
        def backtrack(start, path):
            if len(path) == k:
                result.append(path[:])
                return
            for i in range(start, n + 1):
                path.append(i)
                backtrack(i + 1, path)
                path.pop()
        backtrack(1, [])
        return result

    # Problem 78: Subsets
    def subsets(self, nums: List[int]) -> List[List[int]]:
        result = []
        def backtrack(start, path):
            result.append(path[:])
            for i in range(start, len(nums)):
                path.append(nums[i])
                backtrack(i + 1, path)
                path.pop()
        backtrack(0, [])
        return result

    # Problem 79: Word Search
    def exist(self, board: List[List[str]], word: str) -> bool:
        m, n = len(board), len(board[0])
        def dfs(i, j, k):
            if k == len(word):
                return True
            if i < 0 or i >= m or j < 0 or j >= n or board[i][j] != word[k]:
                return False
            temp = board[i][j]
            board[i][j] = '#'
            found = dfs(i+1, j, k+1) or dfs(i-1, j, k+1) or dfs(i, j+1, k+1) or dfs(i, j-1, k+1)
            board[i][j] = temp
            return found
        for i in range(m):
            for j in range(n):
                if dfs(i, j, 0):
                    return True
        return False

    # Problem 80: Remove Duplicates from Sorted Array II
    def removeDuplicates2(self, nums: List[int]) -> int:
        if len(nums) <= 2:
            return len(nums)
        k = 2
        for i in range(2, len(nums)):
            if nums[i] != nums[k - 2]:
                nums[k] = nums[i]
                k += 1
        return k

    # Problem 81: Search in Rotated Sorted Array II
    def searchWithDuplicates(self, nums: List[int], target: int) -> bool:
        left, right = 0, len(nums) - 1
        while left <= right:
            mid = (left + right) // 2
            if nums[mid] == target:
                return True
            if nums[left] == nums[mid] == nums[right]:
                left += 1
                right -= 1
            elif nums[left] <= nums[mid]:
                if nums[left] <= target < nums[mid]:
                    right = mid - 1
                else:
                    left = mid + 1
            else:
                if nums[mid] < target <= nums[right]:
                    left = mid + 1
                else:
                    right = mid - 1
        return False

    # Problem 82: Remove Duplicates from Sorted List II (array representation)
    def deleteDuplicates2(self, head: List[int]) -> List[int]:
        if not head:
            return []
        from collections import Counter
        count = Counter(head)
        return [x for x in head if count[x] == 1]

    # Problem 83: Remove Duplicates from Sorted List (array representation)
    def deleteDuplicates(self, head: List[int]) -> List[int]:
        if not head:
            return []
        result = [head[0]]
        for val in head[1:]:
            if val != result[-1]:
                result.append(val)
        return result

    # Problem 84: Largest Rectangle in Histogram
    def largestRectangleArea(self, heights: List[int]) -> int:
        stack = []
        max_area = 0
        heights.append(0)
        for i, h in enumerate(heights):
            while stack and heights[stack[-1]] > h:
                height = heights[stack.pop()]
                width = i if not stack else i - stack[-1] - 1
                max_area = max(max_area, height * width)
            stack.append(i)
        heights.pop()
        return max_area

    # Problem 85: Maximal Rectangle
    def maximalRectangle(self, matrix: List[List[str]]) -> int:
        if not matrix:
            return 0
        m, n = len(matrix), len(matrix[0])
        heights = [0] * n
        max_area = 0
        for i in range(m):
            for j in range(n):
                heights[j] = heights[j] + 1 if matrix[i][j] == '1' else 0
            max_area = max(max_area, self.largestRectangleArea(heights[:]))
        return max_area

    # Problem 86: Partition List (array representation)
    def partition(self, head: List[int], x: int) -> List[int]:
        less = []
        greater = []
        for val in head:
            if val < x:
                less.append(val)
            else:
                greater.append(val)
        return less + greater

    # Problem 87: Scramble String
    def isScramble(self, s1: str, s2: str) -> bool:
        if s1 == s2:
            return True
        if sorted(s1) != sorted(s2):
            return False
        n = len(s1)
        for i in range(1, n):
            if (self.isScramble(s1[:i], s2[:i]) and self.isScramble(s1[i:], s2[i:])) or \
               (self.isScramble(s1[:i], s2[n-i:]) and self.isScramble(s1[i:], s2[:n-i])):
                return True
        return False

    # Problem 88: Merge Sorted Array
    def mergeSortedArray(self, nums1: List[int], m: int, nums2: List[int], n: int) -> None:
        p1, p2, p = m - 1, n - 1, m + n - 1
        while p1 >= 0 and p2 >= 0:
            if nums1[p1] > nums2[p2]:
                nums1[p] = nums1[p1]
                p1 -= 1
            else:
                nums1[p] = nums2[p2]
                p2 -= 1
            p -= 1
        nums1[:p2 + 1] = nums2[:p2 + 1]

    # Problem 89: Gray Code
    def grayCode(self, n: int) -> List[int]:
        return [i ^ (i >> 1) for i in range(1 << n)]

    # Problem 90: Subsets II
    def subsetsWithDup(self, nums: List[int]) -> List[List[int]]:
        nums.sort()
        result = []
        def backtrack(start, path):
            result.append(path[:])
            for i in range(start, len(nums)):
                if i > start and nums[i] == nums[i - 1]:
                    continue
                path.append(nums[i])
                backtrack(i + 1, path)
                path.pop()
        backtrack(0, [])
        return result

    # Problem 91: Decode Ways
    def numDecodings(self, s: str) -> int:
        if not s or s[0] == '0':
            return 0
        n = len(s)
        dp = [0] * (n + 1)
        dp[0] = 1
        dp[1] = 1
        for i in range(2, n + 1):
            if s[i-1] != '0':
                dp[i] = dp[i-1]
            two_digit = int(s[i-2:i])
            if 10 <= two_digit <= 26:
                dp[i] += dp[i-2]
        return dp[n]

    # Problem 92: Reverse Linked List II (array representation)
    def reverseBetween(self, head: List[int], left: int, right: int) -> List[int]:
        result = head[:]
        result[left-1:right] = reversed(result[left-1:right])
        return result

    # Problem 93: Restore IP Addresses
    def restoreIpAddresses(self, s: str) -> List[str]:
        result = []
        def backtrack(start, path):
            if len(path) == 4:
                if start == len(s):
                    result.append('.'.join(path))
                return
            for length in range(1, 4):
                if start + length > len(s):
                    break
                part = s[start:start + length]
                if (len(part) > 1 and part[0] == '0') or int(part) > 255:
                    continue
                backtrack(start + length, path + [part])
        backtrack(0, [])
        return result

    # Problem 94: Binary Tree Inorder Traversal (array representation using level-order)
    def inorderTraversal(self, root: List) -> List[int]:
        if not root:
            return []

        # Build tree from array
        def build_tree(arr, idx):
            if idx >= len(arr) or arr[idx] is None:
                return None
            node = {'val': arr[idx], 'left': None, 'right': None}
            node['left'] = build_tree(arr, 2 * idx + 1)
            node['right'] = build_tree(arr, 2 * idx + 2)
            return node

        tree = build_tree(root, 0)
        result = []

        def inorder(node):
            if not node:
                return
            inorder(node['left'])
            result.append(node['val'])
            inorder(node['right'])

        inorder(tree)
        return result

    # Problem 96: Unique Binary Search Trees
    def numTrees(self, n: int) -> int:
        dp = [0] * (n + 1)
        dp[0] = dp[1] = 1
        for i in range(2, n + 1):
            for j in range(1, i + 1):
                dp[i] += dp[j - 1] * dp[i - j]
        return dp[n]

    # Problem 97: Interleaving String
    def isInterleave(self, s1: str, s2: str, s3: str) -> bool:
        if len(s1) + len(s2) != len(s3):
            return False
        dp = [[False] * (len(s2) + 1) for _ in range(len(s1) + 1)]
        dp[0][0] = True
        for i in range(1, len(s1) + 1):
            dp[i][0] = dp[i-1][0] and s1[i-1] == s3[i-1]
        for j in range(1, len(s2) + 1):
            dp[0][j] = dp[0][j-1] and s2[j-1] == s3[j-1]
        for i in range(1, len(s1) + 1):
            for j in range(1, len(s2) + 1):
                dp[i][j] = (dp[i-1][j] and s1[i-1] == s3[i+j-1]) or \
                           (dp[i][j-1] and s2[j-1] == s3[i+j-1])
        return dp[len(s1)][len(s2)]

    # Problem 100: Same Tree (array representation)
    def isSameTree(self, p: List, q: List) -> bool:
        return p == q


# ============================================================================
# TESTS
# ============================================================================

class TestProblem1:
    """Test Two Sum."""

    def test_two_sum(self):
        data = load_test_data(1)
        sol = Solution()
        for test in data['tests']:
            nums, target = test['input']
            result = sol.twoSum(nums[:], target)
            # Two Sum can return indices in any order
            expected = test['expected']
            assert sorted(result) == sorted(expected), f"Input: {test['input']}"


class TestProblem2:
    """Test Add Two Numbers."""

    def test_add_two_numbers(self):
        data = load_test_data(2)
        sol = Solution()
        for test in data['tests']:
            l1, l2 = test['input']
            result = sol.addTwoNumbers(l1, l2)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem3:
    """Test Longest Substring Without Repeating Characters."""

    def test_longest_substring(self):
        data = load_test_data(3)
        sol = Solution()
        for test in data['tests']:
            s = test['input'][0]
            result = sol.lengthOfLongestSubstring(s)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem4:
    """Test Median of Two Sorted Arrays."""

    def test_median(self):
        data = load_test_data(4)
        sol = Solution()
        for test in data['tests']:
            nums1, nums2 = test['input']
            result = sol.findMedianSortedArrays(nums1, nums2)
            assert abs(result - test['expected']) < 0.0001, f"Input: {test['input']}"


class TestProblem5:
    """Test Longest Palindromic Substring."""

    def test_longest_palindrome(self):
        data = load_test_data(5)
        sol = Solution()
        for test in data['tests']:
            s = test['input'][0]
            result = sol.longestPalindrome(s)
            # Multiple valid answers possible, just check it's a palindrome and correct length
            expected = test['expected']
            assert result == result[::-1], f"Result not palindrome: {result}"
            assert len(result) >= len(expected), f"Input: {test['input']}"


class TestProblem6:
    """Test Zigzag Conversion."""

    def test_zigzag(self):
        data = load_test_data(6)
        sol = Solution()
        for test in data['tests']:
            s, numRows = test['input']
            result = sol.convert(s, numRows)
            assert result == test['expected'], f"Input: {test['input']}, Got: {result}"


class TestProblem7:
    """Test Reverse Integer."""

    def test_reverse(self):
        data = load_test_data(7)
        sol = Solution()
        for test in data['tests']:
            x = test['input'][0]
            result = sol.reverse(x)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem8:
    """Test String to Integer (atoi)."""

    def test_atoi(self):
        data = load_test_data(8)
        sol = Solution()
        for test in data['tests']:
            s = test['input'][0]
            result = sol.myAtoi(s)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem9:
    """Test Palindrome Number."""

    def test_is_palindrome(self):
        data = load_test_data(9)
        sol = Solution()
        for test in data['tests']:
            x = test['input'][0]
            result = sol.isPalindrome(x)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem11:
    """Test Container With Most Water."""

    def test_max_area(self):
        data = load_test_data(11)
        sol = Solution()
        for test in data['tests']:
            height = test['input'][0]
            result = sol.maxArea(height)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem12:
    """Test Integer to Roman."""

    def test_int_to_roman(self):
        data = load_test_data(12)
        sol = Solution()
        for test in data['tests']:
            num = test['input'][0]
            result = sol.intToRoman(num)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem13:
    """Test Roman to Integer."""

    def test_roman_to_int(self):
        data = load_test_data(13)
        sol = Solution()
        for test in data['tests']:
            s = test['input'][0]
            result = sol.romanToInt(s)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem14:
    """Test Longest Common Prefix."""

    def test_longest_prefix(self):
        data = load_test_data(14)
        sol = Solution()
        for test in data['tests']:
            strs = test['input'][0]
            result = sol.longestCommonPrefix(strs)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem20:
    """Test Valid Parentheses."""

    def test_valid_parentheses(self):
        data = load_test_data(20)
        sol = Solution()
        for test in data['tests']:
            s = test['input'][0]
            result = sol.isValid(s)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem26:
    """Test Remove Duplicates from Sorted Array."""

    def test_remove_duplicates(self):
        data = load_test_data(26)
        sol = Solution()
        for test in data['tests']:
            nums = test['input'][0][:]
            result = sol.removeDuplicates(nums)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem27:
    """Test Remove Element."""

    def test_remove_element(self):
        data = load_test_data(27)
        sol = Solution()
        for test in data['tests']:
            nums, val = test['input'][0][:], test['input'][1]
            result = sol.removeElement(nums, val)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem28:
    """Test Find the Index of the First Occurrence in a String."""

    def test_str_str(self):
        data = load_test_data(28)
        sol = Solution()
        for test in data['tests']:
            haystack, needle = test['input']
            result = sol.strStr(haystack, needle)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem35:
    """Test Search Insert Position."""

    def test_search_insert(self):
        data = load_test_data(35)
        sol = Solution()
        for test in data['tests']:
            nums, target = test['input']
            result = sol.searchInsert(nums, target)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem53:
    """Test Maximum Subarray."""

    def test_max_subarray(self):
        data = load_test_data(53)
        sol = Solution()
        for test in data['tests']:
            nums = test['input'][0]
            result = sol.maxSubArray(nums)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem58:
    """Test Length of Last Word."""

    def test_length_last_word(self):
        data = load_test_data(58)
        sol = Solution()
        for test in data['tests']:
            s = test['input'][0]
            result = sol.lengthOfLastWord(s)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem66:
    """Test Plus One."""

    def test_plus_one(self):
        data = load_test_data(66)
        sol = Solution()
        for test in data['tests']:
            digits = test['input'][0][:]
            result = sol.plusOne(digits)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem67:
    """Test Add Binary."""

    def test_add_binary(self):
        data = load_test_data(67)
        sol = Solution()
        for test in data['tests']:
            a, b = test['input']
            result = sol.addBinary(a, b)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem69:
    """Test Sqrt(x)."""

    def test_sqrt(self):
        data = load_test_data(69)
        sol = Solution()
        for test in data['tests']:
            x = test['input'][0]
            result = sol.mySqrt(x)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem70:
    """Test Climbing Stairs."""

    def test_climbing_stairs(self):
        data = load_test_data(70)
        sol = Solution()
        for test in data['tests']:
            n = test['input'][0]
            result = sol.climbStairs(n)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem10:
    """Test Regular Expression Matching."""

    def test_regex_match(self):
        data = load_test_data(10)
        sol = Solution()
        for test in data['tests']:
            s, p = test['input']
            result = sol.isMatch(s, p)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem15:
    """Test 3Sum."""

    def test_three_sum(self):
        data = load_test_data(15)
        sol = Solution()
        for test in data['tests']:
            nums = test['input'][0][:]
            result = sol.threeSum(nums)
            expected = test['expected']
            # Sort for comparison
            result_sorted = sorted([sorted(x) for x in result])
            expected_sorted = sorted([sorted(x) for x in expected])
            assert result_sorted == expected_sorted, f"Input: {test['input']}"


class TestProblem16:
    """Test 3Sum Closest."""

    def test_three_sum_closest(self):
        data = load_test_data(16)
        sol = Solution()
        for test in data['tests']:
            nums, target = test['input'][0][:], test['input'][1]
            result = sol.threeSumClosest(nums, target)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem17:
    """Test Letter Combinations of a Phone Number."""

    def test_letter_combinations(self):
        data = load_test_data(17)
        sol = Solution()
        for test in data['tests']:
            digits = test['input'][0]
            result = sol.letterCombinations(digits)
            expected = test['expected']
            assert sorted(result) == sorted(expected), f"Input: {test['input']}"


class TestProblem18:
    """Test 4Sum."""

    def test_four_sum(self):
        data = load_test_data(18)
        sol = Solution()
        for test in data['tests']:
            nums, target = test['input'][0][:], test['input'][1]
            result = sol.fourSum(nums, target)
            expected = test['expected']
            result_sorted = sorted([sorted(x) for x in result])
            expected_sorted = sorted([sorted(x) for x in expected])
            assert result_sorted == expected_sorted, f"Input: {test['input']}"


class TestProblem19:
    """Test Remove Nth Node From End of List."""

    def test_remove_nth(self):
        data = load_test_data(19)
        sol = Solution()
        for test in data['tests']:
            head, n = test['input'][0][:], test['input'][1]
            result = sol.removeNthFromEnd(head, n)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem21:
    """Test Merge Two Sorted Lists."""

    def test_merge_two_lists(self):
        data = load_test_data(21)
        sol = Solution()
        for test in data['tests']:
            list1, list2 = test['input'][0][:], test['input'][1][:]
            result = sol.mergeTwoLists(list1, list2)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem22:
    """Test Generate Parentheses."""

    def test_generate_parentheses(self):
        data = load_test_data(22)
        sol = Solution()
        for test in data['tests']:
            n = test['input'][0]
            result = sol.generateParenthesis(n)
            expected = test['expected']
            assert sorted(result) == sorted(expected), f"Input: {test['input']}"


class TestProblem23:
    """Test Merge k Sorted Lists."""

    def test_merge_k_lists(self):
        data = load_test_data(23)
        sol = Solution()
        for test in data['tests']:
            lists = [lst[:] for lst in test['input'][0]]
            result = sol.mergeKLists(lists)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem24:
    """Test Swap Nodes in Pairs."""

    def test_swap_pairs(self):
        data = load_test_data(24)
        sol = Solution()
        for test in data['tests']:
            head = test['input'][0][:]
            result = sol.swapPairs(head)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem25:
    """Test Reverse Nodes in k-Group."""

    def test_reverse_k_group(self):
        data = load_test_data(25)
        sol = Solution()
        for test in data['tests']:
            head, k = test['input'][0][:], test['input'][1]
            result = sol.reverseKGroup(head, k)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem29:
    """Test Divide Two Integers."""

    def test_divide(self):
        data = load_test_data(29)
        sol = Solution()
        for test in data['tests']:
            dividend, divisor = test['input']
            result = sol.divide(dividend, divisor)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem30:
    """Test Substring with Concatenation of All Words."""

    def test_find_substring(self):
        data = load_test_data(30)
        sol = Solution()
        for test in data['tests']:
            s, words = test['input']
            result = sol.findSubstring(s, words)
            expected = test['expected']
            assert sorted(result) == sorted(expected), f"Input: {test['input']}"


class TestProblem31:
    """Test Next Permutation."""

    def test_next_permutation(self):
        data = load_test_data(31)
        sol = Solution()
        for test in data['tests']:
            nums = test['input'][0][:]
            sol.nextPermutation(nums)
            assert nums == test['expected'], f"Input: {test['input']}"


class TestProblem32:
    """Test Longest Valid Parentheses."""

    def test_longest_valid_parens(self):
        data = load_test_data(32)
        sol = Solution()
        for test in data['tests']:
            s = test['input'][0]
            result = sol.longestValidParentheses(s)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem33:
    """Test Search in Rotated Sorted Array."""

    def test_search(self):
        data = load_test_data(33)
        sol = Solution()
        for test in data['tests']:
            nums, target = test['input']
            result = sol.search(nums, target)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem34:
    """Test Find First and Last Position."""

    def test_search_range(self):
        data = load_test_data(34)
        sol = Solution()
        for test in data['tests']:
            nums, target = test['input']
            result = sol.searchRange(nums, target)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem36:
    """Test Valid Sudoku."""

    def test_valid_sudoku(self):
        data = load_test_data(36)
        sol = Solution()
        for test in data['tests']:
            board = [row[:] for row in test['input'][0]]
            result = sol.isValidSudoku(board)
            assert result == test['expected'], f"Input: problem 36"


class TestProblem38:
    """Test Count and Say."""

    def test_count_and_say(self):
        data = load_test_data(38)
        sol = Solution()
        for test in data['tests']:
            n = test['input'][0]
            result = sol.countAndSay(n)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem39:
    """Test Combination Sum."""

    def test_combination_sum(self):
        data = load_test_data(39)
        sol = Solution()
        for test in data['tests']:
            candidates, target = test['input'][0][:], test['input'][1]
            result = sol.combinationSum(candidates, target)
            expected = test['expected']
            result_sorted = sorted([sorted(x) for x in result])
            expected_sorted = sorted([sorted(x) for x in expected])
            assert result_sorted == expected_sorted, f"Input: {test['input']}"


class TestProblem40:
    """Test Combination Sum II."""

    def test_combination_sum2(self):
        data = load_test_data(40)
        sol = Solution()
        for test in data['tests']:
            candidates, target = test['input'][0][:], test['input'][1]
            result = sol.combinationSum2(candidates, target)
            expected = test['expected']
            result_sorted = sorted([sorted(x) for x in result])
            expected_sorted = sorted([sorted(x) for x in expected])
            assert result_sorted == expected_sorted, f"Input: {test['input']}"


class TestProblem41:
    """Test First Missing Positive."""

    def test_first_missing_positive(self):
        data = load_test_data(41)
        sol = Solution()
        for test in data['tests']:
            nums = test['input'][0][:]
            result = sol.firstMissingPositive(nums)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem42:
    """Test Trapping Rain Water."""

    def test_trap(self):
        data = load_test_data(42)
        sol = Solution()
        for test in data['tests']:
            height = test['input'][0][:]
            result = sol.trap(height)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem43:
    """Test Multiply Strings."""

    def test_multiply(self):
        data = load_test_data(43)
        sol = Solution()
        for test in data['tests']:
            num1, num2 = test['input']
            result = sol.multiply(num1, num2)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem44:
    """Test Wildcard Matching."""

    def test_wildcard_match(self):
        data = load_test_data(44)
        sol = Solution()
        for test in data['tests']:
            s, p = test['input']
            result = sol.isMatchWildcard(s, p)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem45:
    """Test Jump Game II."""

    def test_jump(self):
        data = load_test_data(45)
        sol = Solution()
        for test in data['tests']:
            nums = test['input'][0][:]
            result = sol.jump(nums)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem46:
    """Test Permutations."""

    def test_permute(self):
        data = load_test_data(46)
        sol = Solution()
        for test in data['tests']:
            nums = test['input'][0][:]
            result = sol.permute(nums)
            expected = test['expected']
            result_sorted = sorted([sorted(x) for x in result])
            expected_sorted = sorted([sorted(x) for x in expected])
            assert result_sorted == expected_sorted, f"Input: {test['input']}"


class TestProblem47:
    """Test Permutations II."""

    def test_permute_unique(self):
        data = load_test_data(47)
        sol = Solution()
        for test in data['tests']:
            nums = test['input'][0][:]
            result = sol.permuteUnique(nums)
            expected = test['expected']
            result_sorted = sorted([tuple(x) for x in result])
            expected_sorted = sorted([tuple(x) for x in expected])
            assert result_sorted == expected_sorted, f"Input: {test['input']}"


class TestProblem48:
    """Test Rotate Image."""

    def test_rotate(self):
        data = load_test_data(48)
        sol = Solution()
        for test in data['tests']:
            matrix = [row[:] for row in test['input'][0]]
            sol.rotate(matrix)
            assert matrix == test['expected'], f"Input: problem 48"


class TestProblem49:
    """Test Group Anagrams."""

    def test_group_anagrams(self):
        data = load_test_data(49)
        sol = Solution()
        for test in data['tests']:
            strs = test['input'][0][:]
            result = sol.groupAnagrams(strs)
            expected = test['expected']
            # Sort for comparison
            result_sorted = sorted([sorted(g) for g in result])
            expected_sorted = sorted([sorted(g) for g in expected])
            assert result_sorted == expected_sorted, f"Input: {test['input']}"


class TestProblem50:
    """Test Pow(x, n)."""

    def test_pow(self):
        data = load_test_data(50)
        sol = Solution()
        for test in data['tests']:
            x, n = test['input']
            result = sol.myPow(x, n)
            assert abs(result - test['expected']) < 0.00001, f"Input: {test['input']}"


class TestProblem51:
    """Test N-Queens."""

    def test_n_queens(self):
        data = load_test_data(51)
        sol = Solution()
        for test in data['tests']:
            n = test['input'][0]
            result = sol.solveNQueens(n)
            expected = test['expected']
            # Sort for comparison
            result_sorted = sorted([tuple(x) for x in result])
            expected_sorted = sorted([tuple(x) for x in expected])
            assert result_sorted == expected_sorted, f"Input: {test['input']}"


class TestProblem52:
    """Test N-Queens II."""

    def test_total_n_queens(self):
        data = load_test_data(52)
        sol = Solution()
        for test in data['tests']:
            n = test['input'][0]
            result = sol.totalNQueens(n)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem54:
    """Test Spiral Matrix."""

    def test_spiral_order(self):
        data = load_test_data(54)
        sol = Solution()
        for test in data['tests']:
            matrix = [row[:] for row in test['input'][0]]
            result = sol.spiralOrder(matrix)
            assert result == test['expected'], f"Input: problem 54"


class TestProblem55:
    """Test Jump Game."""

    def test_can_jump(self):
        data = load_test_data(55)
        sol = Solution()
        for test in data['tests']:
            nums = test['input'][0][:]
            result = sol.canJump(nums)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem56:
    """Test Merge Intervals."""

    def test_merge_intervals(self):
        data = load_test_data(56)
        sol = Solution()
        for test in data['tests']:
            intervals = [i[:] for i in test['input'][0]]
            result = sol.merge(intervals)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem57:
    """Test Insert Interval."""

    def test_insert_interval(self):
        data = load_test_data(57)
        sol = Solution()
        for test in data['tests']:
            intervals = [i[:] for i in test['input'][0]]
            new_interval = test['input'][1][:]
            result = sol.insert(intervals, new_interval)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem59:
    """Test Spiral Matrix II."""

    def test_generate_matrix(self):
        data = load_test_data(59)
        sol = Solution()
        for test in data['tests']:
            n = test['input'][0]
            result = sol.generateMatrix(n)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem60:
    """Test Permutation Sequence."""

    def test_get_permutation(self):
        data = load_test_data(60)
        sol = Solution()
        for test in data['tests']:
            n, k = test['input']
            result = sol.getPermutation(n, k)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem61:
    """Test Rotate List."""

    def test_rotate_right(self):
        data = load_test_data(61)
        sol = Solution()
        for test in data['tests']:
            head, k = test['input'][0][:], test['input'][1]
            result = sol.rotateRight(head, k)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem62:
    """Test Unique Paths."""

    def test_unique_paths(self):
        data = load_test_data(62)
        sol = Solution()
        for test in data['tests']:
            m, n = test['input']
            result = sol.uniquePaths(m, n)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem63:
    """Test Unique Paths II."""

    def test_unique_paths_obstacles(self):
        data = load_test_data(63)
        sol = Solution()
        for test in data['tests']:
            grid = [row[:] for row in test['input'][0]]
            result = sol.uniquePathsWithObstacles(grid)
            assert result == test['expected'], f"Input: problem 63"


class TestProblem64:
    """Test Minimum Path Sum."""

    def test_min_path_sum(self):
        data = load_test_data(64)
        sol = Solution()
        for test in data['tests']:
            grid = [row[:] for row in test['input'][0]]
            result = sol.minPathSum(grid)
            assert result == test['expected'], f"Input: problem 64"


class TestProblem71:
    """Test Simplify Path."""

    def test_simplify_path(self):
        data = load_test_data(71)
        sol = Solution()
        for test in data['tests']:
            path = test['input'][0]
            result = sol.simplifyPath(path)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem72:
    """Test Edit Distance."""

    def test_edit_distance(self):
        data = load_test_data(72)
        sol = Solution()
        for test in data['tests']:
            word1, word2 = test['input']
            result = sol.minDistance(word1, word2)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem73:
    """Test Set Matrix Zeroes."""

    def test_set_zeroes(self):
        data = load_test_data(73)
        sol = Solution()
        for test in data['tests']:
            matrix = [row[:] for row in test['input'][0]]
            sol.setZeroes(matrix)
            assert matrix == test['expected'], f"Input: problem 73"


class TestProblem74:
    """Test Search a 2D Matrix."""

    def test_search_matrix(self):
        data = load_test_data(74)
        sol = Solution()
        for test in data['tests']:
            matrix = [row[:] for row in test['input'][0]]
            target = test['input'][1]
            result = sol.searchMatrix(matrix, target)
            assert result == test['expected'], f"Input: problem 74"


class TestProblem75:
    """Test Sort Colors."""

    def test_sort_colors(self):
        data = load_test_data(75)
        sol = Solution()
        for test in data['tests']:
            nums = test['input'][0][:]
            sol.sortColors(nums)
            assert nums == test['expected'], f"Input: {test['input']}"


class TestProblem76:
    """Test Minimum Window Substring."""

    def test_min_window(self):
        data = load_test_data(76)
        sol = Solution()
        for test in data['tests']:
            s, t = test['input']
            result = sol.minWindow(s, t)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem77:
    """Test Combinations."""

    def test_combine(self):
        data = load_test_data(77)
        sol = Solution()
        for test in data['tests']:
            n, k = test['input']
            result = sol.combine(n, k)
            expected = test['expected']
            result_sorted = sorted([sorted(x) for x in result])
            expected_sorted = sorted([sorted(x) for x in expected])
            assert result_sorted == expected_sorted, f"Input: {test['input']}"


class TestProblem78:
    """Test Subsets."""

    def test_subsets(self):
        data = load_test_data(78)
        sol = Solution()
        for test in data['tests']:
            nums = test['input'][0][:]
            result = sol.subsets(nums)
            expected = test['expected']
            result_sorted = sorted([sorted(x) for x in result])
            expected_sorted = sorted([sorted(x) for x in expected])
            assert result_sorted == expected_sorted, f"Input: {test['input']}"


class TestProblem79:
    """Test Word Search."""

    def test_word_search(self):
        data = load_test_data(79)
        sol = Solution()
        for test in data['tests']:
            board = [row[:] for row in test['input'][0]]
            word = test['input'][1]
            result = sol.exist(board, word)
            assert result == test['expected'], f"Input: problem 79"


class TestProblem80:
    """Test Remove Duplicates from Sorted Array II."""

    def test_remove_duplicates2(self):
        data = load_test_data(80)
        sol = Solution()
        for test in data['tests']:
            nums = test['input'][0][:]
            result = sol.removeDuplicates2(nums)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem81:
    """Test Search in Rotated Sorted Array II."""

    def test_search_with_dups(self):
        data = load_test_data(81)
        sol = Solution()
        for test in data['tests']:
            nums, target = test['input']
            result = sol.searchWithDuplicates(nums, target)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem82:
    """Test Remove Duplicates from Sorted List II."""

    def test_delete_duplicates2(self):
        data = load_test_data(82)
        sol = Solution()
        for test in data['tests']:
            head = test['input'][0][:]
            result = sol.deleteDuplicates2(head)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem83:
    """Test Remove Duplicates from Sorted List."""

    def test_delete_duplicates(self):
        data = load_test_data(83)
        sol = Solution()
        for test in data['tests']:
            head = test['input'][0][:]
            result = sol.deleteDuplicates(head)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem84:
    """Test Largest Rectangle in Histogram."""

    def test_largest_rectangle(self):
        data = load_test_data(84)
        sol = Solution()
        for test in data['tests']:
            heights = test['input'][0][:]
            result = sol.largestRectangleArea(heights)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem85:
    """Test Maximal Rectangle."""

    def test_maximal_rectangle(self):
        data = load_test_data(85)
        sol = Solution()
        for test in data['tests']:
            matrix = [row[:] for row in test['input'][0]]
            result = sol.maximalRectangle(matrix)
            assert result == test['expected'], f"Input: problem 85"


class TestProblem86:
    """Test Partition List."""

    def test_partition(self):
        data = load_test_data(86)
        sol = Solution()
        for test in data['tests']:
            head, x = test['input'][0][:], test['input'][1]
            result = sol.partition(head, x)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem88:
    """Test Merge Sorted Array."""

    def test_merge_sorted(self):
        data = load_test_data(88)
        sol = Solution()
        for test in data['tests']:
            nums1, m, nums2, n = test['input']
            nums1 = nums1[:]
            nums2 = nums2[:]
            sol.mergeSortedArray(nums1, m, nums2, n)
            assert nums1 == test['expected'], f"Input: {test['input']}"


class TestProblem89:
    """Test Gray Code."""

    def test_gray_code(self):
        data = load_test_data(89)
        sol = Solution()
        for test in data['tests']:
            n = test['input'][0]
            result = sol.grayCode(n)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem90:
    """Test Subsets II."""

    def test_subsets_with_dup(self):
        data = load_test_data(90)
        sol = Solution()
        for test in data['tests']:
            nums = test['input'][0][:]
            result = sol.subsetsWithDup(nums)
            expected = test['expected']
            result_sorted = sorted([sorted(x) for x in result])
            expected_sorted = sorted([sorted(x) for x in expected])
            assert result_sorted == expected_sorted, f"Input: {test['input']}"


class TestProblem91:
    """Test Decode Ways."""

    def test_num_decodings(self):
        data = load_test_data(91)
        sol = Solution()
        for test in data['tests']:
            s = test['input'][0]
            result = sol.numDecodings(s)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem92:
    """Test Reverse Linked List II."""

    def test_reverse_between(self):
        data = load_test_data(92)
        sol = Solution()
        for test in data['tests']:
            head, left, right = test['input'][0][:], test['input'][1], test['input'][2]
            result = sol.reverseBetween(head, left, right)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem93:
    """Test Restore IP Addresses."""

    def test_restore_ip(self):
        data = load_test_data(93)
        sol = Solution()
        for test in data['tests']:
            s = test['input'][0]
            result = sol.restoreIpAddresses(s)
            expected = test['expected']
            assert sorted(result) == sorted(expected), f"Input: {test['input']}"


class TestProblem94:
    """Test Binary Tree Inorder Traversal."""

    def test_inorder(self):
        data = load_test_data(94)
        sol = Solution()
        for test in data['tests']:
            root = test['input'][0]
            result = sol.inorderTraversal(root)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem96:
    """Test Unique Binary Search Trees."""

    def test_num_trees(self):
        data = load_test_data(96)
        sol = Solution()
        for test in data['tests']:
            n = test['input'][0]
            result = sol.numTrees(n)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem97:
    """Test Interleaving String."""

    def test_is_interleave(self):
        data = load_test_data(97)
        sol = Solution()
        for test in data['tests']:
            s1, s2, s3 = test['input']
            result = sol.isInterleave(s1, s2, s3)
            assert result == test['expected'], f"Input: {test['input']}"


class TestProblem100:
    """Test Same Tree."""

    def test_same_tree(self):
        data = load_test_data(100)
        sol = Solution()
        for test in data['tests']:
            p, q = test['input']
            result = sol.isSameTree(p, q)
            assert result == test['expected'], f"Input: {test['input']}"
